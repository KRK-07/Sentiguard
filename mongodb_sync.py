"""
MongoDB Sync Manager for SentiGuard
Handles encrypted cloud synchronization of user data using MongoDB Atlas.
All data is encrypted client-side before upload - MongoDB never sees unencrypted data.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from encryption_manager import EncryptionManager
import json
import os
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

class MongoDBSyncManager:
    """Manages encrypted sync between local storage and MongoDB Atlas"""
    
    def __init__(self, user_google_id: str, user_email: str):
        """
        Initialize MongoDB sync manager
        
        Args:
            user_google_id: User's unique Google ID (for encryption key)
            user_email: User's email (for document identification)
        """
        self.user_id = user_google_id
        self.user_email = user_email
        self.encryption = EncryptionManager(user_google_id)
        self.client = None
        self.db = None
        self.collection = None
        self.initialized = False
        
        # Try to initialize MongoDB
        try:
            self._initialize_mongodb()
        except Exception as e:
            print(f"[WARNING] MongoDB initialization failed: {e}")
            print("[INFO] App will continue in offline mode")
    
    def _initialize_mongodb(self):
        """Initialize MongoDB Atlas connection"""
        try:
            # Get MongoDB URI from environment variable
            mongodb_uri = os.getenv('MONGODB_URI')
            
            if not mongodb_uri:
                raise ValueError("MONGODB_URI not found in environment variables")
            
            # Connect to MongoDB with SSL certificates
            # Python 3.13 SSL workaround
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=10000,
                tls=True,
                tlsAllowInvalidCertificates=False,
                tlsCAFile=certifi.where()
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client['sentiguard']
            self.collection = self.db['user_data']
            
            self.initialized = True
            print("[SUCCESS] MongoDB connection established")
            
        except Exception as e:
            print(f"[ERROR] MongoDB initialization failed: {e}")
            self.initialized = False
            raise
    
    def is_online(self) -> bool:
        """Check if Firebase is connected and operational"""
        return self.initialized and self.db is not None
    
    def sync_file(self, file_path: str, file_type: str) -> bool:
        """
        Encrypt and upload a file to MongoDB Atlas
        
        Args:
            file_path: Local file path to sync
            file_type: Type identifier (e.g., 'mood_history', 'keystrokes', 'alerts')
            
        Returns:
            True if sync successful, False otherwise
        """
        if not self.is_online():
            print("[WARNING] MongoDB offline - sync skipped")
            return False
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"[WARNING] File not found: {file_path}")
                return False
            
            # Read and encrypt file
            print(f"[SYNC] Encrypting {file_type}...")
            encrypted_data = self.encryption.encrypt_file(file_path)
            
            # Prepare document data
            doc_data = {
                "_id": f"{self.user_id}_{file_type}",  # Composite key
                "user_id": self.user_id,
                "encrypted_data": encrypted_data,
                "file_type": file_type,
                "last_synced": datetime.now().isoformat(),
                "user_email": self.user_email,
                "file_size": len(encrypted_data)
            }
            
            # Upload to MongoDB (upsert)
            self.collection.replace_one(
                {'_id': doc_data['_id']},
                doc_data,
                upsert=True
            )
            
            print(f"[SUCCESS] {file_type} synced to cloud ({len(encrypted_data)} bytes encrypted)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Sync failed for {file_type}: {e}")
            return False
    
    def download_file(self, file_type: str, output_path: str) -> bool:
        """
        Download and decrypt a file from MongoDB Atlas
        
        Args:
            file_type: Type identifier (e.g., 'mood_history', 'keystrokes', 'alerts')
            output_path: Local file path to save decrypted data
            
        Returns:
            True if download successful, False otherwise
        """
        if not self.is_online():
            print("[WARNING] MongoDB offline - download skipped")
            return False
        
        try:
            # Get document from MongoDB
            doc_id = f"{self.user_id}_{file_type}"
            doc = self.collection.find_one({'_id': doc_id})
            
            if not doc:
                print(f"[INFO] No cloud data found for {file_type}")
                return False
            
            # Get encrypted data
            encrypted_data = doc.get('encrypted_data')
            
            if not encrypted_data:
                print(f"[ERROR] No encrypted data in document for {file_type}")
                return False
            
            # Decrypt and save
            print(f"[SYNC] Decrypting {file_type}...")
            self.encryption.decrypt_to_file(encrypted_data, output_path)
            
            last_synced = doc.get('last_synced', 'unknown')
            print(f"[SUCCESS] {file_type} downloaded from cloud (last synced: {last_synced})")
            return True
            
        except Exception as e:
            print(f"[ERROR] Download failed for {file_type}: {e}")
            return False
    
    def sync_all_files(self, file_map: Dict[str, str]) -> Dict[str, bool]:
        """
        Sync multiple files to cloud
        
        Args:
            file_map: Dictionary mapping file types to local file paths
                     e.g., {'mood_history': 'mood_history.json', 'keystrokes': 'keystrokes.txt'}
        
        Returns:
            Dictionary mapping file types to sync status (True/False)
        """
        results = {}
        
        for file_type, file_path in file_map.items():
            success = self.sync_file(file_path, file_type)
            results[file_type] = success
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        print(f"[SYNC] Batch sync complete: {successful}/{total} files synced")
        
        return results
    
    def download_all_files(self, file_map: Dict[str, str]) -> Dict[str, bool]:
        """
        Download multiple files from cloud
        
        Args:
            file_map: Dictionary mapping file types to local file paths
                     e.g., {'mood_history': 'mood_history.json', 'keystrokes': 'keystrokes.txt'}
        
        Returns:
            Dictionary mapping file types to download status (True/False)
        """
        results = {}
        
        for file_type, file_path in file_map.items():
            success = self.download_file(file_type, file_path)
            results[file_type] = success
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        print(f"[SYNC] Batch download complete: {successful}/{total} files downloaded")
        
        return results
    
    def get_last_sync_time(self, file_type: str) -> Optional[str]:
        """
        Get the last sync timestamp for a file
        
        Args:
            file_type: Type identifier
            
        Returns:
            ISO format timestamp string or None
        """
        if not self.is_online():
            return None
        
        try:
            doc_id = f"{self.user_id}_{file_type}"
            doc = self.collection.find_one({'_id': doc_id})
            
            if doc:
                return doc.get('last_synced')
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to get sync time: {e}")
            return None
    
    def delete_cloud_data(self, file_type: Optional[str] = None) -> bool:
        """
        Delete data from cloud
        
        Args:
            file_type: Specific file type to delete, or None to delete all user data
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.is_online():
            print("[WARNING] MongoDB offline - deletion skipped")
            return False
        
        try:
            if file_type:
                # Delete specific file
                doc_id = f"{self.user_id}_{file_type}"
                self.collection.delete_one({'_id': doc_id})
                print(f"[SUCCESS] Deleted {file_type} from cloud")
            else:
                # Delete all user data
                self.collection.delete_many({'user_id': self.user_id})
                print("[SUCCESS] Deleted all user data from cloud")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Deletion failed: {e}")
            return False


def test_mongodb_sync():
    """Test MongoDB sync functionality"""
    print("=" * 50)
    print("Testing MongoDB Sync Manager")
    print("=" * 50)
    
    # Test user credentials
    test_user_id = "test_user_12345"
    test_email = "test@example.com"
    
    try:
        # Initialize sync manager
        print("\n[1/4] Initializing MongoDB Sync...")
        sync = MongoDBSyncManager(test_user_id, test_email)
        
        if not sync.is_online():
            print("[FAILED] MongoDB connection not established")
            return
        
        # Create test data
        print("\n[2/4] Creating test data...")
        test_data = {
            "test_entry": "This is encrypted test data",
            "timestamp": datetime.now().isoformat(),
            "mood_score": 0.75
        }
        
        with open("test_sync_data.json", "w") as f:
            json.dump(test_data, f, indent=2)
        
        # Upload test
        print("\n[3/4] Testing upload...")
        upload_success = sync.sync_file("test_sync_data.json", "test_data")
        
        if upload_success:
            print("[SUCCESS] Upload test passed")
        else:
            print("[FAILED] Upload test failed")
            return
        
        # Download test
        print("\n[4/4] Testing download...")
        download_success = sync.download_file("test_data", "test_sync_data_downloaded.json")
        
        if download_success:
            # Verify data
            with open("test_sync_data_downloaded.json", "r") as f:
                downloaded_data = json.load(f)
            
            if downloaded_data == test_data:
                print("[SUCCESS] Download and decryption test passed")
                print("\n" + "=" * 50)
                print("All MongoDB Sync tests PASSED!")
                print("=" * 50)
            else:
                print("[FAILED] Data mismatch after download")
        else:
            print("[FAILED] Download test failed")
        
        # Cleanup
        sync.delete_cloud_data("test_data")
        os.remove("test_sync_data.json")
        os.remove("test_sync_data_downloaded.json")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_mongodb_sync()

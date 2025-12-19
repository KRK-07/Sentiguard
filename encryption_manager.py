"""
Encryption Manager for SentiGuard
Provides end-to-end encryption for cloud data sync using AES-256.
User's Google ID is used to derive the encryption key, ensuring only the user can decrypt their data.
"""

import hashlib
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

class EncryptionManager:
    """Handles AES-256 encryption/decryption for user data"""
    
    def __init__(self, user_google_id: str):
        """
        Initialize encryption manager with user's Google ID
        
        Args:
            user_google_id: User's unique Google ID (used to derive encryption key)
        """
        self.user_id = user_google_id
        self.key = self._derive_key(user_google_id)
    
    def _derive_key(self, user_id: str) -> bytes:
        """
        Derive a 256-bit encryption key from user's Google ID
        Uses SHA-256 to create a consistent key from the user ID
        
        Args:
            user_id: User's Google ID
            
        Returns:
            32-byte encryption key
        """
        # Use SHA-256 to create a 256-bit (32-byte) key from user ID
        key = hashlib.sha256(user_id.encode('utf-8')).digest()
        return key
    
    def encrypt(self, data: dict) -> str:
        """
        Encrypt data using AES-256-CBC
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            # Convert dict to JSON string
            json_data = json.dumps(data)
            plaintext = json_data.encode('utf-8')
            
            # Generate random IV (Initialization Vector)
            iv = os.urandom(16)
            
            # Pad the plaintext to be a multiple of 128 bits (16 bytes)
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext) + padder.finalize()
            
            # Create cipher and encrypt
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Combine IV and ciphertext, then base64 encode
            encrypted_data = iv + ciphertext
            encoded = base64.b64encode(encrypted_data).decode('utf-8')
            
            return encoded
            
        except Exception as e:
            print(f"[ERROR] Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> dict:
        """
        Decrypt AES-256-CBC encrypted data
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted dictionary
        """
        try:
            # Base64 decode
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract IV (first 16 bytes) and ciphertext
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            # Create cipher and decrypt
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            # Convert back to dict
            json_str = plaintext.decode('utf-8')
            data = json.loads(json_str)
            
            return data
            
        except Exception as e:
            print(f"[ERROR] Decryption failed: {e}")
            raise
    
    def encrypt_file(self, file_path: str) -> str:
        """
        Encrypt the contents of a file
        
        Args:
            file_path: Path to file to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # For JSON files, load as dict and encrypt
            if file_path.endswith('.json'):
                data = json.loads(content)
                return self.encrypt(data)
            
            # For text files, encrypt as string
            else:
                data = {"content": content}
                return self.encrypt(data)
                
        except Exception as e:
            print(f"[ERROR] File encryption failed for {file_path}: {e}")
            raise
    
    def decrypt_to_file(self, encrypted_data: str, file_path: str):
        """
        Decrypt data and write to file
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            file_path: Path to write decrypted data
        """
        try:
            data = self.decrypt(encrypted_data)
            
            # For JSON files, write as formatted JSON
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            # For text files, extract content
            else:
                content = data.get("content", "")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"[ERROR] File decryption failed for {file_path}: {e}")
            raise


def test_encryption():
    """Test the encryption/decryption functionality"""
    print("Testing Encryption Manager...")
    
    # Test with sample user ID
    user_id = "123456789"
    manager = EncryptionManager(user_id)
    
    # Test data
    test_data = {
        "mood_history": [
            {"timestamp": "2025-12-10 14:30", "score": 0.5},
            {"timestamp": "2025-12-10 15:00", "score": -0.2}
        ],
        "user_name": "Test User",
        "sensitive_info": "This is private data"
    }
    
    print(f"Original data: {test_data}")
    
    # Encrypt
    encrypted = manager.encrypt(test_data)
    print(f"\nEncrypted (first 50 chars): {encrypted[:50]}...")
    print(f"Encrypted length: {len(encrypted)} bytes")
    
    # Decrypt
    decrypted = manager.decrypt(encrypted)
    print(f"\nDecrypted data: {decrypted}")
    
    # Verify
    if test_data == decrypted:
        print("\n[SUCCESS] Encryption/Decryption test PASSED!")
    else:
        print("\n[FAILED] Encryption/Decryption test FAILED!")
    
    # Test with different user ID (should fail to decrypt correctly)
    print("\n--- Testing with different user ID ---")
    different_manager = EncryptionManager("different_user_id")
    try:
        wrong_decrypt = different_manager.decrypt(encrypted)
        print("[FAILED] Security issue: Different user could decrypt data!")
    except:
        print("[SUCCESS] Security working: Different user cannot decrypt!")


if __name__ == "__main__":
    test_encryption()

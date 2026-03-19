"""
Quick MongoDB connection test
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import certifi

load_dotenv()

print("=" * 70)
print("MONGODB CONNECTION TEST")
print("=" * 70)

# Get MongoDB URI
mongodb_uri = os.getenv('MONGODB_URI')
print(f"\n1. MongoDB URI loaded: {mongodb_uri[:50]}..." if mongodb_uri else "❌ MONGODB_URI not found!")

if mongodb_uri:
    try:
        print("\n2. Attempting connection to MongoDB Atlas...")
        client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=10000,
            tls=True,
            tlsAllowInvalidCertificates=False,
            tlsCAFile=certifi.where()
        )
        
        print("3. Testing connection with ping...")
        result = client.admin.command('ping')
        print(f"   ✅ Ping successful: {result}")
        
        print("\n4. Accessing database and collection...")
        db = client['sentiguard']
        collection = db['user_data']
        
        print(f"   Database: {db.name}")
        print(f"   Collection: {collection.name}")
        
        print("\n5. Counting documents in collection...")
        count = collection.count_documents({})
        print(f"   Documents found: {count}")
        
        print("\n" + "=" * 70)
        print("✅ MongoDB CONNECTION SUCCESSFUL!")
        print("=" * 70)
        
    except ConnectionFailure as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        print("\nPossible causes:")
        print("- Network issues")
        print("- MongoDB Atlas cluster is paused")
        print("- IP whitelist restrictions")
        print("- Invalid credentials")
        
    except OperationFailure as e:
        print(f"\n❌ OPERATION FAILED: {e}")
        print("\nPossible causes:")
        print("- Insufficient permissions")
        print("- Database/collection doesn't exist")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
else:
    print("\n❌ Cannot test - MONGODB_URI is missing from .env file")

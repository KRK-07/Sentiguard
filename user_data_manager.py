"""
User Data Manager for SentiGuard
Handles user-specific data isolation by changing working directory
"""
import os
import json
import hashlib
import shutil

# Global variable to store current user info
_current_user_dir = None
_current_user_id = None
_original_dir = None

def initialize_user_data(user_info):
    """Initialize user-specific data directory and switch to it"""
    global _current_user_dir, _current_user_id, _original_dir
    
    # Save original directory
    if _original_dir is None:
        _original_dir = os.getcwd()
    
    # Get user ID from Google auth
    user_id = user_info.get('id', 'default_user')
    user_email = user_info.get('email', 'unknown@email.com')
    _current_user_id = user_id
    
    # Create a user-specific directory
    # Use first part of email for readability
    email_prefix = user_email.split('@')[0]
    user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
    user_dir = os.path.join(_original_dir, 'user_data', f'{email_prefix}_{user_hash}')
    
    # Create directory if it doesn't exist
    os.makedirs(user_dir, exist_ok=True)
    
    _current_user_dir = user_dir
    
    # Change working directory to user-specific folder
    os.chdir(user_dir)
    
    print(f"✅ User data directory: {user_dir}")
    print(f"✅ Working directory changed to user folder")
    
    # Initialize empty files if they don't exist
    init_files = [
        ('keystrokes.txt', ''),
        ('mood_history.json', '[]'),
        ('alert_status.json', '{"last_alert_line": 0}'),
        ('alerts_log.json', '[]')
    ]
    
    for filename, default_content in init_files:
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(default_content)
    
    return user_dir

def get_current_user_dir():
    """Get current user's data directory"""
    return _current_user_dir

def get_current_user_id():
    """Get current user's ID"""
    return _current_user_id

def cleanup_user_session():
    """Clean up user session and return to original directory"""
    global _current_user_dir, _current_user_id, _original_dir
    
    if _original_dir:
        os.chdir(_original_dir)
        print(f"✅ Returned to original directory")
    
    _current_user_dir = None
    _current_user_id = None

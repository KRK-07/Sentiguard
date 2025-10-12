#!/usr/bin/env python3
"""
SentiGuard Setup Script
Automatically sets up the required configuration files for first-time users
"""

import os
import shutil
import json

def setup_sentiguard():
    """Set up SentiGuard for first-time use"""
    print("🚀 Setting up SentiGuard...")
    
    # Files to copy from templates
    template_files = [
        ('.env.template', '.env'),
        ('client_secret.json.template', 'client_secret.json'),
        ('mood_history.json.template', 'mood_history.json'),
        ('user_settings.json.template', 'user_settings.json'),
        ('email_config.json.template', 'email_config.json'),
        ('alert_status.json.template', 'alert_status.json')
    ]
    
    for template_file, target_file in template_files:
        if os.path.exists(template_file):
            if not os.path.exists(target_file):
                shutil.copy2(template_file, target_file)
                print(f"✅ Created {target_file}")
            else:
                print(f"ℹ️  {target_file} already exists, skipping")
        else:
            print(f"⚠️  Template file {template_file} not found")
    
    # Check if virtual environment exists
    if not os.path.exists('.venv'):
        print("\n📦 Virtual environment not found. Creating one...")
        import subprocess
        try:
            subprocess.run(['python', '-m', 'venv', '.venv'], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    # Install dependencies
    print("\n📋 Installing dependencies...")
    try:
        import subprocess
        venv_python = '.venv/Scripts/python.exe' if os.name == 'nt' else '.venv/bin/python'
        subprocess.run([venv_python, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    print("\n🎯 Setup complete! Next steps:")
    print("1. Edit .env file and add your GEMINI_API_KEY")
    print("2. Edit client_secret.json with your Google OAuth credentials")
    print("3. (Optional) Edit email_config.json for email notifications")
    print("4. Run: python main.py")
    
    return True

if __name__ == "__main__":
    setup_sentiguard()
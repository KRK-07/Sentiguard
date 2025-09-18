#!/usr/bin/env python3
"""
Setup script for Sentiguard AI features
Run this to install AI companion dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🤖 Sentiguard AI Companion Setup")
    print("=" * 40)
    
    # Check if OpenAI is already installed
    try:
        import openai
        print("✅ OpenAI package already installed")
        openai_installed = True
    except ImportError:
        print("📦 Installing OpenAI package...")
        openai_installed = install_package("openai>=1.3.0")
        
        if openai_installed:
            print("✅ OpenAI package installed successfully")
        else:
            print("❌ Failed to install OpenAI package")
    
    print("\n🔑 API Key Setup")
    print("-" * 20)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OPENAI_API_KEY environment variable found")
        print(f"   Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    else:
        print("⚠️  No OPENAI_API_KEY environment variable found")
        print("\n💡 To enable AI chat features:")
        print("   1. Get an API key from: https://platform.openai.com/api-keys")
        print("   2. Set environment variable: OPENAI_API_KEY=your_key_here")
        print("   3. Or create ai_config.py with your key")
        
        # Ask if user wants to set it now
        try:
            user_key = input("\n🔑 Enter your OpenAI API key (or press Enter to skip): ").strip()
            if user_key:
                # Create ai_config.py
                config_content = f'''# Sentiguard AI Configuration
OPENAI_API_KEY = "{user_key}"
'''
                with open("ai_config.py", "w") as f:
                    f.write(config_content)
                print("✅ Created ai_config.py with your API key")
                
        except KeyboardInterrupt:
            print("\n⏭️  Skipped API key setup")
    
    print("\n🚀 Setup Complete!")
    print("=" * 40)
    
    if openai_installed:
        print("✅ AI Companion is ready to use")
        print("   • AI Chat will be available in the sidebar")
        print("   • Mood-aware conversations enabled")
        print("   • Fallback responses always available")
    else:
        print("⚠️  AI Companion partially available")
        print("   • Basic responses will work")
        print("   • Install OpenAI package for enhanced features")
    
    print("\n💡 Note: The app works perfectly without AI features!")
    print("   All existing features remain fully functional.")

if __name__ == "__main__":
    main()
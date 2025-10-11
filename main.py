import signal
import sys
import atexit
import os
from auth import login_with_google
from gui import launch_gui
from keylogger import start_keylogger
from analyzer import reset_alert_status, reset_analysis_cache

def cleanup():
    """Reset alert status and clear keystrokes for privacy while preserving analytics"""
    print("🔄 Starting cleanup process...")
    
    try:
        reset_alert_status()
        reset_analysis_cache()  # Reset cache for fresh start
        print("✅ Alert status and analysis cache reset")
    except Exception as e:
        print(f"Warning: Could not reset alert status: {e}")
    
    # Clear keystrokes.txt for user privacy (contains sensitive text)
    try:
        keystrokes_file = "keystrokes.txt"
        if os.path.exists(keystrokes_file):
            with open(keystrokes_file, "w") as f:
                f.write("")  # Clear the file
            print("🔒 Keystrokes cleared for privacy")
    except Exception as e:
        print(f"Warning: Could not clear keystrokes file: {e}")
    
    # Clear alert logs for privacy (may contain sensitive information)
    try:
        alerts_file = "alerts_log.json"
        if os.path.exists(alerts_file):
            import json
            with open(alerts_file, "w") as f:
                json.dump([], f)
            print("🔒 Alert logs cleared for privacy")
    except Exception as e:
        print(f"Warning: Could not clear alert logs: {e}")
    
    # Stop any background threads/processes
    try:
        # Force stop any remaining threads
        import threading
        for thread in threading.enumerate():
            if thread != threading.current_thread() and thread.daemon:
                print(f"🔄 Stopping daemon thread: {thread.name}")
    except Exception as e:
        print(f"Warning: Could not stop threads: {e}")
    
    # NOTE: mood_history.json is preserved for timeline analytics
    # It contains only anonymized timestamps and mood scores (no text content)
    print("📊 Mood history preserved for analytics")
    print("✅ Cleanup completed successfully")

def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals"""
    print(f"\nReceived signal {signum}. Cleaning up...")
    cleanup()
    sys.exit(0)

if __name__ == "__main__":
    # Register cleanup functions for various exit scenarios
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination request
    
    # Windows-specific signal handling
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, signal_handler)  # Ctrl+Break on Windows
        except AttributeError:
            pass  # Not available on all Windows versions
    
    try:
        user = login_with_google()
        listener = start_keylogger()
        launch_gui(user)
        listener.stop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        cleanup()
    except Exception as e:
        print(f"Application crashed with error: {e}")
        cleanup()
        raise
    finally:
        cleanup()

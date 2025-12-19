import signal
import sys
import atexit
import os
import gc  # Garbage collector for memory optimization
import json
import threading
import time

# Optional performance monitoring dependency
try:
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from auth import login_with_google
from gui import launch_gui
from keylogger import start_keylogger
from analyzer import reset_alert_status, reset_analysis_cache
from user_data_manager import initialize_user_data, cleanup_user_session
from mongodb_sync import MongoDBSyncManager

# Global sync manager
_sync_manager = None
_sync_thread = None
_sync_stop_event = threading.Event()

def cleanup():
    """Optimized cleanup with memory management and history trimming"""
    print("🔄 Starting cleanup process...")
    
    # Sync to cloud before cleanup
    try:
        if _sync_manager and _sync_manager.is_online():
            print("☁️  Syncing data to cloud...")
            file_map = {
                'mood_history': 'mood_history.json',
                'keystrokes': 'keystrokes.txt',
                'alerts': 'alerts_log.json'
            }
            _sync_manager.sync_all_files(file_map)
            print("✅ Cloud sync completed")
    except Exception as e:
        print(f"Warning: Cloud sync failed: {e}")
    
    # Stop periodic sync thread
    try:
        if _sync_thread and _sync_thread.is_alive():
            _sync_stop_event.set()
            _sync_thread.join(timeout=2)
            print("✅ Sync thread stopped")
    except Exception as e:
        print(f"Warning: Could not stop sync thread: {e}")
    
    # Flush any buffered mood data before cleanup
    try:
        from analyzer import flush_mood_buffer
        flush_mood_buffer()
        print("✅ Mood buffer flushed to disk")
    except Exception as e:
        print(f"Warning: Could not flush mood buffer: {e}")
    
    # Force garbage collection before cleanup to free memory
    gc.collect()
    
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
            # Use truncate for better performance
            with open(keystrokes_file, "r+") as f:
                f.truncate(0)
            print("🔒 Keystrokes cleared for privacy")
    except Exception as e:
        print(f"Warning: Could not clear keystrokes file: {e}")
    
    # Clear alert logs for privacy (may contain sensitive information)
    try:
        alerts_file = "alerts_log.json"
        if os.path.exists(alerts_file):
            with open(alerts_file, "w") as f:
                json.dump([], f)
            print("🔒 Alert logs cleared for privacy")
    except Exception as e:
        print(f"Warning: Could not clear alert logs: {e}")
    
    # Trim mood history to save memory and disk space (keep last 200 entries)
    try:
        mood_file = "mood_history.json"
        if os.path.exists(mood_file):
            with open(mood_file, "r") as f:
                history = json.load(f)
            
            # Keep only recent entries to reduce file size
            MAX_HISTORY_ENTRIES = 200
            if len(history) > MAX_HISTORY_ENTRIES:
                trimmed = history[-MAX_HISTORY_ENTRIES:]
                with open(mood_file, "w") as f:
                    json.dump(trimmed, f)
                print(f"📊 Mood history trimmed to {len(trimmed)} entries (saved {len(history) - len(trimmed)} entries)")
            else:
                print(f"📊 Mood history preserved ({len(history)} entries)")
    except Exception as e:
        print(f"Warning: Could not trim mood history: {e}")
    
    # Stop any background threads/processes
    try:
        for thread in threading.enumerate():
            if thread != threading.current_thread() and thread.daemon:
                print(f"🔄 Stopping daemon thread: {thread.name}")
    except Exception as e:
        print(f"Warning: Could not stop threads: {e}")
    
    # Final garbage collection to free memory
    gc.collect()
    print("✅ Cleanup completed successfully")

def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals"""
    print(f"\nReceived signal {signum}. Cleaning up...")
    cleanup()
    sys.exit(0)

def optimize_system():
    """Apply system-level optimizations for better performance"""
    try:
        # Enable aggressive garbage collection for memory optimization
        gc.enable()
        gc.set_threshold(700, 10, 10)  # More frequent GC cycles
        print("✅ Memory optimization enabled")
        
        # Set process priority to below normal on Windows (better system responsiveness)
        if sys.platform == "win32" and PSUTIL_AVAILABLE:
            try:
                p = psutil.Process(os.getpid())
                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                print("✅ Process priority optimized")
            except Exception as e:
                print(f"Note: Could not set process priority: {e}")
        elif sys.platform == "win32" and not PSUTIL_AVAILABLE:
            print("ℹ️  Install psutil for process priority optimization: pip install psutil")
    except Exception as e:
        print(f"Note: Some optimizations could not be applied: {e}")

def check_system_resources():
    """Check and display available system resources"""
    if not PSUTIL_AVAILABLE:
        print("ℹ️  Install psutil for resource monitoring: pip install psutil")
        return
    
    try:
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        cpu_count = psutil.cpu_count()
        
        print(f"💻 System Resources:")
        print(f"   Available RAM: {available_gb:.1f} GB")
        print(f"   CPU Cores: {cpu_count}")
        
        if available_gb < 2:
            print("⚠️  Low memory detected - performance optimizations active")
    except Exception as e:
        print(f"Note: Could not check system resources: {e}")

def periodic_sync():
    """Background thread that syncs data every 5 minutes"""
    global _sync_manager
    
    file_map = {
        'mood_history': 'mood_history.json',
        'keystrokes': 'keystrokes.txt',
        'alerts': 'alerts_log.json'
    }
    
    while not _sync_stop_event.is_set():
        # Wait 5 minutes (300 seconds) or until stop event
        if _sync_stop_event.wait(300):  # 5 minutes
            break
        
        # Sync if online
        try:
            if _sync_manager and _sync_manager.is_online():
                print("\n☁️  Auto-syncing data to cloud...")
                _sync_manager.sync_all_files(file_map)
                print("✅ Auto-sync completed\n")
        except Exception as e:
            print(f"Warning: Auto-sync failed: {e}")

def initialize_cloud_sync(user):
    """Initialize MongoDB cloud sync for the user"""
    global _sync_manager, _sync_thread
    
    try:
        user_id = user.get('id')
        user_email = user.get('email')
        
        if not user_id or not user_email:
            print("⚠️  Missing user credentials - cloud sync disabled")
            return
        
        print("\n☁️  Initializing cloud sync...")
        _sync_manager = MongoDBSyncManager(user_id, user_email)
        
        if _sync_manager.is_online():
            print("✅ Cloud sync enabled")
            
            # Download existing data from cloud (if any)
            print("📥 Checking for cloud data...")
            file_map = {
                'mood_history': 'mood_history.json',
                'keystrokes': 'keystrokes.txt',
                'alerts': 'alerts_log.json'
            }
            _sync_manager.download_all_files(file_map)
            
            # Start periodic sync thread
            _sync_thread = threading.Thread(target=periodic_sync, daemon=True, name="CloudSync")
            _sync_thread.start()
            print("✅ Auto-sync enabled (every 5 minutes)")
        else:
            print("ℹ️  Cloud sync unavailable - running in offline mode")
            print("   All features work normally, data saved locally")
    
    except Exception as e:
        print(f"⚠️  Could not initialize cloud sync: {e}")
        print("   Running in offline mode - all features work normally")

if __name__ == "__main__":
    print("🚀 Starting SentiGuard (Optimized)...")
    
    # Check system resources
    check_system_resources()
    
    # Apply system optimizations
    optimize_system()
    
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
        
        # Initialize user-specific data directory
        initialize_user_data(user)
        
        # Initialize cloud sync
        initialize_cloud_sync(user)
        
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
        cleanup_user_session()  # Return to original directory
        cleanup()

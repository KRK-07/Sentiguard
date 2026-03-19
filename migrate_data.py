"""
Migrate mood_history.json data to SQLite database
"""
import json
import sqlite3
from datetime import datetime

def migrate_json_to_db():
    """Migrate all mood history from JSON file to database with original timestamps"""
    
    try:
        # Read JSON file
        with open('mood_history.json', 'r') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} entries to migrate...")
        
        # Connect directly to database
        conn = sqlite3.connect('sentiguard.db')
        cursor = conn.cursor()
        
        # Migrate each entry
        migrated = 0
        skipped = 0
        
        for entry in data:
            try:
                timestamp = entry.get('timestamp')
                score = entry.get('score')
                
                if timestamp and score is not None:
                    # Determine mood category
                    if score > 0.3:
                        mood_category = 'positive'
                    elif score < -0.3:
                        mood_category = 'negative'
                    else:
                        mood_category = 'neutral'
                    
                    # Insert directly with original timestamp
                    cursor.execute("""
                        INSERT INTO mood_entries 
                        (timestamp, score, source, text_length, mood_category, has_crisis, is_anomaly, is_venting)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (timestamp, score, 'keylogger', 0, mood_category, False, False, False))
                    
                    migrated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"⚠️ Error migrating entry: {e}")
                skipped += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Migration complete!")
        print(f"   - Migrated: {migrated} entries")
        print(f"   - Skipped: {skipped} entries")
        print(f"\n🔄 Restart the app to see your data in the Analytics Dashboard")
        
    except FileNotFoundError:
        print("❌ mood_history.json not found")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_json_to_db()

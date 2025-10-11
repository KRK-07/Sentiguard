import os
import json
import re
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')

# Import our enhanced analyzer
from enhanced_analyzer import EnhancedSentimentAnalyzer, analyze_sentiment_enhanced

analyzer = SentimentIntensityAnalyzer()
enhanced_analyzer = EnhancedSentimentAnalyzer()

KEYSTROKE_FILE = "keystrokes.txt"
MOOD_HISTORY_FILE = "mood_history.json"  # New persistent mood history file

THRESHOLD = -0.5  
ALERT_LIMIT = 5   

ALERT_STATUS_FILE = "alert_status.json"

# Enhanced sentiment analysis function - now uses context-aware analysis
def analyze_sentiment(text):
    """Enhanced sentiment analysis that handles context, sarcasm, and concerning phrases"""
    
    if not text or not text.strip():
        return 0.0
    
    # Use the enhanced analyzer for better context understanding
    detailed_result = enhanced_analyzer.analyze_context(text)
    
    # Log concerning cases for monitoring
    if detailed_result['needs_attention']:
        log_concerning_analysis(text, detailed_result)
    
    # Return the context-adjusted score
    return detailed_result['adjusted_compound']

def log_concerning_analysis(text, analysis_result):
    """Log concerning text analysis for review"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'text_sample': text[:100] + '...' if len(text) > 100 else text,  # Truncate for privacy
            'original_score': analysis_result['original_vader']['compound'],
            'adjusted_score': analysis_result['adjusted_compound'],
            'is_sarcastic': analysis_result['is_sarcastic'],
            'mental_health_concern': analysis_result['mental_health_concern'],
            'explanation': analysis_result['explanation']
        }
        
        # Append to concerning analysis log
        log_file = "concerning_analysis.json"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        # Keep only last 50 entries for privacy
        logs = logs[-50:]
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    except Exception as e:
        print(f"Warning: Could not log concerning analysis: {e}")

def get_detailed_sentiment_analysis(text):
    """Get detailed sentiment analysis including sarcasm and mental health flags"""
    return enhanced_analyzer.analyze_context(text)

# Load and score last line
def get_latest_mood():
    if not os.path.exists(KEYSTROKE_FILE):
        return 0.0
    with open(KEYSTROKE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return 0.0
        last_line = lines[-1].strip()
        score = analyze_sentiment(last_line)  # Use enhanced analysis
        return score

# Cache for day analysis to improve performance
_analysis_cache = []
_last_file_size = 0

# Analyze all keystrokes as history
def get_day_analysis():
    global _analysis_cache, _last_file_size
    
    if not os.path.exists(KEYSTROKE_FILE):
        return []
    
    # Check if file has grown since last read
    current_size = os.path.getsize(KEYSTROKE_FILE)
    
    # If file size hasn't changed, return cached result
    if current_size == _last_file_size and _analysis_cache:
        return _analysis_cache
    
    # Only process new lines if file has grown
    result = []
    try:
        with open(KEYSTROKE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # If we have cached data and file grew, only process new lines
        if _analysis_cache and current_size > _last_file_size:
            # Start from where we left off
            new_lines = lines[len(_analysis_cache):]
            result = _analysis_cache.copy()
            
            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                score = analyze_sentiment(line)
                timestamp = datetime.now().isoformat()
                result.append((timestamp, score))
                save_mood_to_history(score)  # Save to persistent history
        else:
            # Process all lines (first time or file was truncated)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                score = analyze_sentiment(line)
                timestamp = datetime.now().isoformat()
                result.append((timestamp, score))
                save_mood_to_history(score)  # Save to persistent history
        
        # Update cache
        _analysis_cache = result
        _last_file_size = current_size
        
    except Exception as e:
        print(f"Error reading keystroke file: {e}")
        return _analysis_cache if _analysis_cache else []
    
    return result


def get_alert_status():
    if os.path.exists(ALERT_STATUS_FILE):
        with open(ALERT_STATUS_FILE, "r") as f:
            return json.load(f)
    return {"last_alert_line": 0}

def set_alert_status(line_num):
    status = {"last_alert_line": line_num}
    with open(ALERT_STATUS_FILE, "w") as f:
        json.dump(status, f)

def count_below_threshold(return_lines=False):
    if not os.path.exists(KEYSTROKE_FILE):
        return (0, 0, []) if return_lines else (0, 0)
    count = 0
    lines = []
    neg_lines = []
    with open(KEYSTROKE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    status = get_alert_status()
    start = status.get("last_alert_line", 0)
    for i, line in enumerate(lines[start:], start):
        line = line.strip()
        if not line:
            continue
        score = analyze_sentiment(line)  # Use enhanced analysis
        if score < THRESHOLD:
            count += 1
            neg_lines.append(line)
    if return_lines:
        return count, len(lines), neg_lines
    else:
        return count, len(lines)

def reset_alert_status():
    """Reset alert status - called when app exits"""
    if os.path.exists(ALERT_STATUS_FILE):
        status = {"last_alert_line": 0}
        with open(ALERT_STATUS_FILE, "w") as f:
            json.dump(status, f)

def reset_analysis_cache():
    """Reset the analysis cache - useful for testing or when file is cleared"""
    global _analysis_cache, _last_file_size
    _analysis_cache = []
    _last_file_size = 0

# Mood history management functions for persistent analytics
def save_mood_to_history(score):
    """Save mood score to persistent history file (privacy-safe)"""
    try:
        timestamp = datetime.now().isoformat()
        mood_entry = {
            "timestamp": timestamp,
            "score": score
        }
        
        # Load existing history
        history = []
        if os.path.exists(MOOD_HISTORY_FILE):
            with open(MOOD_HISTORY_FILE, "r") as f:
                history = json.load(f)
        
        # Add new entry
        history.append(mood_entry)
        
        # Keep only last 10000 entries to prevent file from growing too large
        if len(history) > 10000:
            history = history[-10000:]
        
        # Save updated history
        with open(MOOD_HISTORY_FILE, "w") as f:
            json.dump(history, f)
            
    except Exception as e:
        print(f"Warning: Could not save mood to history: {e}")

def get_mood_history():
    """Get mood history from persistent file"""
    try:
        if os.path.exists(MOOD_HISTORY_FILE):
            with open(MOOD_HISTORY_FILE, "r") as f:
                history = json.load(f)
                # Convert to format expected by existing code
                return [(entry["timestamp"], entry["score"]) for entry in history]
        return []
    except Exception as e:
        print(f"Warning: Could not load mood history: {e}")
        return []

def clear_mood_history():
    """Clear mood history file (for complete privacy reset)"""
    try:
        if os.path.exists(MOOD_HISTORY_FILE):
            with open(MOOD_HISTORY_FILE, "w") as f:
                json.dump([], f)
            print("🔒 Mood history cleared")
        return True
    except Exception as e:
        print(f"Warning: Could not clear mood history: {e}")
        return False

def get_mood_statistics(period='daily'):
    """Calculate mood statistics for different time periods"""
    from datetime import datetime, timedelta
    import statistics
    
    # Use persistent mood history instead of keystrokes for privacy
    history = get_mood_history()
    if not history:
        # Fallback to current session data if no persistent history exists
        history = get_day_analysis()
    
    if not history:
        return []
    
    # Convert timestamps and group by period
    now = datetime.now()
    stats_data = []
    
    if period == 'daily':
        # Last 30 days
        for i in range(30):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_scores = []
            for timestamp_str, score in history:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if day_start <= timestamp < day_end:
                        day_scores.append(score)
                except:
                    continue
            
            avg_score = statistics.mean(day_scores) if day_scores else 0.0
            stats_data.append({
                'label': day_start.strftime('%m/%d'),
                'value': avg_score,
                'count': len(day_scores)
            })
        
        return list(reversed(stats_data))  # Show oldest to newest
    
    elif period == 'weekly':
        # Last 12 weeks
        for i in range(12):
            week_start = (now - timedelta(weeks=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            week_start -= timedelta(days=week_start.weekday())  # Start of week (Monday)
            week_end = week_start + timedelta(days=7)
            
            week_scores = []
            for timestamp_str, score in history:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if week_start <= timestamp < week_end:
                        week_scores.append(score)
                except:
                    continue
            
            avg_score = statistics.mean(week_scores) if week_scores else 0.0
            stats_data.append({
                'label': f"Week {week_start.strftime('%m/%d')}",
                'value': avg_score,
                'count': len(week_scores)
            })
        
        return list(reversed(stats_data))
    
    elif period == 'monthly':
        # Last 12 months
        for i in range(12):
            month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
            
            month_scores = []
            for timestamp_str, score in history:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if month_start <= timestamp < next_month:
                        month_scores.append(score)
                except:
                    continue
            
            avg_score = statistics.mean(month_scores) if month_scores else 0.0
            stats_data.append({
                'label': month_start.strftime('%b %Y'),
                'value': avg_score,
                'count': len(month_scores)
            })
        
        return list(reversed(stats_data))
    
    return []

def get_mood_summary():
    """Get overall mood summary statistics"""
    history = get_day_analysis()
    if not history:
        return {
            'total_entries': 0,
            'avg_score': 0.0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0
        }
    
    scores = [score for _, score in history]
    positive_count = sum(1 for score in scores if score > 0.1)
    negative_count = sum(1 for score in scores if score < -0.1)
    neutral_count = len(scores) - positive_count - negative_count
    
    return {
        'total_entries': len(scores),
        'avg_score': sum(scores) / len(scores) if scores else 0.0,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count
    }

def clear_all_logs():
    """Clear all logs and reset alert status - useful for testing or privacy"""
    import os
    
    # Clear keystrokes
    try:
        if os.path.exists(KEYSTROKE_FILE):
            with open(KEYSTROKE_FILE, "w") as f:
                f.write("")
            print("🔒 Keystrokes cleared")
    except Exception as e:
        print(f"Error clearing keystrokes: {e}")
    
    # Clear alert logs
    try:
        alerts_file = "alerts_log.json"
        if os.path.exists(alerts_file):
            with open(alerts_file, "w") as f:
                json.dump([], f)
            print("🔒 Alert logs cleared")
    except Exception as e:
        print(f"Error clearing alert logs: {e}")
    
    # Reset alert status
    reset_alert_status()
    print("🔒 Alert status reset")
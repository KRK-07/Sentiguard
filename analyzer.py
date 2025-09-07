import os
import json
import re
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')

analyzer = SentimentIntensityAnalyzer()
KEYSTROKE_FILE = "keystrokes.txt"
MOOD_HISTORY_FILE = "mood_history.json"  # New persistent mood history file

THRESHOLD = -0.5  
ALERT_LIMIT = 5   

ALERT_STATUS_FILE = "alert_status.json"

# Enhanced sentiment analysis function
def analyze_sentiment(text):
    """Enhanced sentiment analysis that combines VADER with custom rules for modern expressions"""
    
    # Get base VADER score
    vader_score = analyzer.polarity_scores(text)['compound']
    
    # Apply custom enhancements
    enhanced_score = apply_custom_sentiment_rules(text, vader_score)
    
    # Ensure score stays within -1 to 1 range
    enhanced_score = max(-1.0, min(1.0, enhanced_score))
    
    return enhanced_score

def apply_custom_sentiment_rules(text, base_score):
    """Apply custom rules to enhance sentiment detection for modern expressions"""
    
    text_lower = text.lower()
    enhancement = 0.0
    
    # 1. Detect excitement through repeated letters (yayyyy, wooooo, etc.)
    repeated_patterns = re.findall(r'([a-z])\1{2,}', text_lower)
    if repeated_patterns:
        # Common positive repeated letters
        positive_repeats = ['y', 'a', 'o', 'e', 'w', 'h']
        positive_count = sum(1 for char, in repeated_patterns if char in positive_repeats)
        if positive_count > 0:
            enhancement += 0.3 * positive_count  # Boost for positive repeated letters
    
    # 2. Detect ALL CAPS excitement (but not short words like "I" or "OK")
    caps_words = re.findall(r'\b[A-Z]{3,}\b', text)
    if caps_words:
        # Common excited caps expressions
        excited_caps = ['YESSS', 'WOOO', 'LETS', 'GO', 'AWESOME', 'AMAZING', 'GREAT', 'LOVE', 'WIN', 'YES']
        excited_count = sum(1 for word in caps_words if any(excited in word for excited in excited_caps))
        if excited_count > 0:
            enhancement += 0.25 * excited_count
        elif len(caps_words) > 2:  # Multiple caps words generally indicate excitement
            enhancement += 0.2
    
    # 3. Modern slang and informal positive expressions
    positive_slang = {
        'yay': 0.4, 'yayyy': 0.5, 'yayyyy': 0.6,
        'wooo': 0.4, 'woooo': 0.5, 'wooooo': 0.6,
        'lessgo': 0.5, 'letsgo': 0.5, 'lessgoo': 0.5,
        'poggers': 0.4, 'pog': 0.3, 'lit': 0.3,
        'fire': 0.3, 'sick': 0.2, 'dope': 0.3,
        'hype': 0.4, 'hyped': 0.4, 'pumped': 0.4,
        'stoked': 0.4, 'psyched': 0.4, 'amped': 0.4,
        'vibes': 0.2, 'vibing': 0.3, 'mood': 0.1,
        'slay': 0.3, 'slaying': 0.3, 'killing': 0.2,
        'bet': 0.2, 'facts': 0.2, 'no cap': 0.3,
        'fr': 0.1, 'periodt': 0.2, 'period': 0.1
    }
    
    for slang, boost in positive_slang.items():
        if slang in text_lower:
            enhancement += boost
    
    # 4. Exclamation marks (multiple = more excitement)
    exclamation_count = text.count('!')
    if exclamation_count > 0:
        enhancement += min(0.3, exclamation_count * 0.1)  # Cap at 0.3
    
    # 5. Question marks with excitement (like "Really?!")
    if '?' in text and '!' in text:
        enhancement += 0.2
    
    # 6. Emoticons and emoji patterns
    emoticon_patterns = [':)', ':D', '=D', ':P', ';)', ':-)', '=)', 'xD', 'XD']
    for emoticon in emoticon_patterns:
        if emoticon in text:
            enhancement += 0.2
            break  # Don't double count
    
    # 7. Positive action words in caps or with enthusiasm
    action_words = ['winning', 'crushing', 'nailing', 'acing', 'dominating', 'succeeding']
    for word in action_words:
        if word in text_lower:
            enhancement += 0.2
    
    # 8. Gaming/internet culture expressions
    gaming_positive = ['gg', 'ez', 'wp', 'nice', 'clutch', 'carry', 'pro', 'skilled']
    for term in gaming_positive:
        if term in text_lower:
            enhancement += 0.15
    
    # 9. Detect overwhelmingly positive sentiment that VADER might miss
    overwhelming_positive = ['absolutely love', 'so happy', 'best day', 'amazing day', 'incredible', 'fantastic']
    for phrase in overwhelming_positive:
        if phrase in text_lower:
            enhancement += 0.3
    
    # 10. Negative enhancement for clearly negative slang VADER might miss
    negative_slang = {
        'bruh': -0.1, 'ugh': -0.2, 'meh': -0.2, 'bleh': -0.2,
        'cringe': -0.3, 'cringing': -0.3, 'yikes': -0.2,
        'oof': -0.2, 'rip': -0.1, 'dead': -0.2,
        'kill me': -0.5, 'end me': -0.4, 'done': -0.1
    }
    
    for slang, penalty in negative_slang.items():
        if slang in text_lower:
            enhancement += penalty  # penalty is negative
    
    # Apply enhancement to base score
    final_score = base_score + enhancement
    
    # Special case: if base score was neutral/slightly positive but we detected strong positive indicators
    if base_score >= -0.1 and enhancement > 0.4:
        final_score = max(final_score, 0.4)  # Ensure strong positive indicators result in positive score
    
    return final_score

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
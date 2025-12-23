import os
import json
import re
from datetime import datetime, timedelta
from collections import deque
import statistics
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Phase 2: spaCy for linguistic analysis
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_ENABLED = True
except (ImportError, OSError):
    print("⚠️ spaCy not available - some linguistic features disabled")
    SPACY_ENABLED = False
    nlp = None

# Phase 3: Sentence Transformers for semantic understanding
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    print("Loading Sentence Transformer model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    EMBEDDINGS_ENABLED = True
    print("✅ Sentence Transformer loaded")
except Exception as e:
    print(f"⚠️ Sentence Transformers disabled: {e}")
    EMBEDDINGS_ENABLED = False
    embedding_model = None
    st_util = None

# Cardiff NLP RoBERTa Model
print("Loading Cardiff NLP sentiment model...")
try:
    tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment-latest")
    model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment-latest")
    device = 0 if torch.cuda.is_available() else -1
    cardiff_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=device)
    print("✅ Cardiff NLP model loaded")
    CARDIFF_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Cardiff NLP failed, using fallback: {e}")
    CARDIFF_AVAILABLE = False
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk
    nltk.download('vader_lexicon', quiet=True)
    vader_analyzer = SentimentIntensityAnalyzer()

# Import enhanced analyzer for backward compatibility
from enhanced_analyzer import EnhancedSentimentAnalyzer
enhanced_analyzer = EnhancedSentimentAnalyzer()

# ============================================================================
# GLOBAL STATE & CONFIGURATION
# ============================================================================

# Phase 1: Statistical Analysis State
_sentiment_history = deque(maxlen=10)  # Rolling window for z-score
PROFANITY_WORDS = {
    'fuck', 'shit', 'damn', 'hell', 'ass', 'bitch', 'crap', 'piss',
    'bastard', 'dick', 'cock', 'pussy', 'slut', 'whore', 'retard'
}
CIRCADIAN_FILE = os.path.join(os.path.dirname(__file__), 'circadian_baseline.json')

# Phase 2: Linguistic Intelligence Vocabularies
SARCASM_MARKERS = {
    'oh great', 'yeah right', 'sure thing', 'totally', 'obviously', 
    'clearly', 'brilliant', 'fantastic', 'wonderful', 'perfect',
    'just perfect', 'love it', 'thanks a lot', 'just what i needed'
}
CRISIS_KEYWORDS = {
    'suicide', 'kill myself', 'end it all', 'no point', 'better off dead',
    'self harm', 'cut myself', 'want to die', 'give up', 'hopeless',
    'worthless', 'hate myself', 'disappear forever'
}
VENTING_INDICATORS = {
    'ugh', 'argh', 'gah', 'wtf', 'fml', 'smh', 'jfc', 'omfg',
    'i swear', 'i cant', 'why does', 'every time', 'always happens'
}

# Phase 3: Semantic Understanding Vocabularies
GAMING_VOCABULARY = [
    'gg', 'glhf', 'ggwp', 'ez', 'rekt', 'pwned', 'noob', 'clutch',
    'ace', 'headshot', 'respawn', 'loot', 'nerf', 'buff', 'op',
    'camping', 'griefing', 'ganking', 'farming', 'speedrun',
    'ragequit', 'tilted', 'carried', 'feeding', 'stomped'
]
MODERN_IDIOMS = {
    'no cap': 0.3, 'fr fr': 0.2, 'lowkey': 0.0, 'highkey': 0.1,
    'slaps': 0.8, 'hits different': 0.6, 'bussin': 0.9, 'mid': -0.3,
    'its giving': 0.0, 'ate': 0.7, 'slay': 0.8, 'vibe check': 0.0,
    'main character energy': 0.6, 'rent free': -0.2, 'understood the assignment': 0.8,
    'touch grass': -0.4, 'chronically online': -0.3, 'unhinged': -0.2
}

# Phase 3: Semantic State
_gaming_embeddings = {}
_idiom_embeddings = {}
_message_context_window = deque(maxlen=5)

KEYSTROKE_FILE = "keystrokes.txt"
MOOD_HISTORY_FILE = "mood_history.json"  # New persistent mood history file

THRESHOLD = -0.3  # Matches the red dotted line on the graph
ALERT_LIMIT = 5   

ALERT_STATUS_FILE = "alert_status.json"

# Performance optimization: Sentiment result cache
_sentiment_cache = {}
_cache_max_size = 100  # Limit cache to 100 entries to save memory

# ============================================================================
# PHASE 1: STATISTICAL ANALYSIS
# ============================================================================

def detect_profanity_shift(text):
    """Compare sentiment with/without profanity to detect if profanity is genuine distress"""
    text_lower = text.lower()
    has_profanity = any(word in text_lower for word in PROFANITY_WORDS)
    
    if not has_profanity:
        return 0.0  # No profanity, no adjustment
    
    # Remove profanity and compare sentiment
    clean_text = text
    for word in PROFANITY_WORDS:
        clean_text = re.sub(r'\b' + word + r'\b', '', clean_text, flags=re.IGNORECASE)
    
    if not clean_text.strip():
        return 0.0
    
    # Get base scores
    if CARDIFF_AVAILABLE:
        original_score = _cardiff_to_score(cardiff_pipeline(text[:512]))
        clean_score = _cardiff_to_score(cardiff_pipeline(clean_text[:512]))
    else:
        original_score = vader_analyzer.polarity_scores(text)['compound']
        clean_score = vader_analyzer.polarity_scores(clean_text)['compound']
    
    # If profanity removal improves sentiment significantly, it's genuine distress
    delta = clean_score - original_score
    if delta > 0.15:  # Profanity was masking negative sentiment
        return -0.15
    elif delta < -0.1:  # Profanity was expressing frustration, not genuine negativity
        return 0.1
    return 0.0

def detect_statistical_anomaly(score):
    """Z-score anomaly detection on rolling window"""
    _sentiment_history.append(score)
    
    if len(_sentiment_history) < 3:
        return False, 0.0  # Need minimum data
    
    mean = statistics.mean(_sentiment_history)
    stdev = statistics.stdev(_sentiment_history)
    
    if stdev < 0.01:  # Avoid division by near-zero
        return False, 0.0
    
    z_score = (score - mean) / stdev
    
    # Flag if score is > 2 standard deviations below mean
    if z_score < -2.0:
        return True, abs(z_score) * 0.05  # Downward adjustment
    
    return False, 0.0

def load_circadian_profile():
    """Load hourly baseline sentiment from file"""
    if os.path.exists(CIRCADIAN_FILE):
        try:
            with open(CIRCADIAN_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    # Default baseline: neutral across all hours
    return {str(h): 0.0 for h in range(24)}

def update_circadian_profile(hour, score):
    """Update hourly baseline with exponential moving average"""
    profile = load_circadian_profile()
    hour_key = str(hour)
    
    if hour_key in profile:
        # Exponential moving average: new = 0.1 * current + 0.9 * old
        profile[hour_key] = 0.1 * score + 0.9 * profile[hour_key]
    else:
        profile[hour_key] = score
    
    try:
        with open(CIRCADIAN_FILE, 'w') as f:
            json.dump(profile, f)
    except:
        pass

def normalize_by_time(score):
    """Adjust score based on circadian rhythm baseline"""
    current_hour = datetime.now().hour
    profile = load_circadian_profile()
    baseline = profile.get(str(current_hour), 0.0)
    
    # Calculate deviation from baseline
    deviation = score - baseline
    normalized = score - (deviation * 0.2)  # Dampen by 20%
    
    # Update baseline in background
    update_circadian_profile(current_hour, score)
    
    return normalized, baseline

# ============================================================================
# PHASE 2: LINGUISTIC INTELLIGENCE
# ============================================================================

def detect_sarcasm_markers(text):
    """Detect sarcasm through linguistic patterns"""
    text_lower = text.lower()
    adjustment = 0.0
    
    # Check for sarcasm markers
    for marker in SARCASM_MARKERS:
        if marker in text_lower:
            adjustment -= 0.15  # Invert sentiment
    
    if not SPACY_ENABLED:
        return adjustment
    
    # spaCy analysis: Excessive positive adjectives with negative context
    doc = nlp(text)
    positive_adj_count = sum(1 for token in doc if token.pos_ == 'ADJ' and token.sentiment > 0)
    
    if positive_adj_count >= 3:
        # Check for negative verbs nearby
        has_negative_verb = any(token.pos_ == 'VERB' and token.sentiment < 0 for token in doc)
        if has_negative_verb:
            adjustment -= 0.2  # Likely sarcastic
    
    return adjustment

def check_crisis_keywords(text):
    """Flag high-risk crisis keywords"""
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in CRISIS_KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    if found_keywords:
        return True, found_keywords
    return False, []

def detect_venting_pattern(text):
    """Distinguish venting frustration from sustained distress"""
    text_lower = text.lower()
    
    # Check for venting indicators
    venting_count = sum(1 for indicator in VENTING_INDICATORS if indicator in text_lower)
    
    if venting_count == 0:
        return False, 0.0
    
    if not SPACY_ENABLED:
        # Simple heuristic: High profanity + venting indicators = temporary frustration
        profanity_count = sum(1 for word in PROFANITY_WORDS if word in text_lower)
        if profanity_count >= 2 and venting_count >= 1:
            return True, 0.1  # Upward adjustment for venting
        return False, 0.0
    
    # spaCy analysis: Short bursts vs sustained negativity
    doc = nlp(text)
    sentences = list(doc.sents)
    
    if len(sentences) <= 2:  # Short message = likely venting
        if venting_count >= 1:
            return True, 0.15
    
    return False, 0.0

# ============================================================================
# PHASE 3: SEMANTIC UNDERSTANDING
# ============================================================================

def initialize_phase3_embeddings():
    """Pre-compute embeddings for gaming vocabulary and idioms"""
    global _gaming_embeddings, _idiom_embeddings
    
    if not EMBEDDINGS_ENABLED:
        return
    
    try:
        # Gaming vocabulary embeddings
        for phrase in GAMING_VOCABULARY:
            _gaming_embeddings[phrase] = embedding_model.encode(phrase, convert_to_tensor=False)
        
        # Modern idiom embeddings
        for idiom in MODERN_IDIOMS.keys():
            _idiom_embeddings[idiom] = embedding_model.encode(idiom, convert_to_tensor=False)
        
        print(f"✅ Initialized embeddings: {len(_gaming_embeddings)} gaming + {len(_idiom_embeddings)} idioms")
    except Exception as e:
        print(f"⚠️ Embedding initialization failed: {e}")

def detect_gaming_context(text):
    """Detect gaming-related messages and adjust sentiment"""
    if not EMBEDDINGS_ENABLED or not _gaming_embeddings:
        # Fallback: Simple keyword matching
        text_lower = text.lower()
        matches = sum(1 for term in GAMING_VOCABULARY if term in text_lower)
        if matches >= 2:
            return 0.2  # Gaming is usually positive context
        return 0.0
    
    try:
        # Semantic similarity with gaming vocabulary
        text_embedding = embedding_model.encode(text, convert_to_tensor=False)
        
        max_similarity = 0.0
        for phrase, phrase_emb in _gaming_embeddings.items():
            similarity = st_util.cos_sim(text_embedding, phrase_emb).item()
            max_similarity = max(max_similarity, similarity)
        
        # Threshold for gaming context
        if max_similarity > 0.65:
            return 0.2  # Positive adjustment for gaming
        elif max_similarity > 0.5:
            return 0.1  # Slight positive adjustment
        
        return 0.0
    except Exception as e:
        return 0.0

def detect_modern_idioms(text):
    """Detect and interpret modern slang/idioms"""
    text_lower = text.lower()
    
    if not EMBEDDINGS_ENABLED or not _idiom_embeddings:
        # Fallback: Direct keyword matching
        for idiom, sentiment_adj in MODERN_IDIOMS.items():
            if idiom in text_lower:
                return idiom, sentiment_adj
        return None, 0.0
    
    try:
        # Semantic similarity with idiom embeddings
        text_embedding = embedding_model.encode(text, convert_to_tensor=False)
        
        best_match = None
        best_similarity = 0.0
        
        for idiom, phrase_emb in _idiom_embeddings.items():
            similarity = st_util.cos_sim(text_embedding, phrase_emb).item()
            if similarity > best_similarity and similarity > 0.7:
                best_similarity = similarity
                best_match = idiom
        
        if best_match:
            return best_match, MODERN_IDIOMS[best_match]
        
        return None, 0.0
    except Exception as e:
        return None, 0.0

def analyze_with_context_window(text):
    """Analyze sentiment with conversation context"""
    _message_context_window.append(text)
    
    if len(_message_context_window) < 2:
        return 0.0  # Need context for comparison
    
    if not EMBEDDINGS_ENABLED:
        return 0.0
    
    try:
        # Compare current message with previous messages
        current_embedding = embedding_model.encode(text, convert_to_tensor=False)
        
        # Average similarity with previous messages
        similarities = []
        for prev_text in list(_message_context_window)[:-1]:  # Exclude current
            prev_embedding = embedding_model.encode(prev_text, convert_to_tensor=False)
            sim = st_util.cos_sim(current_embedding, prev_embedding).item()
            similarities.append(sim)
        
        avg_similarity = statistics.mean(similarities)
        
        # High similarity = repetitive/ruminating thoughts (concerning)
        if avg_similarity > 0.85:
            return -0.1  # Downward adjustment for rumination
        
        return 0.0
    except Exception as e:
        return 0.0

# Initialize Phase 3 embeddings on module load
initialize_phase3_embeddings()

def _cardiff_to_score(result):
    """Convert Cardiff NLP output to -1 to +1 score"""
    label = result[0]['label']
    confidence = result[0]['score']
    
    if label == 'positive':
        return confidence
    elif label == 'negative':
        return -confidence
    else:  # neutral
        return 0.0

# Enhanced sentiment analysis function - now uses Cardiff NLP + All 3 Phases
def analyze_sentiment(text):
    """
    Multi-phase sentiment analysis:
    - Cardiff NLP RoBERTa (70% weight)
    - Enhanced analyzer (30% weight)
    - Phase 1: Statistical Analysis
    - Phase 2: Linguistic Intelligence
    - Phase 3: Semantic Understanding
    """
    
    if not text or not text.strip():
        return 0.0
    
    # Check cache first to avoid redundant analysis
    cache_key = text.strip().lower()[:100]  # Use first 100 chars as key
    if cache_key in _sentiment_cache:
        return _sentiment_cache[cache_key]
    
    try:
        # ===== BASE SENTIMENT (Cardiff 70% + Enhanced 30%) =====
        if CARDIFF_AVAILABLE:
            cardiff_result = cardiff_pipeline(text[:512])  # Limit to 512 tokens
            base_score = _cardiff_to_score(cardiff_result)
        else:
            vader_scores = vader_analyzer.polarity_scores(text)
            base_score = vader_scores['compound']
        
        # Enhanced analyzer for context
        detailed_result = enhanced_analyzer.analyze_context(text)
        
        # Weighted blend: Cardiff 70% + Enhanced 30%
        blended_score = (base_score * 0.7) + (detailed_result['adjusted_compound'] * 0.3)
        
        # ===== PHASE 1: STATISTICAL ANALYSIS =====
        profanity_adj = detect_profanity_shift(text)
        is_anomaly, anomaly_adj = detect_statistical_anomaly(blended_score)
        circadian_score, baseline = normalize_by_time(blended_score)
        
        # Apply Phase 1 adjustments
        phase1_score = circadian_score + profanity_adj
        if is_anomaly:
            phase1_score -= anomaly_adj
        
        # ===== PHASE 2: LINGUISTIC INTELLIGENCE =====
        sarcasm_adj = detect_sarcasm_markers(text)
        is_crisis, crisis_words = check_crisis_keywords(text)
        is_venting, venting_adj = detect_venting_pattern(text)
        
        # Apply Phase 2 adjustments
        phase2_score = phase1_score + sarcasm_adj
        if is_venting:
            phase2_score += venting_adj
        if is_crisis:
            phase2_score = min(phase2_score, -0.7)  # Cap at high negativity
            # Crisis flagging handled separately in detailed_result
        
        # ===== PHASE 3: SEMANTIC UNDERSTANDING =====
        gaming_adj = detect_gaming_context(text)
        idiom_match, idiom_adj = detect_modern_idioms(text)
        context_adj = analyze_with_context_window(text)
        
        # Apply Phase 3 adjustments
        final_score = phase2_score + gaming_adj + idiom_adj + context_adj
        
        # ===== BOUNDARY CLAMPING =====
        final_score = max(-1.0, min(1.0, final_score))
        
        # Log concerning cases for monitoring
        if detailed_result['needs_attention'] or is_crisis:
            log_concerning_analysis(text, detailed_result)
        
        # Cache the result (with size limit)
        if len(_sentiment_cache) < _cache_max_size:
            _sentiment_cache[cache_key] = final_score
        elif len(_sentiment_cache) >= _cache_max_size:
            # Clear oldest 20% of cache when full
            items = list(_sentiment_cache.items())
            _sentiment_cache.clear()
            _sentiment_cache.update(dict(items[-80:]))  # Keep newest 80%
            _sentiment_cache[cache_key] = final_score
    except Exception as e:
        print(f"⚠️ Sentiment analysis error: {e}")
        final_score = 0.0
    
    return final_score

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
    """Reset the analysis cache and sentiment cache - useful for testing or when file is cleared"""
    global _analysis_cache, _last_file_size, _sentiment_cache
    _analysis_cache = []
    _last_file_size = 0
    _sentiment_cache.clear()  # Clear sentiment cache for memory optimization

# Mood history management functions for persistent analytics
# Performance: Use buffering to reduce disk writes
_mood_buffer = []
_mood_buffer_size = 10  # Write to disk every 10 entries

def save_mood_to_history(score):
    """Save mood score to persistent history file with buffering for performance"""
    global _mood_buffer
    
    try:
        timestamp = datetime.now().isoformat()
        mood_entry = {
            "timestamp": timestamp,
            "score": score
        }
        
        # Add to buffer
        _mood_buffer.append(mood_entry)
        
        # Only write to disk when buffer is full (reduces I/O)
        if len(_mood_buffer) >= _mood_buffer_size:
            flush_mood_buffer()
            
    except Exception as e:
        print(f"Warning: Could not save mood to history: {e}")

def flush_mood_buffer():
    """Flush mood buffer to disk"""
    global _mood_buffer
    
    if not _mood_buffer:
        return
    
    try:
        # Load existing history
        history = []
        if os.path.exists(MOOD_HISTORY_FILE):
            with open(MOOD_HISTORY_FILE, "r") as f:
                history = json.load(f)
        
        # Add buffered entries
        history.extend(_mood_buffer)
        
        # Keep only last 500 entries to save memory (reduced from 10000)
        if len(history) > 500:
            history = history[-500:]
        
        # Save updated history
        with open(MOOD_HISTORY_FILE, "w") as f:
            json.dump(history, f)
        
        # Clear buffer
        _mood_buffer = []
            
    except Exception as e:
        print(f"Warning: Could not flush mood buffer: {e}")

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
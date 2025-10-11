"""
Enhanced Sentiment Analyzer for SentiGuard
Handles context, sarcasm, irony, and concerning phrases that basic NLTK VADER misses.
"""

import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Tuple
import logging

# Ensure VADER lexicon is available
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

class EnhancedSentimentAnalyzer:
    """Enhanced sentiment analyzer that handles context, sarcasm, and complex sentences"""
    
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        
        # Context patterns that can flip sentiment (sarcasm/irony detection)
        self.sarcasm_patterns = [
            r"so\s+(\w+)\s+.*?(kill|die|murder|destroy|hate)",
            r"really\s+(\w+)\s+.*?(awful|terrible|horrible)",
            r"just\s+(perfect|great|wonderful)\s+.*?(not|never|fail|wrong|disaster)",
            r"(happy|excited|thrilled)\s+.*?(kill|murder|destroy)",
            r"(love|adore)\s+.*?(when\s+things\s+go\s+wrong|when\s+people\s+ignore)",
            r"(amazing|wonderful|perfect)\s+.*?(day|time)\s+.*?(disaster|failure|wrong|disappointment)",
            r"(so|really|very)\s+(excited|happy|thrilled)\s+.*?(could\s+(die|kill))",
            r"(great|perfect|wonderful),?\s+another\s+.*?(day|time)\s+.*?(disappointment|failure|disaster)",
            r"(love|adore)\s+it\s+when\s+.*?(ignore|hurt|disappoint)",
        ]
        
        # Intensity modifiers that change context
        self.intensity_modifiers = {
            'very': 1.5, 'really': 1.4, 'extremely': 1.8, 'super': 1.3,
            'quite': 1.2, 'rather': 1.1, 'somewhat': 0.8, 'slightly': 0.6,
            'barely': 0.4, 'hardly': 0.3, 'not': -1.0, 'never': -1.0
        }
        
        # Negative context phrases that flip meaning
        self.negative_contexts = [
            r"(kill|murder|destroy|eliminate)\s+(someone|somebody|people)",
            r"(die|death|dead)\s+(inside|emotionally)",
            r"could\s+(murder|kill)\s+(for|someone)",
            r"(hate|despise)\s+(everything|everyone|life)",
            r"want\s+to\s+(die|disappear|give\s+up)",
            r"wish\s+.*?(dead|gone|never\s+born)",
            r"(end|finish)\s+it\s+all",
            r"nothing\s+matters\s+anymore",
        ]
        
        # Positive expressions that might be sarcastic
        self.potential_sarcasm = [
            r"(so|really|very)\s+(happy|excited|thrilled|perfect|great|wonderful|amazing)",
            r"(absolutely|totally|completely)\s+(love|adore|perfect)",
            r"just\s+(perfect|great|wonderful|amazing)",
        ]
        
        # Mental health concern indicators
        self.mental_health_flags = [
            r"(want|wish)\s+to\s+(die|kill\s+myself|end\s+it)",
            r"(suicide|suicidal|self\s+harm|cutting)",
            r"(no\s+point|meaningless|worthless|useless)",
            r"(everyone\s+hates\s+me|nobody\s+cares|alone\s+forever)",
            r"(can't\s+take\s+it|give\s+up|end\s+everything)",
        ]
    
    def detect_sarcasm(self, text: str) -> Tuple[bool, float]:
        """Detect potential sarcasm and return confidence score"""
        text_lower = text.lower()
        sarcasm_score = 0.0
        
        # Check for sarcasm patterns
        for pattern in self.sarcasm_patterns:
            if re.search(pattern, text_lower):
                sarcasm_score += 0.7
                break  # One strong indicator is enough
        
        # Check for conflicting sentiments in same sentence
        positive_words = ['happy', 'great', 'wonderful', 'perfect', 'amazing', 'love', 'excited', 'thrilled', 'fantastic']
        negative_words = ['kill', 'murder', 'destroy', 'hate', 'die', 'awful', 'terrible', 'horrible', 'disaster']
        
        has_positive = any(word in text_lower for word in positive_words)
        has_negative = any(word in text_lower for word in negative_words)
        
        if has_positive and has_negative:
            sarcasm_score += 0.5
        
        # Check for negative context phrases
        for pattern in self.negative_contexts:
            if re.search(pattern, text_lower):
                sarcasm_score += 0.6
                break
        
        # Check for potential sarcasm indicators
        for pattern in self.potential_sarcasm:
            if re.search(pattern, text_lower):
                # Only add if there are also negative elements
                if has_negative or any(neg in text_lower for neg in ['when', 'while', 'but']):
                    sarcasm_score += 0.4
        
        return sarcasm_score > 0.5, min(sarcasm_score, 1.0)
    
    def detect_mental_health_concerns(self, text: str) -> Tuple[bool, float]:
        """Detect serious mental health concerns that need immediate attention"""
        text_lower = text.lower()
        concern_score = 0.0
        
        for pattern in self.mental_health_flags:
            if re.search(pattern, text_lower):
                concern_score += 0.8
        
        # Additional concerning patterns
        concerning_combinations = [
            r"(happy|excited).*?(kill|murder|hurt)",
            r"(love|adore).*?(pain|suffering|death)",
            r"(perfect|wonderful).*?(end|finish|over)",
        ]
        
        for pattern in concerning_combinations:
            if re.search(pattern, text_lower):
                concern_score += 0.6
        
        return concern_score > 0.5, min(concern_score, 1.0)
    
    def analyze_context(self, text: str) -> Dict:
        """Analyze sentence context and structure"""
        if not text or not text.strip():
            return {
                'original_vader': {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0},
                'adjusted_compound': 0.0,
                'is_sarcastic': False,
                'sarcasm_confidence': 0.0,
                'mental_health_concern': False,
                'concern_confidence': 0.0,
                'sentiment_category': 'neutral',
                'confidence': 0.0,
                'needs_attention': False
            }
        
        # Basic VADER analysis
        vader_scores = self.sia.polarity_scores(text)
        
        # Check for sarcasm
        is_sarcastic, sarcasm_confidence = self.detect_sarcasm(text)
        
        # Check for mental health concerns
        has_mental_concern, concern_confidence = self.detect_mental_health_concerns(text)
        
        # Apply context corrections
        adjusted_score = vader_scores['compound']
        
        # Handle sarcasm
        if is_sarcastic:
            # Flip or dampen the sentiment for sarcastic content
            if adjusted_score > 0.1:  # Positive sentiment that might be sarcastic
                adjusted_score = -abs(adjusted_score) * 0.7  # Make it negative but less extreme
            elif adjusted_score < -0.1:  # Already negative, might be exaggerated
                adjusted_score = adjusted_score * 0.5  # Reduce intensity
        
        # Handle mental health concerns - these override other sentiment
        if has_mental_concern:
            adjusted_score = min(adjusted_score, -0.7)  # Force strongly negative
        
        # Handle specific concerning phrases regardless of positive words
        concerning_phrases = [
            r"(kill|murder)\s+(someone|somebody|people)",
            r"want\s+to\s+(die|kill\s+myself)",
            r"(hate|despise)\s+(life|everything|everyone)",
            r"(wish|want)\s+.*?(dead|gone|disappear)",
            r"(end|finish)\s+it\s+all",
            r"no\s+point\s+(in\s+)?(living|trying|anything)",
        ]
        
        for pattern in concerning_phrases:
            if re.search(pattern, text.lower()):
                adjusted_score = min(adjusted_score, -0.6)  # Force negative
                break
        
        # Determine if attention is needed
        needs_attention = (
            adjusted_score < -0.4 or 
            is_sarcastic or 
            has_mental_concern or
            concern_confidence > 0.3
        )
        
        return {
            'original_vader': vader_scores,
            'adjusted_compound': adjusted_score,
            'is_sarcastic': is_sarcastic,
            'sarcasm_confidence': sarcasm_confidence,
            'mental_health_concern': has_mental_concern,
            'concern_confidence': concern_confidence,
            'sentiment_category': self._categorize_sentiment(adjusted_score),
            'confidence': abs(adjusted_score),
            'needs_attention': needs_attention,
            'explanation': self._generate_explanation(vader_scores['compound'], adjusted_score, is_sarcastic, has_mental_concern)
        }
    
    def _categorize_sentiment(self, score: float) -> str:
        """Categorize sentiment based on adjusted score"""
        if score >= 0.5:
            return "very_positive"
        elif score >= 0.1:
            return "positive"
        elif score >= -0.1:
            return "neutral"
        elif score >= -0.5:
            return "negative"
        else:
            return "very_negative"
    
    def _generate_explanation(self, original: float, adjusted: float, sarcastic: bool, concerning: bool) -> str:
        """Generate explanation for the adjustment"""
        if concerning:
            return "Mental health concern detected - flagged for attention"
        elif sarcastic:
            return f"Sarcasm detected - sentiment adjusted from {original:.2f} to {adjusted:.2f}"
        elif abs(original - adjusted) > 0.2:
            return f"Context adjustment applied - modified from {original:.2f} to {adjusted:.2f}"
        else:
            return "Standard sentiment analysis applied"

# Simple interface functions for backward compatibility
def analyze_sentiment_enhanced(text: str) -> float:
    """Enhanced sentiment analysis that handles context and sarcasm"""
    if not text or not text.strip():
        return 0.0
    
    analyzer = EnhancedSentimentAnalyzer()
    result = analyzer.analyze_context(text)
    
    # Return the adjusted score instead of raw VADER
    return result['adjusted_compound']

def get_detailed_analysis(text: str) -> Dict:
    """Get detailed analysis including sarcasm detection and mental health flags"""
    analyzer = EnhancedSentimentAnalyzer()
    return analyzer.analyze_context(text)

# Test function
def test_enhanced_analyzer():
    """Test the enhanced analyzer with problematic sentences"""
    analyzer = EnhancedSentimentAnalyzer()
    
    test_sentences = [
        "I am so happy right now I can kill someone",  # Your example
        "This is just perfect when everything goes wrong",
        "I really love it when people ignore me",
        "I'm so excited I could die",
        "Great, another wonderful day of disappointment",
        "I am genuinely happy today",
        "I feel terrible and want to give up",
        "Life is amazing and I love everything",
        "I want to kill myself",  # Serious concern
        "Nothing matters anymore, I should just end it",  # Mental health flag
        "I love this beautiful sunny day",  # Genuine positive
        "I hate when things go wrong but today is good",  # Mixed but not sarcastic
    ]
    
    print("🧪 Testing Enhanced Sentiment Analyzer:")
    print("=" * 80)
    
    for sentence in test_sentences:
        result = analyzer.analyze_context(sentence)
        print(f"\n📝 Text: '{sentence}'")
        print(f"   Original VADER: {result['original_vader']['compound']:.3f}")
        print(f"   Enhanced Score: {result['adjusted_compound']:.3f}")
        print(f"   Category: {result['sentiment_category']}")
        print(f"   Sarcastic: {result['is_sarcastic']} (confidence: {result['sarcasm_confidence']:.2f})")
        print(f"   Mental Health Concern: {result['mental_health_concern']} (confidence: {result['concern_confidence']:.2f})")
        print(f"   Needs Attention: {result['needs_attention']}")
        print(f"   Explanation: {result['explanation']}")

if __name__ == "__main__":
    test_enhanced_analyzer()
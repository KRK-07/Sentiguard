#!/usr/bin/env python3
"""
Test script for the enhanced sentiment analyzer integration
"""

from analyzer import analyze_sentiment, get_detailed_sentiment_analysis

def test_enhanced_integration():
    """Test the enhanced sentiment analysis integration"""
    
    test_sentences = [
        "I am so happy right now I can kill someone",  # Your problematic example
        "This is just perfect when everything goes wrong",  # Sarcasm
        "Great, another wonderful day of disappointment",  # Sarcasm  
        "I really love it when people ignore me",  # Sarcasm
        "I am genuinely happy today",  # Genuine positive
        "I feel terrible and want to give up",  # Concerning
        "Life is amazing and I love everything",  # Genuine positive
        "I want to die",  # Serious concern
    ]
    
    print("🧪 Testing Enhanced Sentiment Analysis Integration:")
    print("=" * 70)
    
    for sentence in test_sentences:
        # Get basic score  
        score = analyze_sentiment(sentence)
        
        # Get detailed analysis
        details = get_detailed_sentiment_analysis(sentence)
        
        print(f"\n📝 Text: '{sentence}'")
        print(f"   Enhanced Score: {score:.3f} ({details['sentiment_category']})")
        print(f"   Original VADER: {details['original_vader']['compound']:.3f}")
        print(f"   🎭 Sarcastic: {details['is_sarcastic']}")
        print(f"   ⚠️  Mental Health Concern: {details['mental_health_concern']}")
        print(f"   🚨 Needs Attention: {details['needs_attention']}")
        print(f"   📝 Explanation: {details['explanation']}")

if __name__ == "__main__":
    test_enhanced_integration()
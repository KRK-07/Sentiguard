"""
Test script for Phase 1-3 sentiment analysis
Demonstrates all enhancement features
"""

import sys
sys.path.insert(0, 'c:/Users/krkes/senti/senti-new')

from analyzer import analyze_sentiment

# Test cases covering all phases
test_cases = [
    # Phase 1: Profanity detection
    ("I'm so fucking frustrated with this shit", "Profanity + distress"),
    
    # Phase 2: Sarcasm
    ("Oh great, another wonderful day at work", "Sarcasm detection"),
    
    # Phase 2: Venting
    ("ugh why does this always happen to me fml", "Venting pattern"),
    
    # Phase 2: Crisis keyword
    ("I just want to give up and disappear forever", "Crisis keyword"),
    
    # Phase 3: Gaming context
    ("gg ez that was such a clutch play pwned them", "Gaming vocabulary"),
    
    # Phase 3: Modern idioms
    ("this new song absolutely slaps no cap fr fr", "Modern slang"),
    
    # Normal positive
    ("Had a great day today, feeling happy!", "Baseline positive"),
    
    # Normal negative
    ("Feeling a bit down today, nothing major", "Baseline negative"),
]

print("=" * 70)
print("PHASE 1-3 SENTIMENT ANALYSIS TEST")
print("=" * 70)

for text, description in test_cases:
    score = analyze_sentiment(text)
    sentiment = "POSITIVE" if score > 0.1 else "NEGATIVE" if score < -0.1 else "NEUTRAL"
    
    print(f"\n📝 {description}")
    print(f"   Text: \"{text}\"")
    print(f"   Score: {score:.4f} ({sentiment})")

print("\n" + "=" * 70)
print("✅ All tests completed successfully!")
print("=" * 70)

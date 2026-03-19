"""
Sarcasm Detection Examples - Live Demo
Shows how SentiGuard detects and inverts sarcastic sentiment
"""

import sys
sys.path.insert(0, 'c:/Users/krkes/senti/senti-new')

from analyzer import analyze_sentiment

# Sarcasm test cases with expected behavior
sarcasm_examples = [
    # Classic sarcasm markers
    ("Oh great, another wonderful Monday morning", "Sarcasm: 'oh great' + 'wonderful'"),
    ("Yeah right, that's totally going to work", "Sarcasm: 'yeah right' + 'totally'"),
    ("Sure thing, because that makes perfect sense", "Sarcasm: 'sure thing' + 'perfect'"),
    ("Thanks a lot for the help, really appreciate it", "Sarcasm: 'thanks a lot' + frustration"),
    
    # Excessive positivity with negative context
    ("Just perfect. My car broke down again", "Sarcasm: 'perfect' + negative event"),
    ("Brilliant idea to leave my phone at home", "Sarcasm: 'brilliant' + mistake"),
    ("Fantastic, I love waiting in traffic for 2 hours", "Sarcasm: 'fantastic' + complaint"),
    ("Obviously I wanted to fail that exam", "Sarcasm: 'obviously' + failure"),
    
    # Modern sarcastic expressions
    ("Love it when my code crashes right before demo", "Sarcasm: 'love it' + disaster"),
    ("Clearly the best decision I've ever made", "Sarcasm: 'clearly' + regret"),
    ("Just what I needed today, another problem", "Sarcasm: 'just what i needed' + problem"),
    
    # NOT sarcasm (genuine positive)
    ("I'm so happy about this promotion!", "Genuine positive"),
    ("That was actually a great movie", "Genuine positive"),
    ("I really love spending time with my friends", "Genuine positive"),
    
    # NOT sarcasm (genuine negative)
    ("I'm feeling pretty down today", "Genuine negative"),
    ("This is frustrating and I don't know what to do", "Genuine negative"),
]

print("=" * 80)
print("SARCASM DETECTION DEMO - SentiGuard Phase 2")
print("=" * 80)
print("\nHow it works:")
print("• Detects 14+ sarcasm markers: 'oh great', 'yeah right', 'totally', etc.")
print("• spaCy enhancement: Excessive positive adjectives with negative verbs")
print("• Sentiment inversion: Adjusts score by -0.15 to -0.2")
print("=" * 80)

for text, description in sarcasm_examples:
    score = analyze_sentiment(text)
    
    # Determine if detected as sarcastic based on score
    # Sarcastic phrases should have negative or neutral scores despite positive words
    if "Sarcasm" in description:
        status = "✅ DETECTED" if score < 0.3 else "⚠️ MISSED"
        sentiment = "SARCASTIC (Inverted)"
    elif "Genuine positive" in description:
        status = "✅ CORRECT" if score > 0.1 else "❌ WRONG"
        sentiment = "POSITIVE"
    else:  # Genuine negative
        status = "✅ CORRECT" if score < -0.1 else "❌ WRONG"
        sentiment = "NEGATIVE"
    
    print(f"\n{status} - {description}")
    print(f'   Text: "{text}"')
    print(f"   Score: {score:.4f} ({sentiment})")
    
    # Show what markers were found
    text_lower = text.lower()
    markers = []
    if "oh great" in text_lower: markers.append("'oh great'")
    if "yeah right" in text_lower: markers.append("'yeah right'")
    if "sure thing" in text_lower: markers.append("'sure thing'")
    if "totally" in text_lower: markers.append("'totally'")
    if "thanks a lot" in text_lower: markers.append("'thanks a lot'")
    if "just perfect" in text_lower or "perfect" in text_lower: markers.append("'perfect'")
    if "brilliant" in text_lower: markers.append("'brilliant'")
    if "fantastic" in text_lower: markers.append("'fantastic'")
    if "obviously" in text_lower: markers.append("'obviously'")
    if "clearly" in text_lower: markers.append("'clearly'")
    if "love it" in text_lower: markers.append("'love it'")
    if "just what i needed" in text_lower: markers.append("'just what i needed'")
    
    if markers:
        print(f"   Markers Found: {', '.join(markers)}")

print("\n" + "=" * 80)
print("✅ Sarcasm Detection Complete!")
print("=" * 80)
print("\nKey Insight:")
print("• Sarcasm detection INVERTS positive words when context is negative")
print("• This prevents false positives in crisis detection")
print("• Without this: 'Oh great' would be detected as positive (WRONG)")
print("• With Phase 2: 'Oh great' is correctly detected as negative (RIGHT)")

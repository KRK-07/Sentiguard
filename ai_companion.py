"""
AI Companion Module for Sentiguard
Provides conversational support with mood awareness and fallback options.
"""

import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import threading
from dataclasses import dataclass

# Configuration class
@dataclass
class AIConfig:
    """Configuration for AI companion features"""
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = "AIzaSyAPKupxMuuxpmw6Yk_DdMVAdkQ-cO3JDHQ"
    
    # Model Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Feature Flags
    ENABLE_GEMINI: bool = True
    ENABLE_LOCAL_FALLBACK: bool = True
    
    # Safety Settings (Higher limits for Pro subscription)
    MAX_DAILY_API_CALLS: int = 200
    RESPONSE_MAX_LENGTH: int = 300
    
    def __post_init__(self):
        # Can also load from environment if preferred
        env_key = os.getenv("GEMINI_API_KEY")
        if env_key:
            self.GEMINI_API_KEY = env_key
        self.ENABLE_GEMINI = bool(self.GEMINI_API_KEY)

# Global config instance
ai_config = AIConfig()

class AICompanion:
    """AI-powered conversational companion with mood awareness"""
    
    def __init__(self):
        self.conversation_history = []
        self.daily_api_calls = 0
        self.last_api_reset = datetime.now().date()
        self.empathy_templates = self._load_empathy_templates()
        self.conversation_starters = self._load_conversation_starters()
        
        # Initialize Gemini client if available
        self.gemini_client = None
        if ai_config.ENABLE_GEMINI:
            try:
                import google.generativeai as genai
                genai.configure(api_key=ai_config.GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel(ai_config.GEMINI_MODEL)
                print("Gemini AI client initialized successfully")
            except ImportError:
                print("Google GenerativeAI package not installed. Using fallback responses.")
                ai_config.ENABLE_GEMINI = False
            except Exception as e:
                print(f"Gemini initialization failed: {e}. Using fallback responses.")
                ai_config.ENABLE_GEMINI = False
    
    def _load_empathy_templates(self) -> Dict[str, List[str]]:
        """Load natural, conversational response templates"""
        return {
            'very_positive': [
                "That's awesome! What's got you feeling so good today?",
                "Love to hear it! Tell me more about what's going well 😊",
                "You sound really happy - that's great! What's been the highlight?",
                "Amazing! Your energy is infectious. What's been making you smile?"
            ],
            'positive': [
                "Nice! Sounds like things are looking up. What's been good?",
                "That's great to hear! How are you feeling about everything?", 
                "Good for you! Want to tell me more about what's been positive?",
                "I'm glad you're doing well! What's been working for you lately?"
            ],
            'neutral': [
                "Hey there! How's everything going with you?",
                "What's up? How are you feeling today?",
                "How are things? Anything on your mind?",
                "What's been happening? How are you doing?",
                "Hey! How's your day been so far?"
            ],
            'slightly_negative': [
                "Sounds like things might be a bit tough right now. Want to talk about it?",
                "I hear you - sometimes things just feel heavy, you know?",
                "That doesn't sound easy. How are you holding up?",
                "I'm here if you need to vent or just talk it out."
            ],
            'negative': [
                "That sounds really hard. I'm sorry you're going through this.",
                "Oof, that's tough. Want to tell me what's going on?",
                "I can tell this is difficult for you. I'm here to listen.",
                "That sounds overwhelming. Take your time - what's happening?"
            ],
            'very_negative': [
                "I'm really sorry you're struggling so much right now. You don't have to go through this alone.",
                "This sounds incredibly difficult. Thank you for sharing with me - that takes courage.",
                "I can hear how much pain you're in. Please know that I'm here and you matter.",
                "That sounds so hard. You're being really brave by reaching out."
            ]
        }
    
    def _load_conversation_starters(self) -> List[str]:
        """Load natural conversation starters"""
        return [
            "Hey! How's it going today?",
            "What's up? How are you feeling?", 
            "How are things going for you lately?",
            "What's been on your mind recently?",
            "How's your day been so far?",
            "What's happening in your world today?",
            "How are you doing? Anything interesting going on?",
            "Hey there! How are you holding up?",
            "What's new with you? How are you feeling?",
            "How's everything going? What's on your mind?"
        ]
    
    def _reset_daily_limits_if_needed(self):
        """Reset daily API call limits if it's a new day"""
        today = datetime.now().date()
        if today != self.last_api_reset:
            self.daily_api_calls = 0
            self.last_api_reset = today
    
    def _get_mood_category(self, mood_score: float) -> str:
        """Categorize mood score for appropriate responses"""
        if mood_score >= 0.6:
            return 'very_positive'
        elif mood_score >= 0.2:
            return 'positive'  
        elif mood_score >= -0.1:
            return 'neutral'
        elif mood_score >= -0.4:
            return 'slightly_negative'
        elif mood_score >= -0.7:
            return 'negative'
        else:
            return 'very_negative'
    
    async def generate_response(self, user_input: str, mood_context=None) -> str:
        """Generate empathetic response based on user input and mood context"""
        
        # Clean and validate input
        user_input = user_input.strip()
        if not user_input:
            return self._get_random_conversation_starter()
        
        # Handle different mood_context formats
        if mood_context is None:
            mood_context = {'current_mood': 0.0, 'trend': 'stable'}
        elif isinstance(mood_context, str):
            # Convert string mood to dict format
            mood_map = {
                'positive': 0.5, 'negative': -0.5, 'neutral': 0.0,
                'happy': 0.6, 'sad': -0.6, 'angry': -0.4, 'anxious': -0.3
            }
            mood_context = {
                'current_mood': mood_map.get(mood_context.lower(), 0.0),
                'trend': 'stable'
            }
        
        # Get mood information
        current_mood = mood_context.get('current_mood', 0.0)
        mood_trend = mood_context.get('trend', 'stable')
        
        # Try Gemini first if available
        if ai_config.ENABLE_GEMINI and self._can_make_api_call():
            try:
                response = await self._generate_gemini_response(user_input, mood_context)
                if response:
                    self.daily_api_calls += 1
                    self._add_to_conversation_history(user_input, response)
                    return response
            except Exception as e:
                print(f"Gemini response failed: {e}")
        
        # Fallback to template-based response
        return self._generate_template_response(user_input, current_mood, mood_trend)
    
    async def _generate_gemini_response(self, user_input: str, mood_context: Dict) -> Optional[str]:
        """Generate response using Google Gemini AI"""
        
        if not self.gemini_client:
            return None
        
        current_mood = mood_context.get('current_mood', 0.0)
        mood_category = self._get_mood_category(current_mood)
        recent_trend = mood_context.get('trend', 'stable')
        
        # Create context-aware prompt for Gemini
        prompt = f"""You are a compassionate AI companion for mental health support integrated into the Sentiguard app. You provide empathetic, supportive conversation.

Current context:
- User's current mood score: {current_mood:.2f} (range: -1.0 to 1.0, where -1 is very negative, 0 is neutral, +1 is very positive)
- Mood category: {mood_category}
- Recent trend: {recent_trend}

Guidelines for your response:
- Be warm, empathetic, and genuinely supportive
- Keep responses concise (2-3 sentences maximum)
- Acknowledge their emotional state appropriately
- Never give medical advice or diagnoses
- If they express serious distress, gently encourage professional help
- Use encouraging, hopeful language
- Be conversational and natural, like a caring friend
- If mood is very low, express gentle concern and support
- Respond to what they're actually saying, not just their mood score

User message: "{user_input}"

Respond as their caring AI companion who understands their current emotional state:"""

        try:
            # Generate content with Gemini
            response = await asyncio.to_thread(
                self.gemini_client.generate_content, 
                prompt
            )
            
            # Extract text from response
            if response and response.text:
                return response.text.strip()
            else:
                return None
            
        except Exception as e:
            print(f"Gemini API call failed: {e}")
            return None
    
    def _generate_template_response(self, user_input: str, mood_score: float, mood_trend: str) -> str:
        """Generate natural, contextual response using improved template system"""
        
        # First, try to generate a specific response based on user input
        specific_response = self._get_specific_response(user_input, mood_score)
        if specific_response:
            return specific_response
        
        # Otherwise, use mood-based templates
        mood_category = self._get_mood_category(mood_score)
        templates = self.empathy_templates.get(mood_category, self.empathy_templates['neutral'])
        base_response = random.choice(templates)
        
        return base_response
    
    def _get_specific_response(self, user_input: str, mood_score: float) -> str:
        """Generate specific responses based on what user actually said"""
        
        user_input_lower = user_input.lower()
        
        # Breakup/relationship responses
        if any(word in user_input_lower for word in ['breakup', 'broke up', 'break up', 'girlfriend', 'boyfriend', 'relationship ended']):
            responses = [
                "Oh wow, a breakup is never easy. That must be really painful right now. How are you holding up?",
                "I'm sorry to hear about your breakup. That's got to hurt a lot. Want to talk about what happened?", 
                "Breakups are so hard, even when you know it's for the best. How are you feeling about everything?",
                "That's really tough. Ending a relationship is never simple. Are you doing okay?"
            ]
            return random.choice(responses)
        
        # Career/work focus responses (only if asking about focus/career together)
        if ('focus' in user_input_lower or 'focused' in user_input_lower) and any(word in user_input_lower for word in ['career', 'job', 'work']):
            responses = [
                "That sounds like a really mature way to handle it. Focusing on your career can be a great way to channel that energy.",
                "Good for you for focusing on what you can control. Your career is something you can really invest in right now.", 
                "That's a healthy approach - putting energy into your goals and growth. What are you working on career-wise?",
                "I like that mindset. Sometimes redirecting focus to personal growth is exactly what we need."
            ]
            return random.choice(responses)
            
        # Excitement/positive work news
        if any(word in user_input_lower for word in ['excited', 'new job', 'promotion', 'hired']):
            responses = [
                "That's amazing! I'm so happy for you! Tell me more about this new opportunity.",
                "Wow, congratulations! That's such exciting news. How are you feeling about it?",
                "That's fantastic! New opportunities are always exciting. What's the new job like?",
                "Awesome! I love hearing good news like this. What are you most excited about?"
            ]
            return random.choice(responses)
            
        # Language-related responses
        if any(word in user_input_lower for word in ['language', 'languages', 'speak', 'multilingual', 'bilingual']):
            responses = [
                "I'm programmed primarily in English, but I can understand and discuss many languages! Are you multilingual yourself?",
                "English is my main language, but I find languages fascinating! Do you speak multiple languages?",
                "I work mainly in English, though I can discuss other languages. What languages are you interested in or do you speak?",
                "English is my primary language. Are you asking because you're learning a new language or speak others?"
            ]
            return random.choice(responses)

        # Greeting responses
        if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'how are you']):
            responses = [
                "Hey! I'm doing well, thanks for asking. How are you feeling today?",
                "Hi there! Good to see you. What's going on with you?",
                "Hello! I'm here and ready to chat. How are things with you?",
                "Hey! Thanks for checking in. How's your day been?"
            ]
            return random.choice(responses)
            
        # Sadness/feeling down
        if any(word in user_input_lower for word in ['sad', 'depressed', 'down', 'upset', 'hurt']):
            responses = [
                "I'm sorry you're feeling this way. That sounds really hard. What's been going on?",
                "That must be difficult to deal with. Do you want to talk about what's making you feel down?", 
                "I hear you. Sometimes we just need to feel sad for a bit, and that's okay. Want to share more?",
                "That doesn't sound fun at all. I'm here if you want to talk through what's bothering you."
            ]
            return random.choice(responses)
            
        # Anxiety/stress responses
        if any(word in user_input_lower for word in ['anxious', 'anxiety', 'stressed', 'worried', 'nervous']):
            responses = [
                "Anxiety can be so overwhelming. What's been making you feel anxious lately?",
                "That sounds stressful. Sometimes our minds just won't quiet down, huh? What's on your mind?",
                "I get that - anxiety is tough to deal with. Is there something specific that's worrying you?",
                "Stress is the worst. Want to talk about what's been weighing on you?"
            ]
            return random.choice(responses)
            
        # General work/job responses (but not excited ones)
        if any(word in user_input_lower for word in ['work', 'job']) and not any(word in user_input_lower for word in ['excited', 'love', 'great', 'amazing']):
            responses = [
                "How are things going at work? Sometimes work stuff can be complicated.",
                "Work can be stressful sometimes. What's been going on with your job?",
                "Is everything okay with work? Want to talk about what's happening?",
                "Work stuff can be tough to navigate. How are you handling everything?"
            ]
            return random.choice(responses)

        # Knowledge/question responses
        if any(phrase in user_input_lower for phrase in ['do you know', 'can you tell', 'tell me about', 'what is', 'what are']) or user_input_lower.startswith('tell me'):
            responses = [
                "That's an interesting question! I'd love to help you explore that. What specifically would you like to know?",
                "Great question! While I might not have all the details, I'm here to chat about it. What's got you curious?",
                "I appreciate your curiosity! Let's talk about that - what's making you interested in this topic?",
                "That's something worth discussing! What's prompting this question? I'm here to explore it with you."
            ]
            return random.choice(responses)
            
        return None  # No specific match found
    
    def _get_contextual_additions(self, user_input: str, mood_score: float, mood_trend: str) -> str:
        """Generate contextual additions based on input analysis and mood trends"""
        
        user_input_lower = user_input.lower()
        additions = []
        
        # Analyze user input for specific concerns
        if any(word in user_input_lower for word in ['stress', 'stressed', 'overwhelmed', 'pressure']):
            additions.append("Stress can feel overwhelming. Remember to take deep breaths and take things one step at a time.")
        
        elif any(word in user_input_lower for word in ['tired', 'exhausted', 'drained']):
            additions.append("It sounds like you need some rest. Be gentle with yourself and prioritize self-care.")
        
        elif any(word in user_input_lower for word in ['anxious', 'anxiety', 'worried', 'nervous']):
            additions.append("Anxiety can be really challenging. Grounding techniques like focusing on your breath can help.")
        
        elif any(word in user_input_lower for word in ['sad', 'depressed', 'down', 'low']):
            additions.append("It's okay to feel sad sometimes. Your feelings are valid, and this difficult time will pass.")
        
        elif any(word in user_input_lower for word in ['excited', 'happy', 'great', 'amazing', 'wonderful']):
            additions.append("I love hearing about the positive things in your life! Hold onto these good feelings.")
        
        # Add trend-specific insights
        if mood_trend == 'improving':
            additions.append("I've noticed some positive changes in your patterns lately. Keep nurturing what's helping you feel better!")
        elif mood_trend == 'declining':
            additions.append("I notice things have been challenging recently. Please remember that ups and downs are normal, and support is available.")
        
        # Add mood-specific suggestions
        if mood_score < -0.5:
            suggestions = [
                "Would a brief mindfulness exercise help right now?",
                "Sometimes reaching out to a trusted friend can provide comfort.",
                "Consider doing one small thing that usually brings you a little peace."
            ]
            additions.append(random.choice(suggestions))
        
        return " ".join(additions)
    
    def _can_make_api_call(self) -> bool:
        """Check if we can make an API call within daily limits"""
        self._reset_daily_limits_if_needed()
        return self.daily_api_calls < ai_config.MAX_DAILY_API_CALLS
    
    def _get_random_conversation_starter(self) -> str:
        """Get a random conversation starter for proactive check-ins"""
        return random.choice(self.conversation_starters)
    
    def _add_to_conversation_history(self, user_input: str, response: str):
        """Add exchange to conversation history"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input[:100],  # Truncate for privacy
            'response': response[:100],      # Truncate for privacy  
            'mood_aware': True
        }
        
        self.conversation_history.append(entry)
        
        # Keep only last 10 exchanges to prevent memory issues
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def generate_proactive_check_in(self, recent_patterns: Dict) -> Optional[str]:
        """Generate proactive check-in message based on recent patterns"""
        
        # Don't be too frequent with check-ins
        if self.conversation_history:
            last_interaction = datetime.fromisoformat(self.conversation_history[-1]['timestamp'])
            if datetime.now() - last_interaction < timedelta(hours=2):
                return None
        
        # Analyze patterns for appropriate check-in
        if recent_patterns.get('mood_declining', False):
            return "I've noticed your mood has been a bit lower lately. How are you feeling today? I'm here to listen. 💙"
        
        elif recent_patterns.get('stress_detected', False):
            return "It seems like you might be experiencing some stress. Would you like to talk about what's on your mind? 🤗"
        
        elif recent_patterns.get('improvement_noted', False):
            return "I've noticed some positive changes in your patterns! That's wonderful. How are things feeling for you today? ✨"
        
        elif recent_patterns.get('consistent_low_mood', False):
            return "I want to check in with you. You've been on my mind. How are you holding up today? 💜"
        
        # Gentle general check-in
        elif random.random() < 0.3:  # 30% chance for random check-in
            return random.choice([
                "Just wanted to see how you're doing today. 😊",
                "How's your heart feeling right now? 💙",
                "I'm here if you want to share what's on your mind. 🤗"
            ])
        
        return None
    
    def get_mood_based_suggestions(self, mood_score: float) -> List[str]:
        """Provide mood-appropriate wellness suggestions"""
        
        if mood_score < -0.5:
            return [
                "Try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste",
                "Take 5 slow, deep breaths - inhale for 4 counts, hold for 4, exhale for 6",
                "Consider reaching out to someone you trust for support",
                "Go for a short walk, even if it's just around your room",
                "Write down one thing you're grateful for, no matter how small"
            ]
        
        elif mood_score < -0.2:
            return [
                "Take a few minutes to do something that usually brings you comfort",
                "Listen to calming music or nature sounds",
                "Practice gentle stretching or movement",
                "Drink a glass of water and take a moment to breathe",
                "Do one small act of self-kindness"
            ]
        
        elif mood_score > 0.4:
            return [
                "This positive energy is wonderful! Consider sharing it with someone you care about",
                "Take a moment to savor this good feeling",
                "Maybe capture this moment in a journal or photo",
                "Use this energy to do something creative or fun",
                "Consider what's contributing to this positive mood so you can nurture it"
            ]
        
        else:
            return [
                "Take a moment to check in with yourself - how are you feeling right now?",
                "Practice mindful breathing for a few minutes",
                "Do something small that brings you joy",
                "Connect with nature, even if it's just looking out a window",
                "Show yourself the same kindness you'd show a good friend"
            ]
    
    def get_api_status(self) -> Dict:
        """Get current API usage status"""
        self._reset_daily_limits_if_needed()
        
        return {
            'gemini_available': ai_config.ENABLE_GEMINI,
            'api_calls_today': self.daily_api_calls,
            'api_calls_remaining': ai_config.MAX_DAILY_API_CALLS - self.daily_api_calls,
            'fallback_enabled': ai_config.ENABLE_LOCAL_FALLBACK
        }

# Global instance for use throughout the application
ai_companion = AICompanion()

# Convenience functions for easy integration
async def chat_with_ai(user_message: str, current_mood: float = 0.0, mood_trend: str = 'stable') -> str:
    """Simplified interface for AI chat"""
    mood_context = {
        'current_mood': current_mood,
        'trend': mood_trend
    }
    return await ai_companion.generate_response(user_message, mood_context)

def get_proactive_message(mood_patterns: Dict) -> Optional[str]:
    """Simplified interface for proactive check-ins"""
    return ai_companion.generate_proactive_check_in(mood_patterns)

def get_mood_suggestions(mood_score: float) -> List[str]:
    """Simplified interface for mood-based suggestions"""
    return ai_companion.get_mood_based_suggestions(mood_score)

# Test function for development
if __name__ == "__main__":
    async def test_ai_companion():
        print("Testing Gemini AI Companion...")
        
        # Test different mood scenarios
        test_cases = [
            ("I'm feeling really anxious about work today", -0.4),
            ("Had an amazing day! Everything went perfectly", 0.8),
            ("Just feeling kind of meh, nothing special", 0.0),
            ("I recently had a breakup with my girlfriend, what can I do to keep myself focused on my career?", -0.3)
        ]
        
        for message, mood in test_cases:
            print(f"\n--- Test: {message} (mood: {mood}) ---")
            response = await chat_with_ai(message, mood)
            print(f"Gemini Response: {response}")
            
            suggestions = get_mood_suggestions(mood)
            print(f"Suggestions: {suggestions[:2]}")  # Show first 2 suggestions
    
    # Run test
    asyncio.run(test_ai_companion())
"""
Personalized Insights Module for Sentiguard
Generates LLM-powered personalized mental health insights using existing data
Integrates with mood_history.json, analyzer.py, and keylogger data
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
from collections import defaultdict, Counter

@dataclass
class PersonalizedInsight:
    """Structure for a single personalized insight"""
    insight_type: str  # 'pattern_discovery', 'prediction', 'recommendation', 'celebration'
    title: str
    content: str
    confidence: float  # 0.0 to 1.0
    priority: int  # 1-5, with 1 being highest priority
    actionable_steps: List[str]
    data_sources: List[str]  # Which data sources were used
    generated_at: str

@dataclass
class InsightSummary:
    """Summary of all insights for a user"""
    total_insights: int
    high_priority_count: int
    main_theme: str  # Overall theme of insights
    personal_message: str  # AI-generated personal message
    insights: List[PersonalizedInsight]
    report_generated_at: str

class PersonalizedInsightsEngine:
    """Generates personalized mental health insights using LLM and existing data"""
    
    def __init__(self):
        self.data_sources = {
            'mood_history': 'mood_history.json',
            'user_settings': 'user_settings.json',
            'keystrokes': 'keystrokes.txt',
            'alert_status': 'alert_status.json'
        }
        self.insights_cache_file = 'insights_cache.json'
        self.last_analysis_time = None
        
    def load_existing_data(self) -> Dict[str, Any]:
        """Load all existing data sources without modifying them"""
        data = {}
        
        # Load mood history
        try:
            if os.path.exists(self.data_sources['mood_history']):
                with open(self.data_sources['mood_history'], 'r') as f:
                    data['mood_history'] = json.load(f)
            else:
                data['mood_history'] = []
        except Exception as e:
            print(f"Error loading mood history: {e}")
            data['mood_history'] = []
        
        # Load user settings
        try:
            if os.path.exists(self.data_sources['user_settings']):
                with open(self.data_sources['user_settings'], 'r') as f:
                    data['user_settings'] = json.load(f)
            else:
                data['user_settings'] = {}
        except Exception as e:
            print(f"Error loading user settings: {e}")
            data['user_settings'] = {}
        
        # Load alert status
        try:
            if os.path.exists(self.data_sources['alert_status']):
                with open(self.data_sources['alert_status'], 'r') as f:
                    data['alert_status'] = json.load(f)
            else:
                data['alert_status'] = {}
        except Exception as e:
            print(f"Error loading alert status: {e}")
            data['alert_status'] = {}
        
        # Analyze keystrokes file (if exists) - just get metadata, not content
        data['keystroke_metadata'] = self._analyze_keystroke_metadata()
        
        return data
    
    def _analyze_keystroke_metadata(self) -> Dict[str, Any]:
        """Analyze keystroke file metadata without reading sensitive content"""
        metadata = {}
        
        try:
            if os.path.exists(self.data_sources['keystrokes']):
                stat_info = os.stat(self.data_sources['keystrokes'])
                
                # Get file size and modification time (indicates activity levels)
                metadata['file_size'] = stat_info.st_size
                metadata['last_modified'] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
                # Count lines without reading sensitive content
                with open(self.data_sources['keystrokes'], 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
                
                metadata['activity_level'] = 'high' if line_count > 500 else 'moderate' if line_count > 100 else 'low'
                metadata['total_interactions'] = line_count
            else:
                metadata = {'activity_level': 'none', 'total_interactions': 0}
                
        except Exception as e:
            print(f"Error analyzing keystroke metadata: {e}")
            metadata = {'activity_level': 'unknown', 'total_interactions': 0}
        
        return metadata
    
    def analyze_mood_patterns(self, mood_data: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in mood data for insight generation"""
        # More flexible data requirements - need at least 5 data points instead of being too strict
        if not mood_data or len(mood_data) < 5:
            return {'insufficient_data': True}
        
        # Recent vs historical comparison (look back 14 days instead of 7 for more data)
        recent_entries = [entry for entry in mood_data if self._is_recent(entry.get('timestamp', ''), 14)]
        historical_entries = [entry for entry in mood_data if not self._is_recent(entry.get('timestamp', ''), 14)]
        
        patterns = {}
        
        # Basic statistics - use all available data if recent is insufficient
        mood_entries_to_analyze = recent_entries if len(recent_entries) >= 3 else mood_data[-10:]  # Use last 10 if recent is too sparse
        
        if mood_entries_to_analyze:
            recent_moods = [entry.get('mood_score', entry.get('score', 0)) for entry in mood_entries_to_analyze if 'mood_score' in entry or 'score' in entry]
            if recent_moods:
                patterns['recent_average'] = statistics.mean(recent_moods)
                patterns['recent_trend'] = self._calculate_trend(recent_moods)
                patterns['mood_volatility'] = statistics.stdev(recent_moods) if len(recent_moods) > 1 else 0
        
        # Weekly patterns
        patterns['weekly_patterns'] = self._analyze_weekly_patterns(mood_data)
        
        # Improvement/decline detection
        patterns['improvement_periods'] = self._detect_improvement_periods(mood_data)
        patterns['challenging_periods'] = self._detect_challenging_periods(mood_data)
        
        # Integration with analyzer.py - get current sentiment analysis
        patterns['analyzer_integration'] = self._get_analyzer_insights()
        
        # Data richness
        patterns['data_points'] = len(mood_data)
        patterns['tracking_consistency'] = self._calculate_tracking_consistency(mood_data)
        
        return patterns
    
    def _get_analyzer_insights(self) -> Dict[str, Any]:
        """Get insights from existing analyzer.py integration"""
        insights = {}
        
        try:
            # Import analyzer functions
            from analyzer import get_recent_mood, count_below_threshold, get_alert_status
            
            # Get current mood state from analyzer
            try:
                current_mood = get_recent_mood()
                insights['current_analyzer_mood'] = current_mood
            except:
                insights['current_analyzer_mood'] = None
            
            # Get alert status information
            try:
                alert_status = get_alert_status()
                insights['alert_status'] = alert_status
            except:
                insights['alert_status'] = None
            
            # Get crisis indicator count
            try:
                crisis_count = count_below_threshold()
                if isinstance(crisis_count, tuple):
                    insights['crisis_indicators'] = crisis_count[0]
                else:
                    insights['crisis_indicators'] = crisis_count
            except:
                insights['crisis_indicators'] = 0
                
        except ImportError:
            insights['analyzer_available'] = False
            
        return insights
    
    def _is_recent(self, timestamp: str, days: int) -> bool:
        """Check if timestamp is within recent days"""
        try:
            if not timestamp:
                return False
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return datetime.now() - dt <= timedelta(days=days)
        except:
            return False
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend using simple linear regression"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x_squared_sum = sum(i * i for i in range(n))
        
        try:
            slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum * x_sum)
            return slope
        except ZeroDivisionError:
            return 0.0
    
    def _analyze_weekly_patterns(self, mood_data: List[Dict]) -> Dict[str, Any]:
        """Analyze mood patterns by day of week"""
        weekly_moods = defaultdict(list)
        
        for entry in mood_data:
            if 'timestamp' in entry and 'mood_score' in entry:
                try:
                    dt = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    day_name = dt.strftime('%A')
                    weekly_moods[day_name].append(entry['mood_score'])
                except:
                    continue
        
        # Calculate averages for each day
        weekly_averages = {}
        for day, moods in weekly_moods.items():
            if moods:
                weekly_averages[day] = statistics.mean(moods)
        
        # Find best and worst days
        best_day = max(weekly_averages.items(), key=lambda x: x[1]) if weekly_averages else None
        worst_day = min(weekly_averages.items(), key=lambda x: x[1]) if weekly_averages else None
        
        return {
            'daily_averages': weekly_averages,
            'best_day': best_day,
            'worst_day': worst_day,
            'pattern_strength': abs(best_day[1] - worst_day[1]) if best_day and worst_day else 0
        }
    
    def _detect_improvement_periods(self, mood_data: List[Dict]) -> List[Dict]:
        """Detect periods where mood significantly improved"""
        improvements = []
        
        if len(mood_data) < 5:
            return improvements
        
        moods = []
        timestamps = []
        
        for entry in mood_data:
            if 'mood_score' in entry and 'timestamp' in entry:
                moods.append(entry['mood_score'])
                timestamps.append(entry['timestamp'])
        
        # Look for improvement streaks
        for i in range(len(moods) - 3):
            window = moods[i:i+4]
            if len(window) >= 3:
                trend = self._calculate_trend(window)
                if trend > 0.1:  # Significant positive trend
                    improvements.append({
                        'start_date': timestamps[i],
                        'end_date': timestamps[i+3],
                        'improvement_rate': trend,
                        'start_mood': window[0],
                        'end_mood': window[-1]
                    })
        
        return improvements
    
    def _detect_challenging_periods(self, mood_data: List[Dict]) -> List[Dict]:
        """Detect periods where mood was consistently challenging"""
        challenges = []
        
        if len(mood_data) < 3:
            return challenges
        
        moods = []
        timestamps = []
        
        for entry in mood_data:
            if 'mood_score' in entry and 'timestamp' in entry:
                moods.append(entry['mood_score'])
                timestamps.append(entry['timestamp'])
        
        # Look for challenging periods (consistently low mood)
        for i in range(len(moods) - 2):
            window = moods[i:i+3]
            if all(mood < -0.3 for mood in window):  # Consistently negative
                challenges.append({
                    'start_date': timestamps[i],
                    'end_date': timestamps[i+2],
                    'severity': statistics.mean(window),
                    'duration_days': 3
                })
        
        return challenges
    
    def _calculate_tracking_consistency(self, mood_data: List[Dict]) -> float:
        """Calculate how consistently the user tracks their mood"""
        if not mood_data:
            return 0.0
        
        # Get dates of entries
        dates = []
        for entry in mood_data:
            if 'timestamp' in entry:
                try:
                    dt = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    dates.append(dt.date())
                except:
                    continue
        
        if len(dates) < 2:
            return 0.0
        
        # Calculate consistency over last 30 days
        unique_dates = set(dates)
        days_tracked = len(unique_dates)
        possible_days = min(30, (max(dates) - min(dates)).days + 1)
        
        return days_tracked / possible_days if possible_days > 0 else 0.0
    
    def generate_template_insights(self, patterns, user_data):
        """
        Generate insights using template patterns when LLM is unavailable
        """
        insights = []
        
        # Mood trend insight
        avg_mood = patterns.get('average_mood', 0)
        recent_scores = patterns.get('recent_scores', [])
        
        if len(recent_scores) >= 2:
            recent_avg = sum(recent_scores[-3:]) / len(recent_scores[-3:])
            older_avg = sum(recent_scores[:-3]) / max(1, len(recent_scores[:-3]))
            
            if recent_avg > older_avg + 0.1:
                trend_text = "Your mood has been improving lately! You've shown an upward trend in the past few days. Keep up whatever positive changes you've been making."
            elif recent_avg < older_avg - 0.1:
                trend_text = "I notice your mood has been trending downward recently. This is completely normal - everyone has ups and downs. Consider focusing on self-care activities that usually help you feel better."
            else:
                trend_text = "Your mood has been relatively stable recently. Consistency in emotional well-being is a positive sign of emotional resilience."
            
            insights.append(PersonalizedInsight(
                insight_type="trend_analysis",
                title="📈 Mood Trend Analysis",
                content=trend_text,
                confidence=0.8,
                priority=2,
                actionable_steps=[
                    "Continue monitoring your daily mood patterns",
                    "Practice mindfulness to stay aware of emotional changes"
                ],
                data_sources=['mood_history'],
                generated_at=datetime.now().isoformat()
            ))
        
        # Emotional pattern insight
        if avg_mood > 0.3:
            pattern_text = "You tend to maintain a positive outlook! Your mood data shows you generally experience more positive emotions than negative ones. This optimistic pattern is associated with better mental health outcomes."
            steps = [
                "Continue engaging in activities that bring you joy",
                "Share your positive energy with others"
            ]
        elif avg_mood < -0.3:
            pattern_text = "Your mood data indicates you've been experiencing more challenging emotions lately. Remember that it's completely normal to go through difficult periods, and seeking support is a sign of strength."
            steps = [
                "Consider talking to someone you trust about how you're feeling",
                "Engage in gentle self-care activities"
            ]
        else:
            pattern_text = "Your emotional patterns show a balanced mix of different moods. This emotional variety is healthy and shows you're in touch with your feelings."
            steps = [
                "Continue being aware of your emotional states",
                "Practice healthy coping strategies for difficult emotions"
            ]
        
        insights.append(PersonalizedInsight(
            insight_type="emotional_pattern",
            title="🎭 Emotional Pattern Recognition",
            content=pattern_text,
            confidence=0.75,
            priority=2,
            actionable_steps=steps,
            data_sources=['mood_history'],
            generated_at=datetime.now().isoformat()
        ))
        
        # Activity suggestion based on patterns
        if patterns.get('needs_support', False) or avg_mood < -0.2:
            activity_text = "Based on your recent mood patterns, here are some evidence-based activities that might help boost your emotional well-being: deep breathing exercises, gentle physical activity, connecting with supportive friends or family, or engaging in a hobby you enjoy."
            steps = [
                "Try a 5-minute mindfulness meditation",
                "Take a short walk outdoors"
            ]
        else:
            activity_text = "Your mood patterns suggest you're doing well emotionally! To maintain this positive state, consider continuing your current healthy habits and perhaps exploring new activities that challenge you in positive ways."
            steps = [
                "Write in a gratitude journal",
                "Connect with someone who makes you feel good"
            ]
        
        insights.append(PersonalizedInsight(
            insight_type="activity_suggestion",
            title="🎯 Personalized Activity Suggestions",
            content=activity_text,
            confidence=0.7,
            priority=3,
            actionable_steps=steps,
            data_sources=['mood_history', 'keystroke_metadata'],
            generated_at=datetime.now().isoformat()
        ))
        
        return insights

    async def generate_llm_insights(self, patterns, user_data):
        """Generate insights using LLM based on analyzed patterns"""
        
        # Import AI companion for LLM access
        try:
            from ai_companion import ai_companion
        except ImportError:
            print("AI companion not available for insight generation.")
            return None  # Return None to trigger fallback
        
        insights = []
        
        # Create different types of insight prompts
        prompts = self._create_insight_prompts(patterns, user_data)
        
        for prompt_type, prompt in prompts.items():
            try:
                if ai_companion.gemini_client:
                    response = await asyncio.to_thread(
                        ai_companion.gemini_client.generate_content,
                        prompt
                    )
                    
                    if response and response.text:
                        insight = self._format_llm_response(prompt_type, response.text, patterns)
                        if insight:
                            insights.append(insight)
                            
            except Exception as e:
                print(f"Error generating {prompt_type} insight: {e}")
                # Check if this is a quota error
                if "429" in str(e) or "quota" in str(e).lower():
                    print("API quota exceeded - will use fallback insights")
                    return None  # Trigger fallback system
                continue
        
        return insights[:5] if insights else None  # Return top 5 insights or None for fallback
    
    def _create_insight_prompts(self, patterns: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, str]:
        """Create prompts for different types of insights"""
        prompts = {}
        
        # Pattern Discovery Insight
        if patterns.get('weekly_patterns', {}).get('best_day'):
            best_day = patterns['weekly_patterns']['best_day']
            worst_day = patterns['weekly_patterns']['worst_day']
            
            prompts['pattern_discovery'] = f"""
            As a caring mental health AI, analyze this user's weekly mood pattern:
            - Best day: {best_day[0]} (average mood: {best_day[1]:.2f})
            - Worst day: {worst_day[0]} (average mood: {worst_day[1]:.2f})
            - Pattern strength: {patterns['weekly_patterns'].get('pattern_strength', 0):.2f}
            
            Generate a warm, personalized insight (2-3 sentences) about what this pattern reveals about them,
            followed by one practical suggestion to leverage their good days or improve difficult days.
            Be conversational, empathetic, and specific to their pattern.
            """
        
        # Improvement Recognition
        improvements = patterns.get('improvement_periods', [])
        if improvements:
            recent_improvement = improvements[-1]  # Most recent improvement
            
            prompts['improvement_celebration'] = f"""
            This user recently showed improvement in their mental health:
            - Improvement rate: {recent_improvement.get('improvement_rate', 0):.3f}
            - Mood went from {recent_improvement.get('start_mood', 0):.2f} to {recent_improvement.get('end_mood', 0):.2f}
            - Period: {recent_improvement.get('start_date', '')} to {recent_improvement.get('end_date', '')}
            
            Write an encouraging, personalized message (2-3 sentences) that:
            1. Celebrates their progress authentically
            2. Helps them recognize their own strength
            3. Encourages them to continue their positive trajectory
            Be warm, specific, and genuinely congratulatory.
            """
        
        # Trend Analysis
        if patterns.get('recent_average') is not None:
            recent_avg = patterns['recent_average']
            trend = patterns.get('recent_trend', 0)
            volatility = patterns.get('mood_volatility', 0)
            
            prompts['trend_analysis'] = f"""
            Analyze this user's recent mental health trends:
            - Recent average mood: {recent_avg:.2f} (scale: -1 to +1)
            - Mood trend: {trend:.3f} (positive = improving, negative = declining)
            - Volatility: {volatility:.2f} (higher = more unstable)
            - Tracking consistency: {patterns.get('tracking_consistency', 0):.1%}
            
            Provide a personalized insight (2-3 sentences) that:
            1. Acknowledges their current state with empathy
            2. Puts their trends in perspective
            3. Offers gentle encouragement or validation
            Be supportive and focus on their journey, not just the numbers.
            """
        
        # Activity Level Insight
        keystroke_data = user_data.get('keystroke_metadata', {})
        activity_level = keystroke_data.get('activity_level', 'unknown')
        
        if activity_level != 'unknown':
            prompts['activity_insight'] = f"""
            This user shows {activity_level} digital activity levels.
            Total interactions: {keystroke_data.get('total_interactions', 0)}
            
            As a mental health AI, provide a brief, personalized insight (1-2 sentences) about how their 
            digital activity might relate to their mental well-being. Be encouraging and avoid being judgmental 
            about high or low activity levels. Focus on balance and self-awareness.
            """
        
        # Analyzer Integration Insight
        analyzer_data = patterns.get('analyzer_integration', {})
        if analyzer_data.get('crisis_indicators', 0) > 0 or analyzer_data.get('current_analyzer_mood') is not None:
            current_mood = analyzer_data.get('current_analyzer_mood', 'unknown')
            crisis_count = analyzer_data.get('crisis_indicators', 0)
            
            prompts['safety_insight'] = f"""
            Based on real-time analysis from the user's sentiment analyzer:
            - Current mood reading: {current_mood}
            - Crisis indicators detected: {crisis_count}
            
            As a caring mental health AI, provide a supportive insight (2-3 sentences) that:
            1. Acknowledges their current emotional state with empathy
            2. Validates their experience without judgment
            3. Offers gentle encouragement and hope
            
            If crisis indicators are present, be extra supportive while maintaining a hopeful tone.
            Focus on their strength and resilience.
            """
        
        return prompts
    
    def _format_llm_response(self, insight_type: str, llm_response: str, patterns: Dict) -> Optional[PersonalizedInsight]:
        """Format LLM response into structured insight"""
        
        if not llm_response or len(llm_response.strip()) < 10:
            return None
        
        # Clean up the response
        content = llm_response.strip()
        
        # Extract actionable steps if present
        actionable_steps = []
        if "suggestion:" in content.lower() or "recommend" in content.lower():
            # Try to extract actionable items
            sentences = content.split('.')
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['try', 'consider', 'suggestion', 'recommend']):
                    actionable_steps.append(sentence.strip())
        
        # Determine priority based on insight type
        priority_map = {
            'improvement_celebration': 2,  # Medium-high priority
            'pattern_discovery': 1,       # High priority  
            'trend_analysis': 3,          # Medium priority
            'activity_insight': 4         # Lower priority
        }
        
        # Determine confidence based on data quality
        data_points = patterns.get('data_points', 0)
        confidence = min(0.9, max(0.4, data_points / 20))
        
        # Create title based on insight type
        title_map = {
            'pattern_discovery': '📊 Your Weekly Pattern',
            'improvement_celebration': '🌟 Progress Recognition', 
            'trend_analysis': '📈 Recent Trends',
            'activity_insight': '💻 Digital Wellness'
        }
        
        return PersonalizedInsight(
            insight_type=insight_type,
            title=title_map.get(insight_type, '💡 Personal Insight'),
            content=content,
            confidence=confidence,
            priority=priority_map.get(insight_type, 3),
            actionable_steps=actionable_steps[:2],  # Max 2 steps
            data_sources=['mood_history', 'keystroke_metadata'],
            generated_at=datetime.now().isoformat()
        )
    
    async def generate_personal_summary(self, insights: List[PersonalizedInsight], patterns: Dict) -> str:
        """Generate a personal summary message using LLM"""
        
        if not insights:
            return "Keep tracking your mental health journey - I'll have personalized insights for you soon! 🌟"
        
        try:
            from ai_companion import ai_companion
        except ImportError:
            return "Your mental health journey is unique and valuable. Keep taking care of yourself! 💙"
        
        # Create summary prompt
        insight_summaries = [f"- {insight.title}: {insight.content[:100]}..." for insight in insights[:3]]
        data_points = patterns.get('data_points', 0)
        consistency = patterns.get('tracking_consistency', 0)
        
        summary_prompt = f"""
        Create a warm, personal summary message for someone tracking their mental health.
        
        Their recent insights include:
        {chr(10).join(insight_summaries)}
        
        They have {data_points} mood entries and {consistency:.1%} tracking consistency.
        
        Write a brief, encouraging personal message (2-3 sentences) that:
        1. Acknowledges their commitment to mental health
        2. Highlights something positive from their insights
        3. Provides gentle motivation to continue
        
        Be warm, personal, and genuinely supportive. Use "you" and make it feel like a friend talking.
        """
        
        try:
            if ai_companion.gemini_client:
                response = await asyncio.to_thread(
                    ai_companion.gemini_client.generate_content,
                    summary_prompt
                )
                
                if response and response.text:
                    return response.text.strip()
        except Exception as e:
            print(f"Error generating personal summary: {e}")
        
        # Fallback message
        return f"You've been consistently tracking your mental health journey - that takes real commitment! With {data_points} data points, you're building valuable self-awareness. Keep going! 💙"
    
    def save_insights_cache(self, insights_summary: InsightSummary):
        """Save insights to cache file"""
        try:
            cache_data = {
                'summary': asdict(insights_summary),
                'last_generated': datetime.now().isoformat()
            }
            
            with open(self.insights_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving insights cache: {e}")
    
    def load_cached_insights(self) -> Optional[InsightSummary]:
        """Load cached insights if they're recent enough"""
        try:
            if not os.path.exists(self.insights_cache_file):
                return None
            
            with open(self.insights_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still fresh (within 6 hours)
            last_generated = datetime.fromisoformat(cache_data['last_generated'])
            if datetime.now() - last_generated > timedelta(hours=6):
                return None
            
            # Convert back to InsightSummary object
            summary_data = cache_data['summary']
            insights = [PersonalizedInsight(**insight) for insight in summary_data['insights']]
            
            return InsightSummary(
                total_insights=summary_data['total_insights'],
                high_priority_count=summary_data['high_priority_count'],
                main_theme=summary_data['main_theme'],
                personal_message=summary_data['personal_message'],
                insights=insights,
                report_generated_at=summary_data['report_generated_at']
            )
            
        except Exception as e:
            print(f"Error loading cached insights: {e}")
            return None
    
    async def generate_personalized_insights(self, force_refresh: bool = False) -> Optional[InsightSummary]:
        """Main method to generate personalized insights"""
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_insights = self.load_cached_insights()
            if cached_insights:
                return cached_insights
        
        # Load existing data
        user_data = self.load_existing_data()
        
        # Analyze patterns
        patterns = self.analyze_mood_patterns(user_data['mood_history'])
        
        if patterns.get('insufficient_data'):
            return None
        
        # Generate LLM insights (with fallback for API limitations)
        llm_insights = await self.generate_llm_insights(patterns, user_data)
        
        # If LLM insights failed (e.g., API quota), generate template-based insights
        if not llm_insights:
            llm_insights = self.generate_template_insights(patterns, user_data)
        
        # Convert to PersonalizedInsight objects
        insights = []
        for llm_insight in llm_insights:
            if isinstance(llm_insight, PersonalizedInsight):
                insights.append(llm_insight)
        
        if not insights:
            return None
        
        # Sort by priority
        insights.sort(key=lambda x: x.priority)
        
        # Generate personal summary
        personal_message = await self.generate_personal_summary(insights, patterns)
        
        # Determine main theme
        insight_types = [insight.insight_type for insight in insights]
        most_common_type = max(set(insight_types), key=insight_types.count) if insight_types else 'general'
        
        theme_map = {
            'pattern_discovery': 'Pattern Recognition',
            'improvement_celebration': 'Progress & Growth',
            'trend_analysis': 'Current Trends',
            'activity_insight': 'Digital Wellness'
        }
        main_theme = theme_map.get(most_common_type, 'Personal Growth')
        
        # Create summary
        insights_summary = InsightSummary(
            total_insights=len(insights),
            high_priority_count=len([i for i in insights if i.priority <= 2]),
            main_theme=main_theme,
            personal_message=personal_message,
            insights=insights,
            report_generated_at=datetime.now().isoformat()
        )
        
        # Cache the results
        self.save_insights_cache(insights_summary)
        
        return insights_summary

# Global instance
insights_engine = PersonalizedInsightsEngine()

# Convenience functions for easy integration
async def get_personalized_insights(force_refresh: bool = False) -> Optional[InsightSummary]:
    """Get personalized insights for the current user"""
    return await insights_engine.generate_personalized_insights(force_refresh)

async def refresh_insights() -> Optional[InsightSummary]:
    """Force refresh of personalized insights"""
    return await insights_engine.generate_personalized_insights(force_refresh=True)

# Test function
if __name__ == "__main__":
    async def test_insights():
        print("Testing Personalized Insights Engine...")
        
        summary = await get_personalized_insights()
        
        if summary:
            print(f"\n=== PERSONALIZED INSIGHTS REPORT ===")
            print(f"Generated: {summary.report_generated_at}")
            print(f"Theme: {summary.main_theme}")
            print(f"Total Insights: {summary.total_insights}")
            print(f"\nPersonal Message:")
            print(f"'{summary.personal_message}'")
            
            print(f"\n--- INSIGHTS ---")
            for i, insight in enumerate(summary.insights, 1):
                print(f"\n{i}. {insight.title}")
                print(f"   Priority: {insight.priority} | Confidence: {insight.confidence:.1%}")
                print(f"   {insight.content}")
                if insight.actionable_steps:
                    print(f"   Actions: {', '.join(insight.actionable_steps)}")
        else:
            print("No insights available yet. Need more data!")
    
    asyncio.run(test_insights())
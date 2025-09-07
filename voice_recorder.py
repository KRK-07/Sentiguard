import speech_recognition as sr
import threading
import queue
from datetime import datetime
import wave
import io

print("Voice recorder module loaded successfully")

class VoiceRecorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.emotion_queue = queue.Queue()  # For audio emotion data
        self.recognition_thread = None
        self.recording_thread = None
        self.emotion_thread = None  # For audio emotion analysis
        self.initialized = False
        
        # Try to initialize microphone
        try:
            print("🎤 Initializing microphone...")
            self.microphone = sr.Microphone()
            print("🎤 Microphone object created")
            
            # Try to adjust for ambient noise (optional step)
            try:
                print("📊 Adjusting for ambient noise...")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)  # Use integer duration
                print("✅ Ambient noise adjustment completed")
            except Exception as ambient_error:
                print(f"⚠️ Ambient noise adjustment failed: {ambient_error}")
                print("📢 Voice recording will still work, but may be less accurate")
                
            self.initialized = True
            print("✅ Voice recorder initialized successfully")
        except ImportError as e:
            print(f"❌ Missing audio dependencies: {e}")
            print("💡 Try: pip install pyaudio SpeechRecognition")
            self.initialized = False
        except OSError as e:
            print(f"❌ Microphone access error: {e}")
            print("💡 Check microphone permissions in Windows Settings > Privacy > Microphone")
            self.initialized = False
        except Exception as e:
            print(f"❌ Could not initialize microphone: {e}")
            print(f"📝 Error details: {type(e).__name__}: {str(e)}")
            self.initialized = False
    
    def start_recording(self):
        """Start voice recording"""
        if not self.initialized:
            print("❌ Voice recorder not initialized - microphone not available")
            print("💡 Check microphone permissions and try restarting the application")
            return False
            
        if not self.is_recording:
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recognition_thread = threading.Thread(target=self._process_audio)
            self.emotion_thread = threading.Thread(target=self._analyze_audio_emotion)
            self.recording_thread.daemon = True
            self.recognition_thread.daemon = True
            self.emotion_thread.daemon = True
            self.recording_thread.start()
            self.recognition_thread.start()
            self.emotion_thread.start()
            print("🎙️ Voice recording started...")
            return True
        return False
    
    def stop_recording(self):
        """Stop voice recording"""
        self.is_recording = False
        print("⏹️ Stopping voice recording...")
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1)
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=1)
        if self.emotion_thread and self.emotion_thread.is_alive():
            self.emotion_thread.join(timeout=1)
        
        print("✅ Voice recording stopped")
    
    def _record_audio(self):
        """Continuously record audio in chunks"""
        if not self.microphone:
            print("❌ No microphone available for recording")
            return
            
        try:
            with self.microphone as source:
                print("🎯 Listening for voice input...")
                while self.is_recording:
                    try:
                        # Listen for audio with timeout
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        
                        # Put audio in queue for text recognition
                        self.audio_queue.put(audio)
                        
                        # Also put audio in emotion queue for emotion analysis
                        self.emotion_queue.put(audio)
                        
                    except sr.WaitTimeoutError:
                        pass  # Continue listening - this is normal
                    except OSError as e:
                        print(f"❌ Microphone access error: {e}")
                        break
                    except Exception as e:
                        print(f"❌ Recording error: {e}")
                        # Continue recording unless it's a critical error
                        continue
        except Exception as e:
            print(f"❌ Critical recording error: {e}")
            self.is_recording = False
    
    def _process_audio(self):
        """Process recorded audio and convert to text"""
        while self.is_recording or not self.audio_queue.empty():
            try:
                if not self.audio_queue.empty():
                    audio = self.audio_queue.get(timeout=1)
                    # Convert audio to text using Google Speech Recognition
                    text = self.recognizer.recognize_google(audio)  # type: ignore
                    if text.strip():
                        self.text_queue.put(text)
                        print(f"🗣️ Recognized: {text}")
                        # Analyze sentiment and save
                        self._analyze_and_save(text)
            except sr.UnknownValueError:
                # Could not understand audio - this is normal, just continue
                pass
            except sr.RequestError as e:
                print(f"❌ Speech recognition service error: {e}")
                print("💡 Check your internet connection")
            except ConnectionError as e:
                print(f"❌ Network connection error: {e}")
            except queue.Empty:
                pass
            except Exception as e:
                print(f"❌ Audio processing error: {e}")
                # Don't break the loop on unexpected errors
    
    def _analyze_and_save(self, text):
        """Analyze sentiment and save to keystrokes file"""
        try:
            # Import analyzer locally to avoid circular import issues
            from analyzer import analyze_sentiment, THRESHOLD
            
            # Append to keystrokes file for mood tracking
            with open("keystrokes.txt", "a", encoding="utf-8") as f:
                f.write(text + "\n")
            
            # Get sentiment score using enhanced analysis
            score = analyze_sentiment(text)
            timestamp = datetime.now().isoformat()
            
            print(f"Voice sentiment: {score:.3f} ({'NEGATIVE' if score < THRESHOLD else 'POSITIVE'})")
            
        except Exception as e:
            print(f"Analysis error: {e}")
    
    def _analyze_audio_emotion(self):
        """Analyze audio for emotional cues (crying, laughter, etc.)"""
        while self.is_recording or not self.emotion_queue.empty():
            try:
                if not self.emotion_queue.empty():
                    audio = self.emotion_queue.get(timeout=1)
                    
                    # Convert audio to wav bytes for analysis
                    audio_bytes = self._audio_to_wav_bytes(audio)
                    
                    if audio_bytes:
                        # Import audio emotion analyzer locally
                        try:
                            from audio_emotion_analyzer import audio_emotion_analyzer
                            
                            # Extract audio features
                            features = audio_emotion_analyzer.analyze_audio_features(audio_bytes)
                            
                            # Detect emotional cues
                            emotional_cues = audio_emotion_analyzer.detect_emotional_cues(features)
                            
                            # Log significant emotional cues
                            self._log_emotional_cues(emotional_cues)
                            
                        except ImportError:
                            # Fallback if audio emotion analyzer not available
                            pass
                        except Exception as e:
                            print(f"Audio emotion analysis error: {e}")
                            
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Audio emotion processing error: {e}")
    
    def _audio_to_wav_bytes(self, audio_data) -> bytes:
        """Convert AudioData to wav bytes"""
        try:
            # Get raw audio data
            raw_data = audio_data.get_raw_data()
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(audio_data.sample_rate)
                wav_file.writeframes(raw_data)
            
            return wav_buffer.getvalue()
            
        except Exception as e:
            print(f"Error converting audio to wav: {e}")
            return b""
    
    def _log_emotional_cues(self, emotional_cues):
        """Log significant emotional cues detected in voice"""
        try:
            # Check for significant emotional indicators
            high_threshold = 0.7  # Increased from 0.6 to reduce false positives
            medium_threshold = 0.5  # Increased from 0.4 to reduce false positives
            
            detected_emotions = []
            voice_score_modifier = 0.0
            
            # Check each emotional cue
            if emotional_cues['crying_likelihood'] > medium_threshold:
                detected_emotions.append(f"Crying detected ({emotional_cues['crying_likelihood']:.2f})")
                voice_score_modifier -= 0.7  # Strong negative impact
            
            if emotional_cues['laughter_likelihood'] > medium_threshold:
                detected_emotions.append(f"Laughter detected ({emotional_cues['laughter_likelihood']:.2f})")
                voice_score_modifier += 0.5  # Positive impact
            
            if emotional_cues['stress_level'] > high_threshold:
                detected_emotions.append(f"High stress detected ({emotional_cues['stress_level']:.2f})")
                voice_score_modifier -= 0.4
            
            if emotional_cues['anger_level'] > high_threshold:
                detected_emotions.append(f"Anger detected ({emotional_cues['anger_level']:.2f})")
                voice_score_modifier -= 0.5
            
            if emotional_cues['sadness_level'] > high_threshold:
                detected_emotions.append(f"Sadness detected ({emotional_cues['sadness_level']:.2f})")
                voice_score_modifier -= 0.3
            
            if emotional_cues['excitement_level'] > high_threshold:
                detected_emotions.append(f"Excitement detected ({emotional_cues['excitement_level']:.2f})")
                voice_score_modifier += 0.3
            
            if emotional_cues['calmness_level'] > high_threshold:
                detected_emotions.append(f"Calmness detected ({emotional_cues['calmness_level']:.2f})")
                voice_score_modifier += 0.2
            
            # Log detected emotions
            if detected_emotions:
                print(f"🎵 Voice emotions: {', '.join(detected_emotions)}")
                
                # Save emotional context to file for mood tracking
                if abs(voice_score_modifier) > 0.3:  # Only save significant emotional indicators
                    emotion_text = f"[Voice emotion: {', '.join(detected_emotions)}]"
                    with open("keystrokes.txt", "a", encoding="utf-8") as f:
                        f.write(emotion_text + "\n")
                    
                    # Calculate combined voice emotion score
                    overall_score = emotional_cues['voice_emotion_score'] + voice_score_modifier
                    print(f"🎭 Overall voice emotion score: {overall_score:.3f}")
            
        except Exception as e:
            print(f"Error logging emotional cues: {e}")
    
    def get_latest_text(self):
        """Get the latest recognized text"""
        texts = []
        while not self.text_queue.empty():
            try:
                texts.append(self.text_queue.get_nowait())
            except queue.Empty:
                break
        return texts

# Global voice recorder instance
try:
    voice_recorder = VoiceRecorder()
except Exception as e:
    print(f"Failed to create voice recorder: {e}")
    # Create a dummy voice recorder for fallback
    class DummyVoiceRecorder:
        def __init__(self):
            self.is_recording = False
            self.initialized = False
        def start_recording(self):
            print("Voice recording not available")
            return False
        def stop_recording(self):
            pass
        def get_latest_text(self):
            return []
    voice_recorder = DummyVoiceRecorder()

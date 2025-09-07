import numpy as np
import librosa
import io
import wave
import tempfile
import os
from typing import Dict, Tuple

class AudioEmotionAnalyzer:
    """Analyzes audio features to detect emotional states"""
    
    def __init__(self):
        self.sample_rate = 22050
        self.frame_length = 2048
        self.hop_length = 512
        
    def analyze_audio_features(self, audio_data: bytes) -> Dict[str, float]:
        """Extract audio features for emotion analysis"""
        try:
            # Convert audio bytes to numpy array
            audio_array = self._bytes_to_audio_array(audio_data)
            
            if len(audio_array) == 0:
                return self._empty_features()
            
            # Extract various audio features
            features = {}
            
            # 1. Pitch/Fundamental Frequency Analysis
            pitch_features = self._analyze_pitch(audio_array)
            features.update(pitch_features)
            
            # 2. Energy/Intensity Analysis
            energy_features = self._analyze_energy(audio_array)
            features.update(energy_features)
            
            # 3. Spectral Features
            spectral_features = self._analyze_spectral(audio_array)
            features.update(spectral_features)
            
            # 4. Rhythm/Tempo Analysis
            rhythm_features = self._analyze_rhythm(audio_array)
            features.update(rhythm_features)
            
            # 5. Voice Quality Analysis
            voice_features = self._analyze_voice_quality(audio_array)
            features.update(voice_features)
            
            return features
            
        except Exception as e:
            print(f"Error analyzing audio features: {e}")
            return self._empty_features()
    
    def detect_emotional_cues(self, features: Dict[str, float]) -> Dict[str, float]:
        """Detect specific emotional cues from audio features"""
        cues = {
            'crying_likelihood': 0.0,
            'laughter_likelihood': 0.0,
            'stress_level': 0.0,
            'excitement_level': 0.0,
            'sadness_level': 0.0,
            'anger_level': 0.0,
            'calmness_level': 0.0,
            'voice_emotion_score': 0.0  # Overall emotional score from voice
        }
        
        try:
            # Detect crying (low pitch, high energy variations, specific spectral patterns)
            if (features['pitch_mean'] < 150 and 
                features['energy_variance'] > 0.3 and
                features['spectral_centroid_mean'] < 2000):
                cues['crying_likelihood'] = min(0.8, 
                    (0.4 - features['pitch_mean']/400) + 
                    (features['energy_variance'] * 0.5) +
                    (1 - features['spectral_centroid_mean']/3000) * 0.3)
            
            # Detect laughter (rapid pitch changes, high energy, specific patterns)
            if (features['pitch_variance'] > 500 and 
                features['energy_mean'] > 0.6 and
                features['tempo'] > 100):
                cues['laughter_likelihood'] = min(0.9,
                    (features['pitch_variance']/1000) * 0.4 +
                    (features['energy_mean']) * 0.3 +
                    (features['tempo']/200) * 0.3)
            
            # Detect stress (higher pitch, rapid speech, tension)
            if (features['pitch_mean'] > 180 and 
                features['tempo'] > 120 and
                features['spectral_rolloff_mean'] > 3000):
                cues['stress_level'] = min(0.8,
                    (features['pitch_mean']/250) * 0.4 +
                    (features['tempo']/150) * 0.3 +
                    (features['spectral_rolloff_mean']/5000) * 0.3)
            
            # Detect excitement (high energy, varying pitch, fast tempo)
            if (features['energy_mean'] > 0.7 and 
                features['pitch_variance'] > 300 and
                features['tempo'] > 110):
                cues['excitement_level'] = min(0.8,
                    features['energy_mean'] * 0.4 +
                    (features['pitch_variance']/600) * 0.3 +
                    (features['tempo']/160) * 0.3)
            
            # Detect sadness (very low energy, very low pitch, very slow tempo)
            # Made criteria stricter to reduce false positives
            if (features['energy_mean'] < 0.25 and 
                features['pitch_mean'] < 120 and
                features['tempo'] < 60 and
                features['zero_crossing_rate'] < 0.05):
                cues['sadness_level'] = min(0.8,
                    (1 - features['energy_mean']) * 0.3 +
                    (1 - features['pitch_mean']/200) * 0.25 +
                    (1 - features['tempo']/120) * 0.25 +
                    (1 - features['zero_crossing_rate']) * 0.2)
            
            # Detect anger (high energy, high pitch, harsh spectral content)
            if (features['energy_mean'] > 0.6 and 
                features['pitch_mean'] > 170 and
                features['spectral_bandwidth_mean'] > 1500):
                cues['anger_level'] = min(0.8,
                    features['energy_mean'] * 0.4 +
                    (features['pitch_mean']/250) * 0.3 +
                    (features['spectral_bandwidth_mean']/2500) * 0.3)
            
            # Detect calmness (moderate energy, stable pitch, moderate tempo)
            # Made more sensitive to detect normal speech as calm
            if (0.2 < features['energy_mean'] < 0.7 and 
                features['pitch_variance'] < 300 and
                50 < features['tempo'] < 120):
                cues['calmness_level'] = min(0.8,
                    (0.7 - abs(features['energy_mean'] - 0.45)) * 0.4 +
                    (1 - features['pitch_variance']/400) * 0.3 +
                    (0.8 if 70 < features['tempo'] < 110 else 0.5) * 0.3)
            
            # Calculate overall voice emotion score
            # Negative emotions contribute negatively, positive emotions positively
            negative_emotions = (cues['crying_likelihood'] + cues['stress_level'] + 
                               cues['sadness_level'] + cues['anger_level']) / 4
            positive_emotions = (cues['laughter_likelihood'] + cues['excitement_level'] + 
                               cues['calmness_level']) / 3
            
            cues['voice_emotion_score'] = positive_emotions - negative_emotions
            
            return cues
            
        except Exception as e:
            print(f"Error detecting emotional cues: {e}")
            return cues
    
    def _bytes_to_audio_array(self, audio_data: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        try:
            # Create a temporary file to save the audio data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                temp_filename = temp_file.name
                
            # Load audio using librosa (outside the with block)
            audio_array, sr = librosa.load(temp_filename, sr=self.sample_rate)
            
            # Clean up temp file with retry mechanism for Windows
            try:
                os.unlink(temp_filename)
            except (OSError, PermissionError) as e:
                # If file is locked, try again after a short delay
                import time
                time.sleep(0.1)
                try:
                    os.unlink(temp_filename)
                except (OSError, PermissionError):
                    # If still locked, let Windows clean it up later
                    print(f"Warning: Could not delete temp file {temp_filename} (will be cleaned up by system)")
                    pass
                
            return audio_array
                
        except Exception as e:
            print(f"Error converting audio bytes: {e}")
            return np.array([])
    
    def _analyze_pitch(self, audio: np.ndarray) -> Dict[str, float]:
        """Analyze pitch characteristics"""
        try:
            # Extract pitch using librosa
            pitches, magnitudes = librosa.piptrack(y=audio, sr=self.sample_rate)
            
            # Get the most prominent pitch at each time frame
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Valid pitch
                    pitch_values.append(pitch)
            
            if len(pitch_values) == 0:
                return {'pitch_mean': 0, 'pitch_variance': 0, 'pitch_range': 0}
            
            pitch_array = np.array(pitch_values)
            return {
                'pitch_mean': float(np.mean(pitch_array)),
                'pitch_variance': float(np.var(pitch_array)),
                'pitch_range': float(np.max(pitch_array) - np.min(pitch_array))
            }
        except:
            return {'pitch_mean': 0, 'pitch_variance': 0, 'pitch_range': 0}
    
    def _analyze_energy(self, audio: np.ndarray) -> Dict[str, float]:
        """Analyze energy/intensity characteristics"""
        try:
            # RMS energy
            rms = librosa.feature.rms(y=audio, frame_length=self.frame_length, 
                                    hop_length=self.hop_length)[0]
            
            return {
                'energy_mean': float(np.mean(rms)),
                'energy_variance': float(np.var(rms)),
                'energy_max': float(np.max(rms))
            }
        except:
            return {'energy_mean': 0, 'energy_variance': 0, 'energy_max': 0}
    
    def _analyze_spectral(self, audio: np.ndarray) -> Dict[str, float]:
        """Analyze spectral characteristics"""
        try:
            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)[0]
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.sample_rate)[0]
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate)[0]
            
            return {
                'spectral_centroid_mean': float(np.mean(spectral_centroids)),
                'spectral_bandwidth_mean': float(np.mean(spectral_bandwidth)),
                'spectral_rolloff_mean': float(np.mean(spectral_rolloff))
            }
        except:
            return {'spectral_centroid_mean': 0, 'spectral_bandwidth_mean': 0, 'spectral_rolloff_mean': 0}
    
    def _analyze_rhythm(self, audio: np.ndarray) -> Dict[str, float]:
        """Analyze rhythm/tempo characteristics"""
        try:
            # Tempo estimation
            tempo, _ = librosa.beat.beat_track(y=audio, sr=self.sample_rate)
            
            return {
                'tempo': float(tempo)
            }
        except:
            return {'tempo': 0}
    
    def _analyze_voice_quality(self, audio: np.ndarray) -> Dict[str, float]:
        """Analyze voice quality characteristics"""
        try:
            # Zero crossing rate (indicates voice quality/breathiness)
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            
            # MFCCs (voice timbre characteristics)
            mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=13)
            
            return {
                'zero_crossing_rate': float(np.mean(zcr)),
                'mfcc_mean': float(np.mean(mfccs)),
                'mfcc_variance': float(np.var(mfccs))
            }
        except:
            return {'zero_crossing_rate': 0, 'mfcc_mean': 0, 'mfcc_variance': 0}
    
    def _empty_features(self) -> Dict[str, float]:
        """Return empty feature dictionary"""
        return {
            'pitch_mean': 0, 'pitch_variance': 0, 'pitch_range': 0,
            'energy_mean': 0, 'energy_variance': 0, 'energy_max': 0,
            'spectral_centroid_mean': 0, 'spectral_bandwidth_mean': 0, 'spectral_rolloff_mean': 0,
            'tempo': 0,
            'zero_crossing_rate': 0, 'mfcc_mean': 0, 'mfcc_variance': 0
        }

# Global audio emotion analyzer instance
audio_emotion_analyzer = AudioEmotionAnalyzer()

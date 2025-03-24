"""
Voice Command Module
Provides speech recognition and text-to-speech capabilities
"""
import os
import platform
import threading
import queue
import logging
from typing import Callable, Dict, List, Optional, Any

# Setup logging
logger = logging.getLogger(__name__)

class VoiceCommandHandler:
    """Handles voice command recognition and text-to-speech output"""
    
    def __init__(self, config: Dict = None):
        """Initialize voice command handler with configuration"""
        self.config = config or {}
        self.is_listening = False
        self.command_queue = queue.Queue()
        self.listener_thread = None
        self.speech_language = self.config.get('voice_recognition_language', 'en-US')
        self.tts_engine = None
        self.recognizer = None
        self.microphone = None
        self._setup_dependencies()
    
    def _setup_dependencies(self) -> None:
        """Import and set up speech recognition and TTS dependencies"""
        try:
            # Only import these packages if voice commands are enabled
            import speech_recognition as sr
            import pyttsx3
            
            # Set up speech recognition
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            
            # Set up text-to-speech
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS voice properties based on system
            voices = self.tts_engine.getProperty('voices')
            self.tts_engine.setProperty('rate', 150)  # Speed of speech
            
            # Try to set a more natural voice if available
            if voices:
                for voice in voices:
                    # Prefer female voice for better clarity
                    if "female" in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                    
            logger.info("Voice command system initialized successfully")
            return True
        except ImportError as e:
            logger.warning(f"Voice command dependencies not available: {str(e)}")
            logger.info("Install required packages with: pip install SpeechRecognition pyttsx3 pyaudio")
            return False
        except Exception as e:
            logger.error(f"Error setting up voice command system: {str(e)}")
            return False
    
    def start_listening(self, command_callback: Callable[[str], None]) -> bool:
        """Start listening for voice commands in background"""
        if not self.recognizer or not self.microphone:
            logger.error("Speech recognition components not available")
            return False
        
        if self.is_listening:
            logger.warning("Already listening for voice commands")
            return True
            
        def listen_worker():
            import speech_recognition as sr
            logger.info("Voice command listener started")
            self.is_listening = True
            
            while self.is_listening:
                try:
                    with self.microphone as source:
                        logger.debug("Listening for command...")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    try:
                        text = self.recognizer.recognize_google(audio, language=self.speech_language)
                        logger.info(f"Recognized: {text}")
                        command_callback(text)
                    except sr.UnknownValueError:
                        logger.debug("Could not understand audio")
                    except sr.RequestError as e:
                        logger.error(f"Could not request results: {e}")
                except Exception as e:
                    logger.error(f"Error in voice recognition: {e}")
                    if not self.is_listening:
                        break
        
        self.listener_thread = threading.Thread(target=listen_worker)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        return True
    
    def stop_listening(self) -> None:
        """Stop listening for voice commands"""
        self.is_listening = False
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2)
            logger.info("Voice command listener stopped")
    
    def speak(self, text: str) -> None:
        """Convert text to speech"""
        if not self.tts_engine:
            logger.error("Text-to-speech engine not available")
            return
            
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
    
    def is_available(self) -> bool:
        """Check if voice command functionality is available"""
        return self.recognizer is not None and self.tts_engine is not None 
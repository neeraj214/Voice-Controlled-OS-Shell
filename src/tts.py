"""
Text-to-speech conversion module.

This module handles the conversion of text responses to speech
using the pyttsx3 library for offline text-to-speech synthesis.
TTS can be globally enabled/disabled via initialization.
"""

import pyttsx3
from typing import Optional

class TextToSpeech:
    def __init__(self, enabled: bool = True, rate: Optional[int] = None, volume: Optional[float] = None):
        """
        Initialize the TTS engine.
        
        Args:
            enabled: Whether TTS should be enabled
        """
        self.enabled = enabled
        self.engine = None
        
        if enabled:
            try:
                self.engine = pyttsx3.init()
                # Set properties (allow overrides)
                default_rate = 150 if rate is None else rate
                default_volume = 0.9 if volume is None else volume
                self.engine.setProperty('rate', default_rate)    # Speaking rate
                self.engine.setProperty('volume', default_volume)  # Volume (0.0 to 1.0)
                
                # Try to set a female voice if available
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if 'female' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            except Exception as e:
                print(f"Warning: Could not initialize TTS engine: {str(e)}")
                print("TTS feedback will be disabled.")
                self.engine = None

    def say(self, text: str) -> None:
        """
        Convert text to speech if TTS is enabled.
        
        Args:
            text: The text to be spoken
        """
        # Print the text regardless of TTS state
        print(text)
        
        # Only attempt speech if TTS is enabled and engine is initialized
        if self.enabled and self.engine is not None:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {str(e)}")

    def cleanup(self) -> None:
        """Clean up TTS engine resources."""
        if self.engine is not None:
            try:
                self.engine.stop()
            except:
                pass
"""
Speech-to-text conversion module.

This module handles the conversion of spoken commands to text using
the SpeechRecognition library with Google's speech recognition service.
It also provides a fallback text input mode for environments where
speech recognition is not available or not desired.
"""

import speech_recognition as sr
from typing import Optional


class SpeechToText:
    def __init__(self, text_mode: bool = False):
        """
        Initialize the speech recognizer and microphone.
        
        Args:
            text_mode: Whether to force text input mode
        """
        self.text_mode = text_mode
        self.recognizer = sr.Recognizer()
        
        if not text_mode:
            try:
                self.microphone = sr.Microphone()
                # Adjust for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except (OSError, sr.RequestError) as e:
                print(f"Warning: Could not initialize microphone: {str(e)}")
                print("Falling back to text input mode.")
                self.microphone = None
                self.text_mode = True
        else:
            self.microphone = None

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 6) -> str:
        """
        Listen for a single voice command and convert it to text.
        
        Args:
            timeout: Maximum seconds to wait for speech to start
            phrase_time_limit: Maximum seconds to capture speech
            
        Returns:
            Recognized text or empty string if recognition fails
        """
        if self.text_mode or not self.microphone:
            return self.read_text_input()
            
        try:
            with self.microphone as source:
                print("\nListening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
            print("Processing...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("No speech detected. Please try again.")
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
        except sr.RequestError as e:
            print(f"Could not request results; {str(e)}")
            print("Switching to text input mode.")
            return self.read_text_input()
        except Exception as e:
            print(f"Error: {str(e)}")
        
        return ""

    def read_text_input(self) -> str:
        """
        Read command from keyboard input as a fallback method.
        
        Returns:
            The entered text command in lowercase
        """
        try:
            text = input("\nEnter command: ").strip()
            return text.lower()
        except (KeyboardInterrupt, EOFError):
            return ""
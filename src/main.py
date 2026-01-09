"""
Voice Shell main module.

This module provides the entry point and main loop for the voice-controlled shell.
It handles command-line arguments, initializes components, and manages the interaction
loop with state machine for confirmations.
"""

import argparse
import os
import platform
import threading
import speech_recognition as sr
from pathlib import Path
from typing import Dict, Any, Optional

# Try to import winsound for Windows beep
try:
    import winsound
    HAVE_WINSOUND = True
except ImportError:
    HAVE_WINSOUND = False

from . import stt
from . import tts
from . import parser
from . import commands
from . import executor
from . import state
from . import logging_util
from . import ui

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Voice-controlled shell")
    parser.add_argument(
        "--text",
        action="store_true",
        help="Use keyboard input instead of microphone"
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Disable text-to-speech output"
    )
    parser.add_argument(
        "--sandbox",
        type=str,
        default="sandbox",
        help="Path to sandbox directory (default: ./sandbox)"
    )
    parser.add_argument(
        "--no-beep",
        action="store_true",
        help="Disable beep sound before listening"
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch with graphical user interface"
    )
    # Adjustable speed controls
    parser.add_argument(
        "--listen-timeout",
        type=int,
        default=int(os.getenv("VOICE_LISTEN_TIMEOUT", "5")),
        help="Seconds to wait for speech start (default: 5)"
    )
    parser.add_argument(
        "--phrase-limit",
        type=int,
        default=int(os.getenv("VOICE_PHRASE_LIMIT", "6")),
        help="Max seconds to capture speech (default: 6)"
    )
    parser.add_argument(
        "--tts-rate",
        type=int,
        default=int(os.getenv("VOICE_TTS_RATE", "150")),
        help="TTS speaking rate (default: 150)"
    )
    return parser.parse_args()

def print_banner():
    """Print welcome banner."""
    banner = [
        "╔══════════════════════════════════════╗",
        "║          Voice Shell v1.0            ║",
        "║    Voice/Text controlled sandbox     ║",
        "╚══════════════════════════════════════╝"
    ]
    print("\n".join(banner))
    print("\nSay 'help' for available commands\n")

def play_beep():
    """Play a short beep sound if available."""
    if HAVE_WINSOUND:
        try:
            winsound.Beep(1000, 100)  # 1000Hz for 100ms
        except:
            pass  # Ignore any beep failures

class ShellStateMachine:
    """Manages shell state and confirmation flows."""
    
    def __init__(self, shell_ui=None):
        """Initialize state machine."""
        self.state = "READY"
        self.pending_payload: Optional[Dict[str, Any]] = None
        self.ui = shell_ui
    
    def handle_delete_confirmation(self, text: str, shell_state) -> bool:
        """
        Handle yes/no confirmation for delete commands.
        
        Args:
            text: User input text
            shell_state: Current shell state for executor
            
        Returns:
            True if confirmation was handled, False otherwise
        """
        if self.state != "AWAIT_CONFIRM_DELETE" or not self.pending_payload:
            return False
            
        # Reset state before handling to prevent loops
        payload = self.pending_payload
        self.state = "READY"
        self.pending_payload = None
        
        # Check confirmation response
        if text.lower().strip() in ["yes", "y"]:
            kind = payload["kind"]
            name = payload["name"]
            try:
                executor.delete(shell_state, kind, name)
                outcome = f"Successfully deleted {kind} '{name}'"
                print(f"\n✅ {outcome}")
                if self.ui:
                    self.ui.update_outcome(f"✅ {outcome}")
                    self.ui.add_to_history(outcome)
                logging_util.log_event(text, "DELETE_CONFIRM", outcome)
            except Exception as e:
                outcome = f"Error deleting {kind} '{name}': {str(e)}"
                print(f"\n❌ {outcome}")
                if self.ui:
                    self.ui.update_outcome(f"❌ {outcome}")
                    self.ui.add_to_history(outcome)
                logging_util.log_event(text, "DELETE_CONFIRM", outcome)
                raise
            return True
        else:
            outcome = f"Delete {payload['kind']} '{payload['name']}' cancelled."
            print(f"\n❌ {outcome}")
            if self.ui:
                self.ui.update_outcome(f"❌ {outcome}")
                self.ui.add_to_history(outcome)
            logging_util.log_event(text, "DELETE_CANCEL", outcome)
            return True
            
        return False
    
    def set_delete_confirmation(self, payload: Dict[str, Any]):
        """Set state for delete confirmation."""
        self.state = "AWAIT_CONFIRM_DELETE"
        self.pending_payload = payload
        prompt = f"\nConfirm delete {payload['kind']} '{payload['name']}'? Say yes/no"
        print(prompt)
        if self.ui:
            self.ui.update_outcome(prompt)
            self.ui.add_to_history(prompt)
        logging_util.log_event(
            f"Request delete {payload['kind']} '{payload['name']}'",
            "DELETE_REQUEST",
            "Awaiting confirmation"
        )

class VoiceShell:
    """Main shell class that handles the interaction loop."""
    
    def __init__(self, args):
        """Initialize shell components."""
        self.args = args
        self.running = True
        self.listening_thread_active = False
        self.stop_requested = False
        self.listen_stop_event = threading.Event()
        
        # Initialize text-to-speech
        self.tts_engine = tts.TextToSpeech(enabled=not args.no_tts, rate=args.tts_rate)
        
        # Initialize speech-to-text
        self.speech = stt.SpeechToText(text_mode=args.text)
        
        # Initialize command parser
        self.cmd_parser = parser.CommandParser()
        
        # Initialize shell state with sandbox
        sandbox_path = Path(args.sandbox).resolve()
        self.shell_state = state.ShellState(sandbox_path)
        
        # Initialize UI if requested
        self.ui = None
        if args.ui:
            self.ui = ui.VoiceShellUI(
                start_listening_callback=self.handle_listen_request,
                stop_listening_callback=self.handle_stop_listening,
                exit_callback=self.handle_exit_request,
                submit_text_callback=self.handle_text_input
            )
        
        # Initialize state machine
        self.state_machine = ShellStateMachine(self.ui)
    
    def say(self, text: str):
        """Wrapper for TTS."""
        self.tts_engine.say(text)
    
    def handle_listen_request(self):
        """Handle one-shot listening request from UI."""
        if self.args.text:
            print("[handle_listen_request] Text mode active, ignoring voice listen.")
            return
        if self.listening_thread_active:
            print("[handle_listen_request] Already listening, ignoring duplicate request.")
            return
        print("[handle_listen_request] Starting listen thread...")
        self.listening_thread_active = True
        self.stop_requested = False
        self.listen_stop_event.clear()
        if self.ui:
            self.ui.set_listening(True)
        threading.Thread(target=self.process_voice_input, daemon=True).start()

    def handle_stop_listening(self):
        """Signal to stop current listening attempt."""
        print("[handle_stop_listening] Stop requested.")
        self.stop_requested = True
        self.listen_stop_event.set()
    
    def handle_text_input(self, text: str):
        """Handle text input from UI."""
        self.process_command(text)
    
    def handle_exit_request(self):
        """Handle exit request from UI."""
        self.running = False
        if self.ui:
            self.ui.root.quit()
    
    def process_voice_input(self):
        """Process a single voice input."""
        print("[process_voice_input] Thread started.")
        if not self.args.text and not self.args.no_beep:
            play_beep()
        
        # Check for stop request before listening
        if self.listen_stop_event.is_set():
            print("[process_voice_input] Cancelled before listening.")
            self.stop_requested = False
            self.listening_thread_active = False
            self.listen_stop_event.clear()
            if self.ui:
                self.ui.set_listening(False)
                self.ui.update_outcome("❌ Listening cancelled")
            return
        
        try:
            with self.speech.microphone as source:
                print("\nListening... (click Stop to cancel)")
                audio = self.speech.recognizer.listen(
                    source,
                    timeout=1,  # Short timeout for frequent stop checks
                    phrase_time_limit=self.args.phrase_limit
                )
        except sr.WaitTimeoutError:
            if self.listen_stop_event.is_set():
                # User pressed Stop
                print("[process_voice_input] Cancelled by stop event (timeout).")
                self.stop_requested = False
                self.listening_thread_active = False
                self.listen_stop_event.clear()
                if self.ui:
                    self.ui.set_listening(False)
                    self.ui.update_outcome("❌ Listening cancelled")
                return
            print("No speech detected. Please try again.")
            self.listening_thread_active = False
            if self.ui:
                self.ui.set_listening(False)
            return
        except Exception as e:
            print(f"Listen error: {str(e)}")
            self.listening_thread_active = False
            if self.ui:
                self.ui.set_listening(False)
            return

        if self.listen_stop_event.is_set():
            # Stop requested after audio captured
            print("[process_voice_input] Cancelled by stop event (after audio).")
            self.stop_requested = False
            self.listening_thread_active = False
            self.listen_stop_event.clear()
            if self.ui:
                self.ui.set_listening(False)
                self.ui.update_outcome("❌ Listening cancelled")
            return

        print("Processing...")
        try:
            text = self.speech.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            self.process_command(text.lower())
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
            if self.ui:
                self.ui.update_outcome("❌ Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results; {str(e)}")
            if self.ui:
                self.ui.update_outcome(f"❌ Request error: {str(e)}")
        except Exception as e:
            print(f"Error: {str(e)}")
            if self.ui:
                self.ui.update_outcome(f"❌ Error: {str(e)}")
        finally:
            self.listening_thread_active = False
            if self.ui:
                self.ui.set_listening(False)
            print("[process_voice_input] Thread finished.")
    
    def process_command(self, text: str):
        """Process a single command."""
        try:
            print(f"[process_command] Received: {text}")
            # Update UI with command
            if self.ui:
                self.ui.update_command(text)
                self.ui.add_to_history(f"Command: {text}")
            
            # Check for pending confirmations first
            if self.state_machine.handle_delete_confirmation(text, self.shell_state):
                return
            
            # Parse and handle command
            intent = self.cmd_parser.parse(text)
            try:
                result = commands.handle(intent, self.shell_state, self.say)
                
                # Update UI with current directory
                if self.ui:
                    self.ui.update_directory(str(self.shell_state.cwd))
                
                # Log successful command
                if intent["type"] != "UNKNOWN":
                    outcome = "Success" if not result else (
                        "Exit requested" if result[0] == "EXIT" else
                        "Delete confirmation requested"
                    )
                    if self.ui:
                        self.ui.update_outcome(f"✅ {outcome}")
                        self.ui.add_to_history(outcome)
                    logging_util.log_event(text, intent["type"], outcome)
                else:
                    if self.ui:
                        self.ui.update_outcome("❌ Command not recognized")
                        self.ui.add_to_history("Command not recognized")
                    logging_util.log_event(text, "UNKNOWN", "Command not recognized")
                
                # Handle special states
                if result:
                    state_token, payload = result
                    
                    if state_token == 'EXIT':
                        self.handle_exit_request()
                        return
                        
                    elif state_token == 'AWAIT_CONFIRM_DELETE':
                        self.state_machine.set_delete_confirmation(payload)
                        
            except Exception as e:
                # Log command error
                error_msg = str(e)
                print(f"\n❌ Error: {error_msg}")
                self.say("Sorry, there was an error")
                if self.ui:
                    self.ui.update_outcome(f"❌ Error: {error_msg}")
                    self.ui.add_to_history(f"Error: {error_msg}")
                logging_util.log_event(text, intent["type"], f"Error: {error_msg}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ An unexpected error occurred: {error_msg}")
            self.say("Sorry, something went wrong")
            if self.ui:
                self.ui.update_outcome(f"❌ System error: {error_msg}")
                self.ui.add_to_history(f"System error: {error_msg}")
            logging_util.log_event("ERROR", "SYSTEM", error_msg)
        finally:
            print("[process_command] Finished processing.")
    
    def run(self):
        """Main run loop."""
        # Show welcome banner
        print_banner()
        
        # Log startup
        logging_util.log_event(
            "Shell started",
            "STARTUP",
            f"Mode: {'text' if self.args.text else 'voice'}, "
            f"TTS: {'disabled' if self.args.no_tts else 'enabled'}, "
            f"UI: {'enabled' if self.args.ui else 'disabled'}"
        )
        
        if self.ui:
            # Update initial state
            self.ui.update_directory(str(self.shell_state.cwd))
            self.ui.update_command("No commands yet")
            self.ui.update_outcome("Ready")
            self.ui.add_to_history("Voice Shell started")
            # Show mode in status bar
            mode_text = (
                f"Mode: {'Text' if self.args.text else 'Voice'} | "
                f"TTS: {'Off' if self.args.no_tts else 'On'} | "
                f"Listen: {self.args.listen_timeout}s | Phrase: {self.args.phrase_limit}s | "
                f"Rate: {self.args.tts_rate}"
            )
            self.ui.set_mode_status(mode_text)
            
            # Run UI main loop
            self.ui.run()
        else:
            # Main interaction loop without UI
            while self.running:
                try:
                    if not self.args.text and not self.args.no_beep:
                        play_beep()
                    
                    # Get input (voice or text)
                    text = self.speech.listen_once() if not self.args.text else self.speech.read_text_input()
                    if text:
                        self.process_command(text)
                    
                except KeyboardInterrupt:
                    print("\n⚠️ Use 'exit' command to quit.")
                    logging_util.log_event("KeyboardInterrupt", "INTERRUPT", "Advised to use exit command")
                    continue
        
        # Log shutdown and cleanup
        logging_util.log_event("Shell stopped", "SHUTDOWN", "Clean exit")
        self.tts_engine.cleanup()
        print("\n👋 Goodbye!")

def main():
    """Main entry point."""
    args = parse_args()
    shell = VoiceShell(args)
    shell.run()

if __name__ == "__main__":
    main()
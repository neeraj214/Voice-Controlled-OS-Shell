import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable
import queue
import threading

class VoiceShellUI:
    def __init__(self, start_listening_callback: Callable, 
                 stop_listening_callback: Callable,
                 exit_callback: Callable,
                 submit_text_callback: Callable):
        self.root = tk.Tk()
        self.root.title("Voice Shell")
        self.root.geometry("600x400")
        
        # Callbacks
        self.start_listening = start_listening_callback
        self.stop_listening = stop_listening_callback
        self.exit_callback = exit_callback
        self.submit_text = submit_text_callback
        
        # Message queue for thread-safe UI updates
        self.msg_queue = queue.Queue()
        
        self._create_widgets()
        self._setup_layout()
        
        # Start message processing
        self.root.after(100, self._process_messages)
        # Initialize button states
        self.set_listening(False)
    
    def _create_widgets(self):
        # Current directory frame
        self.dir_frame = ttk.LabelFrame(self.root, text="Current Directory")
        self.dir_label = ttk.Label(self.dir_frame, text="", wraplength=550)
        
        # Last command frame
        self.cmd_frame = ttk.LabelFrame(self.root, text="Last Command")
        self.cmd_label = ttk.Label(self.cmd_frame, text="", wraplength=550)
        
        # Last outcome frame
        self.outcome_frame = ttk.LabelFrame(self.root, text="Last Outcome")
        self.outcome_label = ttk.Label(self.outcome_frame, text="", wraplength=550)
        
        # History pane
        self.history_frame = ttk.LabelFrame(self.root, text="History")
        self.history_text = scrolledtext.ScrolledText(
            self.history_frame, wrap=tk.WORD, height=10)
        self.history_text.config(state=tk.DISABLED)
        
        # Control frame
        self.control_frame = ttk.Frame(self.root)
        
        # Text input
        self.input_frame = ttk.Frame(self.control_frame)
        self.input_entry = ttk.Entry(self.input_frame, width=40)
        self.input_entry.bind('<Return>', lambda e: self._on_submit())
        self.submit_btn = ttk.Button(
            self.input_frame, text="Submit", command=self._on_submit)
        
        # Action buttons
        self.listen_btn = ttk.Button(
            self.control_frame, text="Start Listening", command=self.start_listening)
        self.stop_btn = ttk.Button(
            self.control_frame, text="Stop Listening", command=self.stop_listening)
        self.exit_btn = ttk.Button(
            self.control_frame, text="Exit", command=self.exit_callback)

        # Status bar
        self.status_frame = ttk.Frame(self.root)
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        # Remove progress bar to avoid confusion
        # self.progress = ttk.Progressbar(self.status_frame, mode="indeterminate", length=120)
    
    def _setup_layout(self):
        # Pack main sections
        self.dir_frame.pack(fill=tk.X, padx=5, pady=2)
        self.dir_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.cmd_frame.pack(fill=tk.X, padx=5, pady=2)
        self.cmd_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.outcome_frame.pack(fill=tk.X, padx=5, pady=2)
        self.outcome_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Pack control elements
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.submit_btn.pack(side=tk.LEFT)
        
        self.listen_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.exit_btn.pack(side=tk.LEFT)

        # Status bar layout
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label.pack(side=tk.LEFT)
        # self.progress.pack(side=tk.RIGHT)  # removed
    
    def _on_submit(self):
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, tk.END)
            self.submit_text(text)
    
    def _process_messages(self):
        """Process messages from the queue and update UI"""
        try:
            while True:
                msg_type, msg = self.msg_queue.get_nowait()
                if msg_type == "dir":
                    self.dir_label.config(text=msg)
                elif msg_type == "cmd":
                    self.cmd_label.config(text=msg)
                elif msg_type == "outcome":
                    self.outcome_label.config(text=msg)
                elif msg_type == "history":
                    self.history_text.config(state=tk.NORMAL)
                    self.history_text.insert(tk.END, msg + "\n")
                    self.history_text.see(tk.END)
                    self.history_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(100, self._process_messages)
    
    def update_directory(self, directory: str):
        """Update current directory display"""
        self.msg_queue.put(("dir", directory))
    
    def update_command(self, command: str):
        """Update last command display"""
        self.msg_queue.put(("cmd", command))
    
    def update_outcome(self, outcome: str):
        """Update last outcome display"""
        self.msg_queue.put(("outcome", outcome))
    
    def add_to_history(self, text: str):
        """Add a new entry to history"""
        self.msg_queue.put(("history", text))

    def set_mode_status(self, text: str):
        """Update status label with mode/config"""
        self.status_label.config(text=text)

    def set_listening(self, listening: bool):
        """Update button states when listening starts/stops"""
        if listening:
            self.listen_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Listening... click Stop to cancel")
        else:
            self.listen_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Ready")

    def set_busy(self, busy: bool):
        """No-op to avoid progress bar issues"""
        pass

    def clear_history(self):
        """Clear history text area"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        self.history_text.config(state=tk.DISABLED)
    
    def run(self):
        """Start the UI main loop"""
        self.root.mainloop()
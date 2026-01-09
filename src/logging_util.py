"""
Logging utility for voice shell interactions.
Logs commands and their outcomes to a CSV file.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

def log_event(text: str, intent_type: str, outcome: str, timestamp: Optional[datetime] = None) -> None:
    """
    Log a voice shell interaction event to the CSV file.
    
    Args:
        text: The raw input text from the user
        intent_type: The type of intent parsed from the text
        outcome: The result of handling the command (success/error message)
        timestamp: Optional timestamp for the event (defaults to current time)
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Ensure the log file exists with headers
    log_file = Path("logs.csv")
    if not log_file.exists():
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'text', 'intent_type', 'outcome'])
    
    # Append the new log entry
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            text,
            intent_type,
            outcome
        ])
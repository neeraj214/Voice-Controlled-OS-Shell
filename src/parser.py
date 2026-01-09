"""
Command parser module.

This module handles the parsing of voice/text commands into structured intent
dictionaries that can be executed by the shell. It uses regular expressions
to match command patterns flexibly, allowing for natural language variations.
"""

import re
from typing import Dict, Any, List

class CommandParser:
    def __init__(self):
        """Initialize command patterns and whitelisted applications."""
        # Whitelisted applications that can be opened
        self.ALLOWED_APPS = {
            'calculator': 'calc',
            'calc': 'calc',
            'notepad': 'notepad',
            'paint': 'mspaint',
            'browser': 'explorer',
            'explorer': 'explorer'
        }

        # Command patterns with named capture groups
        self.patterns = [
            # Help command
            (r'^\s*(?:please\s+)?(?:show\s+)?(?:help|what\s+can\s+you\s+do|show\s+available\s+commands)\s*$',
             self._handle_help),
            
            # Exit commands
            (r'^\s*(?:please\s+)?(?:exit|quit|goodbye|bye)\s*$',
             self._handle_exit),
            
            # List files
            (r'^\s*(?:please\s+)?(?:show|list)(?:\s+all)?\s+(?:files?|contents?)|(?:show\s+me\s+the\s+contents?|what\s+files?\s+are\s+here)\s*$',
             self._handle_list),
            
            # Create folder
            (r'^\s*(?:please\s+)?(?:create|make)(?:\s+a)?(?:\s+new)?\s+(?:folder|directory)(?:\s+called)?\s+(?P<name>[\w\-. ]+)\s*$',
             self._handle_mkdir),
            
            # Create file
            (r'^\s*(?:please\s+)?(?:create|make)(?:\s+a)?(?:\s+new)?\s+file(?:\s+called)?\s+(?P<name>[\w\-. ]+)\s*$',
             self._handle_mkfile),
            
            # Delete file/folder
            (r'^\s*(?:please\s+)?(?:delete|remove)\s+(?:the\s+)?(?P<kind>file|folder|directory)\s+(?:called\s+)?(?P<name>[\w\-. ]+)\s*$',
             self._handle_delete),
            
            # Change directory (multiple forms)
            (r'^\s*(?:please\s+)?(?:change\s+directory\s+to|cd\s+to|go\s+to|move\s+to|switch\s+to\s+directory)(?:\s+folder)?\s+(?P<path>[\w\-. /\\]+)\s*$',
             self._handle_cd),
            # Go back / up one directory
            (r'^\s*(?:please\s+)?(?:go\s+back|go\s+up|back)\s*$', self._handle_back),
            
            # Print working directory
            (r'^\s*(?:please\s+)?(?:where\s+am\s+i|show\s+(?:current\s+)?(?:working\s+)?directory|what\s+folder\s+am\s+i\s+in|current\s+location|could\s+you\s+show\s+me\s+where\s+i\s+am)\s*$',
             self._handle_pwd),
            
            # Open application
            (r'^\s*(?:please\s+|would\s+you\s+kindly\s+)?(?:open|launch|start)(?:\s+the)?\s+(?P<app>calculator|calc|notepad|paint|browser|explorer)\s*$',
             self._handle_open_app),
            # Generic open file/folder by path or name
            (r'^\s*(?:please\s+)?open\s+(?P<name>[\w\-. /\\]+)\s*$', self._handle_open_file),
            # Search files/folders
            (r'^\s*(?:please\s+)?(?:search|find|look\s+for)\s+(?P<query>[\w\-. ]+)\s*$', self._handle_search),
            # Rename file/folder
            (r'^\s*(?:please\s+)?rename\s+(?P<old>[\w\-. ]+)\s+(?:to|as)\s+(?P<new>[\w\-. ]+)\s*$', self._handle_rename),
            # Show history with optional count
            (r'^\s*(?:please\s+)?history(?:\s+(?P<count>\d+))?\s*$', self._handle_history),
            # Copy file/folder
            (r'^\s*(?:please\s+)?copy\s+(?P<src>[\w\-. /\\]+)\s+(?:to|into)\s+(?P<dst>[\w\-. /\\]+)\s*$', self._handle_copy),
            # Move file/folder
            (r'^\s*(?:please\s+)?move\s+(?P<src>[\w\-. /\\]+)\s+(?:to|into)\s+(?P<dst>[\w\-. /\\]+)\s*$', self._handle_move),
            # Read file
            (r'^\s*(?:please\s+)?(?:read|show|display)\s+file\s+(?P<name>[\w\-. /\\]+)\s*$', self._handle_read),
            # Append to file (double quotes)
            (r'^\s*(?:please\s+)?(?:append|write)\s+"(?P<text>.+?)"\s+(?:to|into)\s+file\s+(?P<name>[\w\-. /\\]+)\s*$', self._handle_append),
            # Append to file (single quotes)
            (r"^\s*(?:please\s+)?(?:append|write)\s+'(?P<text>.+?)'\s+(?:to|into)\s+file\s+(?P<name>[\w\-. /\\]+)\s*$", self._handle_append),
            # Grep/search in files (double quotes)
            (r'^\s*(?:please\s+)?(?:grep|find\s+in\s+files|search\s+in\s+files)\s+"(?P<query>.+?)"\s*$', self._handle_grep),
            # Grep/search in files (single quotes)
            (r"^\s*(?:please\s+)?(?:grep|find\s+in\s+files|search\s+in\s+files)\s+'(?P<query>.+?)'\s*$", self._handle_grep),
            # Size of item
            (r'^\s*(?:please\s+)?(?:size\s+of|how\s+big\s+is)\s+(?P<name>[\w\-. /\\]+)\s*$', self._handle_size),
            # Tree view
            (r'^\s*(?:please\s+)?tree(?:\s+(?P<depth>\d+))?\s*$', self._handle_tree),
            # Touch file
            (r'^\s*(?:please\s+)?touch\s+(?P<name>[\w\-. /\\]+)\s*$', self._handle_touch),
            # Clear history
            (r'^\s*(?:please\s+)?clear\s+history\s*$', self._handle_clear_history),
            # Recent files
            (r'^\s*(?:please\s+)?recent\s+files(?:\s+(?P<count>\d+))?\s*$', self._handle_recents),
            # Stats
            (r'^\s*(?:please\s+)?stats(?:\s+here)?\s*$', self._handle_stats),
            # Open file
            (r'^\s*(?:please\s+)?open\s+file\s+(?P<name>[\w\-. /\\]+)\s*$', self._handle_open_file)
        ]

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse command text into an intent dictionary.
        
        Args:
            text: Command text to parse
            
        Returns:
            Intent dictionary with command type and parameters
        """
        if not text:
            return {'type': 'UNKNOWN', 'raw': text}
            
        # Convert to lowercase for case-insensitive matching
        text = text.lower().strip()
        
        # Try each pattern
        for pattern, handler in self.patterns:
            match = re.match(pattern, text)
            if match:
                return handler(match)
        
        # Return unknown intent if no pattern matches
        return {'type': 'UNKNOWN', 'raw': text}

    def _handle_help(self, _) -> Dict[str, str]:
        """Handle help command."""
        return {'type': 'HELP'}

    def _handle_exit(self, _) -> Dict[str, str]:
        """Handle exit command."""
        return {'type': 'EXIT'}

    def _handle_list(self, _) -> Dict[str, str]:
        """Handle list files command."""
        return {'type': 'LIST'}

    def _handle_mkdir(self, match) -> Dict[str, str]:
        """Handle create folder command."""
        return {
            'type': 'MKDIR',
            'name': match.group('name').strip()
        }

    def _handle_mkfile(self, match) -> Dict[str, str]:
        """Handle create file command."""
        return {
            'type': 'MKFILE',
            'name': match.group('name').strip()
        }

    def _handle_delete(self, match) -> Dict[str, str]:
        """Handle delete command."""
        kind = 'folder' if match.group('kind') in ['folder', 'directory'] else 'file'
        return {
            'type': 'DELETE',
            'kind': kind,
            'name': match.group('name').strip()
        }

    def _handle_cd(self, match) -> Dict[str, str]:
        """Handle change directory command."""
        return {
            'type': 'CD',
            'path': match.group('path').strip()
        }

    def _handle_back(self, _) -> Dict[str, str]:
        """Handle 'go back' command."""
        return {'type': 'CD', 'path': '..'}

    def _handle_pwd(self, _) -> Dict[str, str]:
        """Handle print working directory command."""
        return {'type': 'PWD'}

    def _handle_open_app(self, match) -> Dict[str, str]:
        """Handle open application command."""
        app = match.group('app').strip()
        return {
            'type': 'OPEN_APP',
            'app': self.ALLOWED_APPS.get(app, app)
        }

    def _handle_search(self, match) -> Dict[str, str]:
        """Handle search files/folders command."""
        return {'type': 'SEARCH', 'query': match.group('query').strip()}

    def _handle_rename(self, match) -> Dict[str, str]:
        """Handle rename command."""
        return {
            'type': 'RENAME',
            'old': match.group('old').strip(),
            'new': match.group('new').strip()
        }

    def _handle_history(self, match) -> Dict[str, Any]:
        """Handle history command with optional count."""
        count_str = match.group('count') if 'count' in match.groupdict() else None
        count = int(count_str) if count_str else 10
        return {'type': 'HISTORY', 'count': count}

    def _handle_copy(self, match) -> Dict[str, str]:
        return {'type': 'COPY', 'src': match.group('src').strip(), 'dst': match.group('dst').strip()}

    def _handle_move(self, match) -> Dict[str, str]:
        return {'type': 'MOVE', 'src': match.group('src').strip(), 'dst': match.group('dst').strip()}

    def _handle_read(self, match) -> Dict[str, str]:
        return {'type': 'READ', 'name': match.group('name').strip()}

    def _handle_append(self, match) -> Dict[str, str]:
        text = match.group('text')
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        return {'type': 'APPEND', 'name': match.group('name').strip(), 'text': text}

    def _handle_grep(self, match) -> Dict[str, str]:
        return {'type': 'GREP', 'query': match.group('query').strip()}

    def _handle_size(self, match) -> Dict[str, str]:
        return {'type': 'SIZE', 'name': match.group('name').strip()}

    def _handle_tree(self, match) -> Dict[str, Any]:
        depth_str = match.group('depth') if 'depth' in match.groupdict() else None
        depth = int(depth_str) if depth_str else 2
        return {'type': 'TREE', 'depth': depth}

    def _handle_touch(self, match) -> Dict[str, str]:
        return {'type': 'TOUCH', 'name': match.group('name').strip()}

    def _handle_clear_history(self, _) -> Dict[str, str]:
        return {'type': 'CLEAR_HISTORY'}

    def _handle_recents(self, match) -> Dict[str, Any]:
        count_str = match.group('count') if 'count' in match.groupdict() else None
        count = int(count_str) if count_str else 10
        return {'type': 'RECENTS', 'count': count}

    def _handle_stats(self, _) -> Dict[str, str]:
        return {'type': 'STATS'}

    def _handle_open_file(self, match) -> Dict[str, str]:
        # Support spoken punctuation like "dot" or "slash"
        name = match.group('name').strip()
        name = re.sub(r'\bdot\b', '.', name)
        name = re.sub(r'\bperiod\b', '.', name)
        name = re.sub(r'\bunderscore\b', '_', name)
        name = re.sub(r'\bdash\b', '-', name)
        name = re.sub(r'\bslash\b', '/', name)
        name = re.sub(r'\bbackslash\b', r'\\', name)
        return {'type': 'OPEN_FILE', 'name': name}

    def get_help(self) -> str:
        """Return help text listing available commands."""
        commands = [
            "Available commands:",
            "- help",
            "- exit / quit",
            "- list files",
            "- create folder <name>",
            "- create file <name>",
            "- delete file/folder <name>",
            "- change directory to <path> (or: cd to <path>)",
            "- where am i (or: show working directory)",
            f"- open <app> (available: {', '.join(sorted(set(self.ALLOWED_APPS.keys())))})"
        ]
        return "\n".join(commands)
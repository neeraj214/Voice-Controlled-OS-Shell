"""
Command handler module.

Routes parsed intents to appropriate executor functions and manages help messages.
"""

from typing import Dict, Any, Optional, Tuple, Callable
from . import executor

# Centralized help message with examples
HELP_MESSAGE = """
Available Commands:
------------------
1. File Operations
   • "list files" or "show files"
   • "create file example.txt"
   • "create folder documents"
   • "delete file notes.txt"
   • "delete folder temp"
   • "rename old_name to new_name"
   • "search report" (find files/folders by name)
   • "copy A.txt to backups" (copy file/folder)
   • "move docs to archive" (move/relocate)
   • "read file notes.txt" (show content)
   • "append \"hello\" to file notes.txt" (write text)
   • "grep \"error\"" (search in file contents)
   • "size of docs" (show size)
   • "tree 3" (directory tree up to 3 levels)
   • "touch README.md" (create/update timestamp)
2. Navigation
   • "change directory to documents" or "cd to docs"
   • "where am i" or "current directory"
   • "go back" or "go up"

3. Applications
   • "open notepad"
   • "open calculator"
   • "open file notes.txt" (open with default app)

4. System
   • "help" - Show this help message
   • "exit" or "quit" - Exit the shell
   • "history" or "history 20" - Show recent commands
   • "recent files 10" - Show latest modified files
   • "clear history" - Reset logs
   • "stats" - Count files/folders here

Tips:
-----
• All commands work with natural phrases like "please" or "can you"
• File operations are restricted to the sandbox directory
• Delete operations require confirmation
• Use simple, clear names for files and folders
"""

def handle(intent: Dict[str, Any], st, say: Callable[[str], None]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Handle a parsed command intent.
    
    Args:
        intent: The parsed command intent
        st: Shell state for path operations
        say: Text-to-speech callback
    
    Returns:
        Optional tuple of (state_token, payload) for special states
    """
    try:
        if intent["type"] == "HELP":
            print(HELP_MESSAGE)
            say("Showing available commands")
            return None

        elif intent["type"] == "EXIT":
            say("Goodbye")
            return ("EXIT", {})

        elif intent["type"] == "LIST":
            files = executor.list_files(st)
            print("\nContents:")
            print("─" * 40)
            if not files:
                print("(empty directory)")
            else:
                for f in files:
                    print(f"{'📁 ' if f.is_dir() else '📄 '}{f.name}")
            print("─" * 40)
            say("Listed directory contents")
            return None

        elif intent["type"] == "SEARCH":
            results = executor.search_files(st, intent["query"])
            print(f"\nSearch results for '{intent['query']}':")
            print("─" * 40)
            if not results:
                print("(no matches)")
            else:
                for p in results:
                    kind = '📁 ' if p.is_dir() else '📄 '
                    try:
                        rel = p.relative_to(st.base)
                        print(f"{kind}{rel}")
                    except Exception:
                        print(f"{kind}{p.name}")
            print("─" * 40)
            say("Search completed")
            return None

        elif intent["type"] == "MKDIR":
            executor.mkdir(st, intent["name"])
            msg = f"Created folder '{intent['name']}'"
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "MKFILE":
            executor.mkfile(st, intent["name"])
            msg = f"Created file '{intent['name']}'"
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "RENAME":
            msg = executor.rename_item(st, intent["old"], intent["new"])
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "COPY":
            msg = executor.copy_item(st, intent["src"], intent["dst"])
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "MOVE":
            msg = executor.move_item(st, intent["src"], intent["dst"])
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "READ":
            msg, lines = executor.read_file(st, intent["name"])
            print(msg)
            if lines:
                print("─" * 40)
                for ln in lines:
                    print(ln)
                print("─" * 40)
            say("File read")
            return None

        elif intent["type"] == "APPEND":
            msg = executor.append_file(st, intent["name"], intent["text"])
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "DELETE":
            # Return confirmation request
            return ("AWAIT_CONFIRM_DELETE", {
                "kind": intent["kind"],
                "name": intent["name"]
            })

        elif intent["type"] == "CD":
            executor.cd(st, intent["path"])
            msg = f"Changed directory to '{intent['path']}'"
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "PWD":
            cwd = executor.pwd(st)
            print(f"\nCurrent directory: {cwd}")
            say("Showing current directory")
            return None

        elif intent["type"] == "HISTORY":
            entries = executor.read_history(intent.get("count", 10))
            print("\nRecent history:")
            print("─" * 60)
            if not entries:
                print("(no history yet)")
            else:
                for row in entries:
                    print(f"{row['timestamp']} | {row['intent_type']}: {row['text']} -> {row['outcome']}")
            print("─" * 60)
            say("Showing recent history")
            return None

        elif intent["type"] == "RECENTS":
            files = executor.recent_files(st, intent.get("count", 10))
            print("\nRecent files:")
            print("─" * 60)
            if not files:
                print("(none)")
            else:
                for p in files:
                    try:
                        rel = p.relative_to(st.base)
                        print(f"{rel}  (modified)")
                    except Exception:
                        print(f"{p.name}")
            print("─" * 60)
            say("Showing recent files")
            return None

        elif intent["type"] == "CLEAR_HISTORY":
            msg = executor.clear_history()
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "STATS":
            s = executor.stats(st)
            print(f"\nStats: files={s['files']}, folders={s['folders']}, total={s['total']}")
            say("Showing directory stats")
            return None

        elif intent["type"] == "SIZE":
            msg = executor.item_size(st, intent["name"])
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "TREE":
            lines = executor.dir_tree(st, intent.get("depth", 2))
            print("\nDirectory tree:")
            print("─" * 40)
            for ln in lines:
                print(ln)
            print("─" * 40)
            say("Tree view shown")
            return None

        elif intent["type"] == "TOUCH":
            msg = executor.touch_file(st, intent["name"])
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "OPEN_FILE":
            msg = executor.open_file(st, intent["name"])
            print(msg)
            say(msg)
            return None

        elif intent["type"] == "OPEN_APP":
            executor.open_app(intent["app"])
            msg = f"Opened {intent['app']}"
            print(msg)
            say(msg)
            return None

        else:  # UNKNOWN
            print("\nI didn't understand that command.")
            print("Say 'help' to see available commands.")
            say("Command not recognized. Try asking for help.")
            return None

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"\n❌ {error_msg}")
        say("Sorry, there was an error")
        return None
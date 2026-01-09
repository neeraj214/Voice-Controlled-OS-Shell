"""
Command executor module.

This module provides safe execution of shell commands within a sandbox directory.
All file operations are restricted to the sandbox for security. Commands include
file/directory operations and launching whitelisted applications.
"""

import os
import re
import platform
import subprocess
from pathlib import Path
import shutil
from typing import Dict, List, Optional, Tuple

# OS-specific whitelisted applications
ALLOWED_APPS = {
    'Windows': {
        'notepad': 'notepad',
        'calc': 'calc'
    },
    'Linux': {
        'gedit': 'gedit',
        'calculator': 'gnome-calculator',
        'code': 'code'
    }
}

def list_files(state) -> List[Path]:
    """
    Return files and directories in the current working directory.
    
    Args:
        state: ShellState instance tracking current directory
    Returns:
        Sorted list of Path entries in current directory
    """
    try:
        entries = sorted(state.current_directory.iterdir())
        return entries
    except Exception:
        return []

def mkdir(state, name: str) -> None:
    """
    Create a new directory in the sandbox.
    
    Args:
        state: ShellState instance tracking current directory
        name: Name of directory to create
    """
    try:
        # Resolve path relative to current directory
        new_dir = state.resolve_in_cwd(name)
        
        # Safety check
        if not state.inside_sandbox(new_dir):
            print("Error: Cannot create directory outside sandbox")
            return
            
        # Create directory
        new_dir.mkdir(exist_ok=False)
        print(f"Created directory: {name}")
        
    except FileExistsError:
        print(f"Error: Directory '{name}' already exists")
    except PermissionError:
        print("Error: Permission denied when creating directory")
    except Exception as e:
        print(f"Error creating directory: {str(e)}")

def mkfile(state, name: str) -> None:
    """
    Create a new empty file in the sandbox.
    
    Args:
        state: ShellState instance tracking current directory
        name: Name of file to create
    """
    try:
        # Resolve path relative to current directory
        new_file = state.resolve_in_cwd(name)
        
        # Safety check
        if not state.inside_sandbox(new_file):
            print("Error: Cannot create file outside sandbox")
            return
            
        # Create empty file
        new_file.touch(exist_ok=False)
        print(f"Created file: {name}")
        
    except FileExistsError:
        print(f"Error: File '{name}' already exists")
    except PermissionError:
        print("Error: Permission denied when creating file")
    except Exception as e:
        print(f"Error creating file: {str(e)}")

def delete(state, kind: str, name: str) -> None:
    """
    Delete a file or directory in the sandbox.
    
    Args:
        state: ShellState instance tracking current directory
        kind: Either 'file' or 'folder'
        name: Name of item to delete
    """
    try:
        # Resolve path relative to current directory
        target = state.resolve_in_cwd(name)
        
        # Safety check
        if not state.inside_sandbox(target):
            print("Error: Cannot delete items outside sandbox")
            return
            
        if kind == 'folder':
            if not target.is_dir():
                print(f"Error: '{name}' is not a directory")
                return
            shutil.rmtree(target)
            print(f"Deleted directory: {name}")
        else:  # file
            if not target.is_file():
                print(f"Error: '{name}' is not a file")
                return
            target.unlink()
            print(f"Deleted file: {name}")
            
    except FileNotFoundError:
        print(f"Error: {kind.capitalize()} '{name}' not found")
    except PermissionError:
        print("Error: Permission denied when deleting")
    except Exception as e:
        print(f"Error deleting {kind}: {str(e)}")

def cd(state, path: str) -> None:
    """
    Change current working directory within sandbox.
    
    Args:
        state: ShellState instance tracking current directory
        path: Target directory path (absolute or relative)
    """
    try:
        # Handle special cases
        if path == '..':
            # Don't allow going above sandbox root
            if state.current_directory == state.base:
                print("Error: Already at sandbox root")
                return
                
        # Resolve target path
        target = state.resolve_in_cwd(path)
        
        # Safety checks
        if not state.inside_sandbox(target):
            print("Error: Cannot change to directory outside sandbox")
            return
            
        if not target.is_dir():
            print(f"Error: '{path}' is not a directory")
            return
            
        # Update current directory
        state.change_directory(target)
        print(f"Changed directory to: {target.name}")
        
    except FileNotFoundError:
        print(f"Error: Directory '{path}' not found")
    except PermissionError:
        print("Error: Permission denied when changing directory")
    except Exception as e:
        print(f"Error changing directory: {str(e)}")

def pwd(state) -> str:
    """
    Get current working directory relative to sandbox root.
    
    Args:
        state: ShellState instance tracking current directory
    Returns:
        Relative path string from sandbox root (leading slash)
    """
    try:
        rel_path = state.current_directory.relative_to(state.base)
        return f"/{rel_path}"
    except Exception:
        return "/"

def open_app(app: str) -> None:
    """
    Open a whitelisted application.
    
    Args:
        app: Name of application to open
    """
    try:
        # Get OS-specific application whitelist
        os_name = 'Windows' if platform.system() == 'Windows' else 'Linux'
        allowed = ALLOWED_APPS.get(os_name, {})
        
        # Check if app is whitelisted
        if app not in allowed:
            print(f"Error: Application '{app}' is not allowed")
            return
            
        # Launch application
        subprocess.Popen(
            allowed[app],
            shell=True,  # Required for some Windows apps
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"Opened application: {app}")
        
    except FileNotFoundError:
        print(f"Error: Application '{app}' not found")
    except Exception as e:
        print(f"Error opening application: {str(e)}")

def copy_item(state, src_name: str, dst_name: str) -> str:
    """
    Copy a file or folder within the sandbox.
    """
    try:
        src = state.resolve_in_cwd(src_name)
        dst = state.resolve_in_cwd(dst_name)
        # If dst is a directory, copy inside it
        if dst.exists() and dst.is_dir():
            dst = dst / src.name
        # Safety checks
        if not state.inside_sandbox(src) or not state.inside_sandbox(dst):
            return "Error: Operation outside sandbox"
        if not src.exists():
            return f"Error: '{src_name}' not found"
        if src.is_dir():
            if dst.exists():
                return f"Error: '{dst.name}' already exists"
            shutil.copytree(src, dst)
            return f"Copied folder '{src.name}' to '{dst.name}'"
        else:
            if dst.is_dir():
                dst = dst / src.name
            shutil.copy2(src, dst)
            return f"Copied file '{src.name}' to '{dst.name}'"
    except Exception as e:
        return f"Error: {str(e)}"

def move_item(state, src_name: str, dst_name: str) -> str:
    """
    Move (rename) a file or folder within the sandbox.
    """
    try:
        src = state.resolve_in_cwd(src_name)
        dst = state.resolve_in_cwd(dst_name)
        if dst.exists() and dst.is_dir():
            dst = dst / src.name
        if not state.inside_sandbox(src) or not state.inside_sandbox(dst):
            return "Error: Operation outside sandbox"
        if not src.exists():
            return f"Error: '{src_name}' not found"
        if dst.exists():
            return f"Error: Target '{dst_name}' already exists"
        shutil.move(str(src), str(dst))
        return f"Moved '{src.name}' to '{dst.name}'"
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(state, name: str, max_lines: int = 100) -> Tuple[str, List[str]]:
    """
    Read a text file and return up to max_lines and an outcome.
    """
    try:
        path = state.resolve_in_cwd(name)
        if not state.inside_sandbox(path):
            return ("Error: Outside sandbox", [])
        if not path.is_file():
            return (f"Error: '{name}' is not a file", [])
        lines: List[str] = []
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line.rstrip('\n'))
        return (f"Read {len(lines)} lines from '{path.name}'", lines)
    except Exception as e:
        return (f"Error: {str(e)}", [])

def append_file(state, name: str, text: str) -> str:
    """
    Append text to a file, creating it if it doesn't exist.
    """
    try:
        path = state.resolve_in_cwd(name)
        if not state.inside_sandbox(path):
            return "Error: Outside sandbox"
        with open(path, 'a', encoding='utf-8') as f:
            f.write(text + "\n")
        return f"Appended text to '{path.name}'"
    except Exception as e:
        return f"Error: {str(e)}"

def grep_files(state, query: str) -> List[Tuple[Path, int, str]]:
    """
    Search for query substring in text files under current directory.
    Returns list of (path, line_no, line_text).
    """
    q = query.lower().strip()
    results: List[Tuple[Path, int, str]] = []
    try:
        for p in state.current_directory.rglob('*'):
            if p.is_file():
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, start=1):
                            if q in line.lower():
                                if state.inside_sandbox(p):
                                    results.append((p, i, line.strip()))
                except Exception:
                    continue
        return results[:500]  # cap results for speed
    except Exception:
        return []

def _dir_size(path: Path) -> int:
    total = 0
    try:
        if path.is_file():
            return path.stat().st_size
        for p in path.rglob('*'):
            try:
                if p.is_file():
                    total += p.stat().st_size
            except Exception:
                continue
    except Exception:
        return total
    return total

def _fmt_size(bytes_count: int) -> str:
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_count)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.2f} {u}"
        size /= 1024
    return f"{bytes_count} B"

def item_size(state, name: str) -> str:
    try:
        path = state.resolve_in_cwd(name)
        if not state.inside_sandbox(path):
            return "Error: Outside sandbox"
        if not path.exists():
            return f"Error: '{name}' not found"
        size = _dir_size(path)
        return f"Size of '{path.name}': {_fmt_size(size)}"
    except Exception as e:
        return f"Error: {str(e)}"

def dir_tree(state, depth: int = 2) -> List[str]:
    """
    Generate a simple tree view up to given depth.
    """
    base = state.current_directory
    lines: List[str] = [f"{base.name}/"]
    try:
        def walk(dir_path: Path, level: int):
            if level > depth:
                return
            entries = sorted(dir_path.iterdir())
            for e in entries:
                prefix = '  ' * level + ('├─ ' if e != entries[-1] else '└─ ')
                lines.append(prefix + (e.name + ('/' if e.is_dir() else '')))
                if e.is_dir():
                    walk(e, level + 1)
        walk(base, 1)
        return lines
    except Exception:
        return lines

def touch_file(state, name: str) -> str:
    try:
        path = state.resolve_in_cwd(name)
        if not state.inside_sandbox(path):
            return "Error: Outside sandbox"
        path.touch(exist_ok=True)
        return f"Touched '{path.name}'"
    except Exception as e:
        return f"Error: {str(e)}"

def clear_history() -> str:
    from pathlib import Path
    import csv
    log_file = Path('logs.csv')
    try:
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'text', 'intent_type', 'outcome'])
        return "History cleared"
    except Exception as e:
        return f"Error: {str(e)}"

def recent_files(state, count: int = 10) -> List[Path]:
    try:
        files = [p for p in state.current_directory.rglob('*') if p.is_file()]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files[:count]
    except Exception:
        return []

def stats(state) -> Dict[str, int]:
    try:
        entries = list(state.current_directory.iterdir())
        return {
            'files': sum(1 for e in entries if e.is_file()),
            'folders': sum(1 for e in entries if e.is_dir()),
            'total': len(entries)
        }
    except Exception:
        return {'files': 0, 'folders': 0, 'total': 0}

def open_file(state, name: str) -> str:
    try:
        # Normalize spoken punctuation to path characters
        def _normalize_spoken_path(s: str) -> str:
            s = re.sub(r'\bdot\b', '.', s)
            s = re.sub(r'\bperiod\b', '.', s)
            s = re.sub(r'\bunderscore\b', '_', s)
            s = re.sub(r'\bdash\b', '-', s)
            s = re.sub(r'\bslash\b', '/', s)
            s = re.sub(r'\bbackslash\b', r'\\', s)
            return s

        normalized = _normalize_spoken_path(name).strip()
        # Build candidate names to try
        candidates = [name.strip()]
        if normalized != candidates[0]:
            candidates.append(normalized)
        # Heuristic: convert "base ext" -> "base.ext" for common extensions
        m = re.match(r"^(?P<base>[\w\-. /\\]+)\s+(?P<ext>txt|pdf|docx|xlsx|csv|md|png|jpg|jpeg)$", normalized)
        if m:
            candidates.append(f"{m.group('base').strip()}.{m.group('ext').strip()}")

        # Try each candidate until one exists
        path = None
        for cand in candidates:
            try:
                p = state.resolve_in_cwd(cand)
                if state.inside_sandbox(p) and p.exists():
                    path = p
                    break
            except Exception:
                continue
        if path is None:
            return f"Error: '{normalized}' not found"
        if not state.inside_sandbox(path):
            return "Error: Outside sandbox"
        if platform.system() == 'Windows':
            os.startfile(str(path))  # type: ignore
        else:
            subprocess.Popen(['xdg-open', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Opened '{path.name}'"
    except Exception as e:
        return f"Error: {str(e)}"

def search_files(state, query: str) -> List[Path]:
    """
    Search for files and folders by substring in name within current directory tree.
    
    Args:
        state: ShellState instance
        query: Substring to search for (case-insensitive)
    Returns:
        List of matching Path objects (files or directories)
    """
    q = query.lower().strip()
    try:
        matches: List[Path] = []
        for p in state.current_directory.rglob('*'):
            try:
                if q in p.name.lower():
                    # Ensure still inside sandbox
                    if state.inside_sandbox(p):
                        matches.append(p)
            except Exception:
                continue
        return sorted(matches)
    except Exception:
        return []

def rename_item(state, old: str, new: str) -> str:
    """
    Rename a file or folder within the sandbox.
    
    Args:
        state: ShellState
        old: Existing name or relative path
        new: New name
    Returns:
        Outcome message string
    """
    try:
        src = state.resolve_in_cwd(old)
        if not state.inside_sandbox(src):
            return "Error: Cannot rename items outside sandbox"
        if not src.exists():
            return f"Error: '{old}' not found"
        dst = src.parent / new
        if not state.inside_sandbox(dst):
            return "Error: Target path outside sandbox"
        if dst.exists():
            return f"Error: '{new}' already exists"
        src.rename(dst)
        kind = 'folder' if dst.is_dir() else 'file'
        return f"Renamed {kind} '{src.name}' to '{dst.name}'"
    except Exception as e:
        return f"Error: {str(e)}"

def read_history(count: int) -> List[dict]:
    """
    Read recent command history entries from logs.csv.
    
    Args:
        count: Number of recent entries to read
    Returns:
        List of dict entries with keys timestamp, text, intent_type, outcome
    """
    from pathlib import Path
    import csv
    log_file = Path('logs.csv')
    if not log_file.exists():
        return []
    rows: List[dict] = []
    try:
        with open(log_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            for row in data[-count:]:
                rows.append({
                    'timestamp': row.get('timestamp', ''),
                    'text': row.get('text', ''),
                    'intent_type': row.get('intent_type', ''),
                    'outcome': row.get('outcome', '')
                })
        return rows
    except Exception:
        return []
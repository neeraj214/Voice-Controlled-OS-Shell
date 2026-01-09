"""
State management module.

This module manages the shell's state, particularly the sandbox directory
and current working directory. It ensures all file operations remain
within the sandbox for security.
"""

from pathlib import Path
from typing import Optional


class ShellState:
    def __init__(self, sandbox_path: Optional[str] = None):
        """
        Initialize shell state with sandbox directory.
        Creates sandbox if it doesn't exist.
        
        Args:
            sandbox_path: Optional path to sandbox directory
        """
        # Get absolute path to sandbox directory
        self.base = Path(sandbox_path or "sandbox").resolve()
        
        # Create sandbox if it doesn't exist
        if not self.base.exists():
            self.base.mkdir(parents=True)
        elif not self.base.is_dir():
            raise RuntimeError("sandbox exists but is not a directory")
            
        # Set current working directory to sandbox root
        self.cwd = self.base
    
    def inside_sandbox(self, target: Path) -> bool:
        """
        Check if a path is within the sandbox directory.
        
        Args:
            target: Path to check
            
        Returns:
            True if path is within sandbox, False otherwise
        """
        try:
            # Resolve any symlinks and relative path components
            target = target.resolve()
            # Check if target is sandbox or subdirectory of sandbox
            return self.base in target.parents or target == self.base
        except (RuntimeError, OSError):
            # Handle symlink loops and permission issues
            return False
    
    def resolve_in_cwd(self, rel: str) -> Path:
        """
        Safely resolve a relative path string against current working directory.
        
        Args:
            rel: Relative path string
            
        Returns:
            Resolved absolute Path object
            
        Raises:
            ValueError: If path would escape sandbox
        """
        # Handle special case for current directory
        if rel in (".", ""):
            return self.cwd
            
        # Resolve path relative to current directory
        target = (self.cwd / rel).resolve()
        
        # Ensure resolved path is within sandbox
        if not self.inside_sandbox(target):
            raise ValueError(f"Path '{rel}' would escape sandbox")
            
        return target
    
    def change_directory(self, path: str) -> bool:
        """
        Change current working directory.
        
        Args:
            path: Target directory path (relative to cwd)
            
        Returns:
            True if directory was changed, False otherwise
        """
        try:
            new_dir = self.resolve_in_cwd(path)
            if not new_dir.is_dir():
                return False
            self.cwd = new_dir
            return True
        except ValueError:
            return False
    
    @property
    def current_directory(self) -> Path:
        """Get current working directory."""
        return self.cwd
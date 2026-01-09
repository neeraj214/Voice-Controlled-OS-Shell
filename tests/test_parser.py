"""
Test suite for command parser.

This module contains test cases for the command parser, covering various
command patterns, edge cases, and error conditions.
"""

import pytest
from src.parser import CommandParser

@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return CommandParser()

def test_help_command(parser):
    """Test help command variations."""
    assert parser.parse("help") == {"type": "HELP"}
    assert parser.parse("show help") == {"type": "HELP"}
    assert parser.parse("  help  ") == {"type": "HELP"}
    assert parser.parse("what can you do") == {"type": "HELP"}
    assert parser.parse("show available commands") == {"type": "HELP"}

def test_exit_commands(parser):
    """Test exit command variations."""
    assert parser.parse("exit") == {"type": "EXIT"}
    assert parser.parse("quit") == {"type": "EXIT"}
    assert parser.parse("please exit") == {"type": "EXIT"}
    assert parser.parse("goodbye") == {"type": "EXIT"}
    assert parser.parse("bye") == {"type": "EXIT"}

def test_list_files_command(parser):
    """Test list files command variations."""
    assert parser.parse("list files") == {"type": "LIST"}
    assert parser.parse("show files") == {"type": "LIST"}
    assert parser.parse("list all files") == {"type": "LIST"}
    assert parser.parse("what files are here") == {"type": "LIST"}
    assert parser.parse("show me the contents") == {"type": "LIST"}

def test_create_folder_command(parser):
    """Test folder creation command variations."""
    assert parser.parse("create folder test") == {
        "type": "MKDIR",
        "name": "test"
    }
    assert parser.parse("create a new folder downloads") == {
        "type": "MKDIR",
        "name": "downloads"
    }
    assert parser.parse("create directory src") == {
        "type": "MKDIR",
        "name": "src"
    }
    assert parser.parse("make a folder called temp") == {
        "type": "MKDIR",
        "name": "temp"
    }

def test_create_file_command(parser):
    """Test file creation command variations."""
    assert parser.parse("create file test.txt") == {
        "type": "MKFILE",
        "name": "test.txt"
    }
    assert parser.parse("create a new file readme.md") == {
        "type": "MKFILE",
        "name": "readme.md"
    }
    assert parser.parse("make file data.json") == {
        "type": "MKFILE",
        "name": "data.json"
    }
    assert parser.parse("create a file called config.yaml") == {
        "type": "MKFILE",
        "name": "config.yaml"
    }

def test_delete_commands(parser):
    """Test delete command variations."""
    assert parser.parse("delete file test.txt") == {
        "type": "DELETE",
        "kind": "file",
        "name": "test.txt"
    }
    assert parser.parse("delete folder downloads") == {
        "type": "DELETE",
        "kind": "folder",
        "name": "downloads"
    }
    assert parser.parse("delete directory temp") == {
        "type": "DELETE",
        "kind": "folder",
        "name": "temp"
    }
    assert parser.parse("remove file data.json") == {
        "type": "DELETE",
        "kind": "file",
        "name": "data.json"
    }

def test_change_directory_commands(parser):
    """Test directory navigation command variations."""
    assert parser.parse("cd to downloads") == {
        "type": "CD",
        "path": "downloads"
    }
    assert parser.parse("change directory to src/test") == {
        "type": "CD",
        "path": "src/test"
    }
    assert parser.parse("go to ..") == {
        "type": "CD",
        "path": ".."
    }
    assert parser.parse("move to folder projects") == {
        "type": "CD",
        "path": "projects"
    }
    assert parser.parse("switch to directory docs") == {
        "type": "CD",
        "path": "docs"
    }

def test_pwd_commands(parser):
    """Test print working directory command variations."""
    assert parser.parse("where am i") == {"type": "PWD"}
    assert parser.parse("show working directory") == {"type": "PWD"}
    assert parser.parse("show current directory") == {"type": "PWD"}
    assert parser.parse("what folder am i in") == {"type": "PWD"}
    assert parser.parse("current location") == {"type": "PWD"}

def test_open_app_commands(parser):
    """Test application opening command variations."""
    assert parser.parse("open notepad") == {
        "type": "OPEN_APP",
        "app": "notepad"
    }
    assert parser.parse("open calculator") == {
        "type": "OPEN_APP",
        "app": "calc"
    }
    assert parser.parse("open the calculator") == {
        "type": "OPEN_APP",
        "app": "calc"
    }
    assert parser.parse("launch notepad") == {
        "type": "OPEN_APP",
        "app": "notepad"
    }
    assert parser.parse("start calculator") == {
        "type": "OPEN_APP",
        "app": "calc"
    }

def test_unknown_commands(parser):
    """Test handling of unknown or invalid commands."""
    assert parser.parse("") == {
        "type": "UNKNOWN",
        "raw": ""
    }
    assert parser.parse("invalid command") == {
        "type": "UNKNOWN",
        "raw": "invalid command"
    }
    assert parser.parse("create") == {
        "type": "UNKNOWN",
        "raw": "create"
    }
    assert parser.parse("make coffee") == {
        "type": "UNKNOWN",
        "raw": "make coffee"
    }
    assert parser.parse("do something weird") == {
        "type": "UNKNOWN",
        "raw": "do something weird"
    }

def test_edge_cases(parser):
    """Test edge cases and boundary conditions."""
    # Extra whitespace
    assert parser.parse("   list    files   ") == {"type": "LIST"}
    
    # Mixed case
    assert parser.parse("CrEaTe FiLe test.txt") == {
        "type": "MKFILE",
        "name": "test.txt"
    }
    
    # Special characters in names
    assert parser.parse("create file test-1_special.txt") == {
        "type": "MKFILE",
        "name": "test-1_special.txt"
    }
    
    # Path separators
    assert parser.parse("cd to path/to/dir") == {
        "type": "CD",
        "path": "path/to/dir"
    }
    
    # Very long file names
    long_name = "very_long_file_name_that_is_valid_with_special_chars-1.txt"
    assert parser.parse(f"create file {long_name}") == {
        "type": "MKFILE",
        "name": long_name
    }

def test_polite_commands(parser):
    """Test commands with polite phrases."""
    assert parser.parse("please create file test.txt") == {
        "type": "MKFILE",
        "name": "test.txt"
    }
    assert parser.parse("please list files") == {"type": "LIST"}
    assert parser.parse("please delete folder temp") == {
        "type": "DELETE",
        "kind": "folder",
        "name": "temp"
    }
    assert parser.parse("could you show me where I am") == {"type": "PWD"}
    assert parser.parse("would you kindly open notepad") == {
        "type": "OPEN_APP",
        "app": "notepad"
    }
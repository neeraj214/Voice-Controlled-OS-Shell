# Voice-Controlled OS Shell

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?logo=windows)
![Project](https://img.shields.io/badge/Type-OS%20Project-orange)
![Voice](https://img.shields.io/badge/Interface-Voice%20%2B%20Text-green)
![GUI](https://img.shields.io/badge/GUI-Tkinter-blueviolet)
![STT](https://img.shields.io/badge/STT-SpeechRecognition-red)
![TTS](https://img.shields.io/badge/TTS-pyttsx3-yellow)
![Security](https://img.shields.io/badge/Security-Sandboxed-success)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)
![Tests](https://img.shields.io/badge/Tests-pytest-blue)
![CodeStyle](https://img.shields.io/badge/Code%20Style-black-black)

**A Voice-Activated File System Interface**

---

### 🎓 Academic Project
**MCA Semester 1 NLP Project**  
**Author:** Neeraj Negi ([@neeraj214](https://github.com/neeraj214))  
**Institution:** Bennett University  
**Department:** Department of Computer Science / MCA

---

## 📋 Project Overview

The **Voice-Controlled OS Shell** is a Python-based application designed to bridge the gap between traditional command-line interfaces and natural language interaction. Developed as part of the MCA curriculum at Bennett University, this project demonstrates the integration of Speech-to-Text (STT) and Text-to-Speech (TTS) technologies to create an accessible and efficient file management tool.

The application allows users to perform essential file system operations—such as creating, deleting, and organizing files—using simple voice commands. It operates within a secure **sandboxed environment** to ensure safety and prevent accidental system modification.

## ✨ Key Features

- **🗣️ Voice Command Recognition:** Execute file operations using natural voice commands via Google Speech Recognition.
- **⌨️ Dual Input Modes:** Seamlessly switch between Voice and Text input modes.
- **🛡️ Sandboxed Security:** All file operations are restricted to a `sandbox/` directory to protect the host system.
- **🔊 Audio Feedback:** Integrated Text-to-Speech (TTS) provides auditory confirmation of actions.
- **🖥️ Graphical User Interface (GUI):** A user-friendly Tkinter-based dashboard displaying real-time status, command history, and directory contents.
- **📝 Activity Logging:** comprehensive logging system (`logs.csv`) tracks user interactions for analysis and debugging.
- **💻 Cross-Platform:** Compatible with Windows and Linux environments.

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.8+ |
| **Frontend** | Tkinter (GUI) |
| **Speech Recognition** | `SpeechRecognition` (Google Web Speech API) |
| **Audio Input** | `PyAudio` |
| **Text-to-Speech** | `pyttsx3` (Offline TTS) |
| **Testing** | `pytest` |
| **Code Quality** | `black`, `pylint` |

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher installed.
- Microphone for voice input.

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd voice-shell
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On Windows, if PyAudio fails, install `pipwin` first:*
   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```

3. **Linux Specifics**
   Users on Ubuntu/Debian may need additional system libraries:
   ```bash
   sudo apt-get install python3-dev portaudio19-dev espeak
   ```

## 📖 Usage

Run the application using the following command:

### Launch GUI Mode (Recommended)
```bash
python -m src.main --ui
```

### Launch CLI Mode
```bash
python -m src.main
```

### Command Line Arguments
- `--ui`: Start with the Graphical User Interface.
- `--text`: Force text-only input mode.
- `--no-tts`: Disable voice feedback.
- `--sandbox <path>`: Specify a custom sandbox directory.

## 🗣️ Supported Commands

The shell understands natural language variations. Examples include:

| Category | Voice Command Examples |
|----------|------------------------|
| **File Creation** | "Create file notes.txt", "Make a folder called Project" |
| **File Management** | "Delete file old.doc", "Rename data.txt to backup.txt" |
| **Navigation** | "Change directory to documents", "Go back", "Where am I?" |
| **Utilities** | "Open calculator", "Open notepad", "List files" |
| **System** | "Help", "History", "Exit" |

## 📂 Project Structure

```
voice-shell/
├── src/
│   ├── main.py        # Application entry point
│   ├── ui.py          # Tkinter GUI implementation
│   ├── commands.py    # Command handling logic
│   ├── executor.py    # File system operations (Sandboxed)
│   ├── parser.py      # Natural language command parser
│   ├── stt.py         # Speech-to-Text module
│   ├── tts.py         # Text-to-Speech module
│   └── state.py       # Shell state management
├── tests/             # Pytest test suite
├── sandbox/           # Safe directory for file operations
├── logs.csv           # Interaction logs
└── requirements.txt   # Project dependencies
```

## 👨‍💻 About the Developer

**Neeraj Negi**  
**MCA Student**  
**Bennett University, Greater Noida**

This project represents a practical application of Operating System concepts and Human-Computer Interaction (HCI) principles, showcasing skills in Python development, system programming, and UI design.

---

<div align="center"> 
   <sub>Built with ❤️ by <a href="https://github.com/neeraj214">Neeraj Negi</a> as part of the MCA Curriculum.</sub> 
</div>

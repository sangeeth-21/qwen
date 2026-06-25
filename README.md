# Qwen — Voice-Powered AI Assistant

A macOS desktop voice assistant with a Siri-like interface, powered by Google AI Studio (Gemini). Wake word, voice recognition, and text-to-speech, all running locally.

<p align="center">
  <img src="app/resources/icon.png" width="120" alt="Qwen Icon">
</p>

## ✨ Features

- **🎤 Voice-First Interface** — Say *"Hey Qwen"* or click the mic button
- **🧠 Google Gemini AI** — Free streaming AI via Google AI Studio API
- **🗣 Speech Recognition** — Whisper/faster-whisper for accurate transcription
- **🔊 Voice Response** — macOS `say` engine (built-in, no extra setup)
- **⚡ Fast & Lightweight** — Minimal overlay, instant wake word detection
- **🖥 Menu Bar App** — Runs in the background, accessible from system tray
- **🌙 Glassmorphism UI** — Modern, translucent design

## 🖼 Screenshots

| Onboarding | Voice Overlay |
|---|---|
| API key setup dialog | Siri-style glass overlay |

## 🚀 Quick Start

### Prerequisites

- macOS 13+
- Python 3.12+
- A free [Google AI Studio API key](https://aistudio.google.com/apikey)

### Install

```bash
# Clone the repository
git clone https://github.com/sangeeth-21/qwen.git
cd qwen

# Create virtual environment and install dependencies
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
# First run — shows onboarding dialog to enter API key
PYTHONPATH=. .venv/bin/python -m app

# Or pass API key directly (skips onboarding)
QWEN_GOOGLE_API_KEY="your_key_here" PYTHONPATH=. .venv/bin/python -m app
```

## 🎯 Usage

1. **First launch** — A dialog asks for your Google AI Studio API key
2. **Say *"Hey Qwen"*** — The overlay appears and starts listening
3. **Speak your question** — 5 seconds of recording
4. **Get AI response** — Transcribed, processed by Gemini, spoken aloud
5. **Click 🎤** — Manual toggle if wake word isn't working

The app lives in your menu bar. Double-click the icon to open.

## 🧩 Project Structure

```
qwen/
├── app/
│   ├── __main__.py        # Module entry point
│   ├── main.py            # Application launcher
│   ├── backend/
│   │   ├── server.py      # FastAPI HTTP server
│   │   ├── ai_engine.py   # Google Gemini API integration
│   │   ├── voice.py       # Audio recording + Whisper transcription
│   │   ├── tts.py         # macOS say command TTS
│   │   ├── wake_word.py   # Wake word detection engine
│   │   └── config.py      # Settings (env/file based)
│   ├── ui/
│   │   ├── onboarding.py  # First-run API key dialog
│   │   └── siri_overlay.py# Siri-style voice overlay widget
│   ├── resources/
│   │   └── icon.py        # App icon generator
│   └── utils/
│       └── logger.py      # Logging setup
├── scripts/
│   ├── build_dmg.sh       # DMG packaging script
│   └── entitlements.plist # macOS sandbox entitlements
├── requirements.txt
├── setup.py               # py2app build config
├── Makefile
└── .env.example
```

## 🏗 Architecture

- **PyQt6** — Desktop UI (frameless glass overlay, system tray)
- **FastAPI** — Local HTTP backend (threaded inside the Qt app)
- **Google Gemini API** — Streaming AI responses
- **faster-whisper** — Offline speech-to-text
- **openWakeWord + Whisper** — Wake word detection
- **macOS `say`** — Native text-to-speech

The frontend (PyQt6) communicates with the backend (FastAPI) via HTTP on `127.0.0.1:8001`.

## 📦 Building a DMG

```bash
make install   # Set up venv + dependencies
make build     # Build .app with py2app
make build-dmg # Package into .dmg installer
```

Output: `dist/Qwen Desktop.dmg`

## 🔧 Configuration

Environment variables (or `.env` file):

| Variable | Default | Description |
|---|---|---|
| `QWEN_GOOGLE_API_KEY` | `""` | Google AI Studio API key |
| `QWEN_GOOGLE_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `QWEN_WHISPER_MODEL` | `base` | Whisper model size |
| `QWEN_TTS_VOICE` | `Samantha` | macOS voice name |
| `QWEN_WAKE_WORD_ENABLED` | `true` | Enable wake word detection |
| `QWEN_FIRST_RUN` | `true` | Show onboarding dialog |

## 🤝 Contributing

Contributions welcome! Open an issue or PR.

## 📄 License

MIT

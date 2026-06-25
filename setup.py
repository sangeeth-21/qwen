import sys
from setuptools import find_packages, setup

APP_NAME = "Qwen Desktop"
VERSION = "1.0.0"

APP = ["app/main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "strip": True,
    "iconfile": "app/resources/icon.icns",
    "plist": {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": "com.qwen.desktop",
        "CFBundleVersion": VERSION,
        "CFBundleShortVersionString": VERSION,
        "CFBundleExecutable": APP_NAME,
        "CFBundleIconFile": "icon.icns",
        "NSHighResolutionCapable": True,
        "NSMicrophoneUsageDescription": "Qwen needs microphone access for voice input.",
        "NSSpeechRecognitionUsageDescription": "Qwen needs speech recognition for voice commands.",
    },
    "packages": find_packages(),
    "includes": [
        "PyQt6",
        "fastapi",
        "uvicorn",
        "httpx",
        "faster_whisper",
        "numpy",
        "sounddevice",
        "soundfile",
    ],
}

setup(
    name=APP_NAME.lower().replace(" ", "_"),
    version=VERSION,
    description="AI-powered desktop assistant",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.0",
        "httpx>=0.27.0",
        "PyQt6>=6.7.0",
        "faster-whisper>=1.0.3",
        "openai>=1.51.0",
        "sounddevice>=0.5.1",
        "soundfile>=0.12.1",
        "numpy>=2.0.0",
        "pydantic-settings>=2.5.0",
        "duckduckgo-search>=7.1.0",
        "wikipedia-api>=0.7.1",
        "openwakeword>=0.5.0",
        "requests>=2.32.3",
        "psutil>=6.0.0",
    ],
)

import json
import logging
import os
import subprocess
import sys
import threading

import httpx
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.backend.config import settings
from app.ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)

BACKEND_URL = f"http://{settings.host}:{settings.port}"


class ChatStreamThread(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, messages: list[dict], parent=None):
        super().__init__(parent)
        self.messages = messages

    def run(self):
        try:
            with httpx.Client(timeout=120) as client:
                with client.stream(
                    "POST",
                    f"{BACKEND_URL}/chat",
                    json={"messages": self.messages, "stream": True},
                ) as resp:
                    if resp.status_code != 200:
                        self.error.emit(f"Server error: {resp.status_code}")
                        return
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = (
                                    chunk.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if content:
                                    self.chunk_received.emit(content)
                            except json.JSONDecodeError:
                                pass
            self.finished.emit()
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{settings.app_name} v{settings.app_version}")
        self.setMinimumSize(900, 600)
        self._setup_ui()
        self._setup_menu()
        self._setup_tray()
        self._backend_process: subprocess.Popen | None = None
        self._start_backend()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        splitter = QSplitter()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        self.input_edit = QTextEdit()
        self.input_edit.setMaximumHeight(100)
        self.input_edit.setPlaceholderText("Type your message here...")

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.chat_display)
        right_layout.addWidget(self.input_edit)

        splitter.addWidget(right_panel)
        layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Starting backend...")

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        settings_action = QAction("&Settings...", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip(settings.app_name)
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(
            lambda reason: self.show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self.tray_icon.show()

    def _start_backend(self):
        def run():
            import uvicorn
            from app.backend.server import app

            uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.status_bar.showMessage("Backend running")

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(
            self,
            f"About {settings.app_name}",
            f"<b>{settings.app_name}</b> v{settings.app_version}<br><br>"
            "AI-powered desktop assistant with voice support.",
        )

    def send_message(self, text: str):
        self.chat_display.append(f"<b>You:</b> {text}")
        messages = [{"role": "user", "content": text}]
        self.status_bar.showMessage("AI is thinking...")
        self.stream_thread = ChatStreamThread(messages)
        self.stream_thread.chunk_received.connect(self._on_chunk)
        self.stream_thread.finished.connect(
            lambda: self.status_bar.showMessage("Ready", 5000)
        )
        self.stream_thread.error.connect(
            lambda err: self.status_bar.showMessage(f"Error: {err}")
        )
        self.stream_thread.start()

    def _on_chunk(self, chunk: str):
        self.chat_display.insertPlainText(chunk)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            settings.app_name,
            "Still running in the background.",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

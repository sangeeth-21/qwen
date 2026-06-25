import sys
import threading

import uvicorn
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.backend.config import settings
from app.backend.voice import transcriber
from app.backend.wake_word import engine as wake_engine
from app.resources.icon import get_icon_path, get_small_icon_path
from app.ui.onboarding import OnboardingDialog
from app.ui.siri_overlay import SiriOverlay
from app.utils.logger import setup_logging


def start_backend():
    from app.backend.server import app
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="warning")


class QwenApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Qwen")

        self.overlay = SiriOverlay()
        self._backend_started = False
        self._setup_tray()

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self.app)
        self.tray.setToolTip("Qwen - Voice Assistant")
        self.tray.setIcon(QIcon(get_small_icon_path()))

        menu = QMenu()
        show_action = menu.addAction("🎤 Open Qwen")
        show_action.triggered.connect(self.show_overlay)
        reset_action = menu.addAction("🔄 Reset Conversation")
        reset_action.triggered.connect(self._reset_conversation)
        menu.addSeparator()
        settings_action = menu.addAction("⚙ Settings")
        settings_action.triggered.connect(self._open_settings)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()
        self.tray.showMessage("Qwen", "Running in background. Say \"Hey Qwen\"!", QSystemTrayIcon.MessageIcon.Information, 3000)

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_overlay()

    def _open_settings(self):
        from app.ui.onboarding import OnboardingDialog
        dialog = OnboardingDialog()
        dialog.exec()

    def show_overlay(self):
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()

    def _reset_conversation(self):
        import httpx
        try:
            httpx.post(f"http://{settings.host}:{settings.port}/conversation/reset", timeout=3)
        except Exception:
            pass

    def _quit(self):
        wake_engine.stop()
        self.app.quit()

    def _init_backend(self):
        if self._backend_started:
            return
        self._backend_started = True
        threading.Thread(target=start_backend, daemon=True).start()
        threading.Thread(target=transcriber.load, daemon=True).start()

    def run(self):
        self._init_backend()

        if settings.first_run:
            QTimer.singleShot(1000, self._show_onboarding)
        else:
            QTimer.singleShot(1500, self.show_overlay)

        sys.exit(self.app.exec())

    def _show_onboarding(self):
        dialog = OnboardingDialog()
        dialog.exec()
        self.show_overlay()


def main():
    setup_logging("WARNING")
    app = QwenApp()
    app.run()


if __name__ == "__main__":
    main()

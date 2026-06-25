import math
import threading
import time

import httpx
from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.backend.config import settings
from app.backend.wake_word import engine as wake_engine
from app.resources.icon import get_small_icon_path

BACKEND_URL = f"http://{settings.host}:{settings.port}"

_ICON_PIXMAP = None


def _get_icon():
    global _ICON_PIXMAP
    if _ICON_PIXMAP is None:
        _ICON_PIXMAP = QPixmap(get_small_icon_path())
    return _ICON_PIXMAP


COLORS = {
    "idle": (100, 100, 160),
    "listening": (67, 97, 238),
    "processing": (238, 130, 67),
    "done": (67, 200, 150),
}


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 100)
        self._amplitude = 0.0
        self._target = 0.0
        self._phase = 0.0
        self._state = "idle"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(20)

    def set_state(self, state: str):
        self._state = state
        self._target = 1.0 if state != "idle" else 0.0

    def set_amplitude(self, amp: float):
        self._target = min(1.0, max(0.1, amp * 2.5))

    def _tick(self):
        self._amplitude += (self._target - self._amplitude) * 0.12
        self._phase += 0.06
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        r, g, b = COLORS.get(self._state, COLORS["idle"])
        alpha = int(80 + 175 * self._amplitude)
        base_color = QColor(r, g, b, alpha)
        glow_color = QColor(r, g, b, max(20, alpha // 4))

        # Outer glow ring
        glow_radius = 20 + self._amplitude * 8
        glow_path = QPainterPath()
        glow_path.addEllipse(cx - glow_radius, cy - glow_radius, glow_radius * 2, glow_radius * 2)
        painter.setBrush(glow_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(glow_path)

        # Animated bars
        num_bars = 13
        bar_w = 4
        gap = 3
        total_w = num_bars * (bar_w + gap) - gap
        start_x = (w - total_w) / 2
        max_h = 50

        for i in range(num_bars):
            rel = (i - num_bars / 2) / (num_bars / 2)
            envelope = max(0.05, 1 - abs(rel) * 0.7)
            wave = math.sin(self._phase + i * 0.6) * 0.5 + 0.5
            height = max(3, self._amplitude * max_h * envelope * wave + 3)

            bar_color = QColor(r, g, b)
            bar_color.setAlphaF(0.3 + 0.7 * envelope)
            painter.setBrush(bar_color)
            painter.setPen(Qt.PenStyle.NoPen)

            x = start_x + i * (bar_w + gap)
            rect = QRectF(x, cy - height / 2, bar_w, height)
            painter.drawRoundedRect(rect, 2, 2)

        painter.end()


class SiriOverlay(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qwen")
        self.setFixedSize(420, 280)

        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._setup_ui()
        self._position_top_right()
        self._state = "idle"
        self._setup_wake_word()

    def _setup_ui(self):
        self.outer = QWidget(self)
        self.outer.setGeometry(0, 0, 420, 280)

        layout = QVBoxLayout(self.outer)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(6)

        # Top bar
        top = QHBoxLayout()
        icon = QLabel()
        pix = _get_icon().scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        icon.setPixmap(pix)
        top.addWidget(icon)

        self.status_text = QLabel("Say \"Hey Qwen\"")
        self.status_text.setFont(QFont("SF Pro Display", 12, QFont.Weight.Medium))
        self.status_text.setStyleSheet("color: rgba(200,200,220,200); background: transparent; padding-left: 6px;")
        top.addWidget(self.status_text)
        top.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,20); color: rgba(200,200,220,150);
                border: none; border-radius: 13px; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,80,80,120); color: white; }
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._minimize)
        top.addWidget(close_btn)
        layout.addLayout(top)

        # Waveform
        center = QHBoxLayout()
        center.addStretch()
        self.waveform = WaveformWidget(self)
        center.addWidget(self.waveform)
        center.addStretch()
        layout.addLayout(center)
        layout.addSpacing(4)

        # Text display
        self.text_label = QLabel("")
        self.text_label.setFont(QFont("SF Pro Display", 14))
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: rgba(255,255,255,200); background: transparent; padding: 2px 8px;")
        self.text_label.setFixedHeight(40)
        layout.addWidget(self.text_label)

        # Response display
        self.response_label = QLabel("")
        self.response_label.setFont(QFont("SF Pro Display", 13))
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setStyleSheet("color: rgba(200,200,230,180); background: transparent; padding: 2px 8px;")
        self.response_label.setFixedHeight(50)
        layout.addWidget(self.response_label)

        # Mic button
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(48, 48)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: rgba(67,97,238,200); color: white;
                border: none; border-radius: 24px; font-size: 24px;
            }
            QPushButton:hover { background: rgba(67,97,238,255); }
            QPushButton:pressed { background: rgba(50,70,200,255); }
        """)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.clicked.connect(self._toggle_mic)
        bottom.addWidget(self.mic_btn)
        bottom.addStretch()
        layout.addLayout(bottom)

    def _position_top_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.width() - 16, geo.top() + 60)

    def _setup_wake_word(self):
        def callback():
            QTimer.singleShot(0, self._start_listening)
        wake_engine.set_callback(callback)
        wake_engine.start()

    def _minimize(self):
        self.hide()
        self.closed.emit()

    def _toggle_mic(self):
        if self._state == "idle":
            self._start_listening()
        else:
            self._stop_listening()

    def _start_listening(self):
        if self._state != "idle":
            return
        self._state = "listening"
        self.waveform.set_state("listening")
        self.status_text.setText("Listening...")
        self.text_label.setText("")
        self.response_label.setText("")
        self.show()
        self.raise_()
        self.activateWindow()
        self._start_record()

    def _start_record(self):
        try:
            httpx.post(f"{BACKEND_URL}/record/start", timeout=3)
        except Exception as e:
            self._show_result("", f"Backend not ready: {e}")
            return
        QTimer.singleShot(5000, self._stop_listening)

    def _stop_listening(self):
        if self._state != "listening":
            return
        self._state = "processing"
        self.waveform.set_state("processing")
        self.status_text.setText("Thinking...")
        threading.Thread(target=self._process_voice, daemon=True).start()

    def _process_voice(self):
        try:
            resp = httpx.post(f"{BACKEND_URL}/voice/process", timeout=30)
            data = resp.json()
            text = data.get("text", "")
            response = data.get("response", "")
            QTimer.singleShot(0, lambda: self._show_result(text, response))
        except httpx.ConnectError:
            QTimer.singleShot(0, lambda: self._show_result("", "Backend not running. Restart the app."))
        except Exception as exc:
            QTimer.singleShot(0, lambda: self._show_result("", f"Error: {exc}"))

    def _show_result(self, text: str, response: str):
        self.text_label.setText(f'"{text}"' if text else "")
        self.response_label.setText(response)
        self.waveform.set_state("done")
        self.status_text.setText("Tap 🎤 or say \"Hey Qwen\"")
        self._state = "idle"
        QTimer.singleShot(1500, lambda: self.waveform.set_state("idle"))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 28, 28)

        # Glassmorphism background
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        gradient.setColorAt(0, QColor(18, 18, 35, 230))
        gradient.setColorAt(1, QColor(28, 20, 50, 230))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(67, 97, 238, 60), 1.5))
        painter.drawPath(path)

    def closeEvent(self, event):
        wake_engine.stop()
        self.closed.emit()
        super().closeEvent(event)

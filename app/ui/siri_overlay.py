import math
import threading

import httpx
from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
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
    "idle": (100, 100, 170),
    "listening": (67, 97, 238),
    "processing": (255, 170, 60),
    "done": (67, 200, 150),
}


class SiriCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self._energy = 0.0
        self._target = 0.0
        self._phase = 0.0
        self._state = "idle"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(20)

    def set_state(self, state: str):
        self._state = state
        self._target = 1.0 if state != "idle" else 0.0

    def set_energy(self, val: float):
        self._target = min(1.0, max(0.05, val * 2.5))

    def _tick(self):
        self._energy += (self._target - self._energy) * 0.1
        self._phase += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        r, g, b = COLORS.get(self._state, COLORS["idle"])
        max_radius = 54
        num_rings = 6

        for i in range(num_rings):
            frac = i / num_rings
            wave = math.sin(self._phase + frac * math.tau * 2) * 0.5 + 0.5
            ring_r = max_radius * (0.3 + 0.7 * frac) + self._energy * 12 * wave
            thickness = 3 + self._energy * 6 * (1 - frac)

            alpha = int(40 + 180 * (1 - frac * 0.7) * self._energy)
            if self._state == "idle":
                alpha = int(20 + 30 * (0.5 + 0.5 * wave))

            color = QColor(r, g, b, alpha)
            pen = QPen(color, thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            start_angle = self._phase * 30 + i * 30
            span = 180 + 120 * (1 - frac / num_rings)
            path = QPainterPath()
            path.arcMoveTo(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2), start_angle)
            path.arcTo(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2), start_angle, span)
            painter.drawPath(path)

        painter.end()


class SiriOverlay(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qwen")
        self.setFixedSize(380, 340)

        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._setup_ui()
        self._position_top_right()
        self._state = "idle"
        self._setup_wake_word()

    def _setup_ui(self):
        self.outer = QWidget(self)
        self.outer.setGeometry(0, 0, 380, 340)

        layout = QVBoxLayout(self.outer)
        layout.setContentsMargins(20, 14, 20, 18)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(6)
        icon = QLabel()
        pix = _get_icon().scaled(
            22, 22, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        icon.setPixmap(pix)
        icon.setStyleSheet("background: transparent;")
        top.addWidget(icon)

        self.status_label = QLabel('Say "Hey Qwen"')
        self.status_label.setFont(QFont("SF Pro Text", 11, QFont.Weight.Medium))
        self.status_label.setStyleSheet("color: rgba(200,200,220,160); background: transparent;")
        top.addWidget(self.status_label)
        top.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,15); color: rgba(200,200,220,120);
                border: none; border-radius: 12px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,80,80,120); color: white; }
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._minimize)
        top.addWidget(close_btn)
        layout.addLayout(top)

        self.circle = SiriCircle()
        layout.addWidget(self.circle, alignment=Qt.AlignmentFlag.AlignCenter)

        self.text_label = QLabel("")
        self.text_label.setFont(QFont("SF Pro Display", 13))
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: rgba(255,255,255,190); background: transparent; padding: 2px 6px;")
        self.text_label.setFixedHeight(36)
        layout.addWidget(self.text_label)

        self.response_label = QLabel("")
        self.response_label.setFont(QFont("SF Pro Display", 12))
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setStyleSheet("color: rgba(200,200,230,150); background: transparent; padding: 2px 6px;")
        self.response_label.setFixedHeight(44)
        layout.addWidget(self.response_label)

        bottom = QHBoxLayout()
        bottom.addStretch()
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(42, 42)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: rgba(67,97,238,180); color: white;
                border: none; border-radius: 21px; font-size: 20px;
            }
            QPushButton:hover { background: rgba(67,97,238,255); }
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
        self.circle.set_state("listening")
        self.status_label.setText("Listening...")
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
        self.circle.set_state("processing")
        self.status_label.setText("Thinking...")
        threading.Thread(target=self._process_voice, daemon=True).start()

    def _process_voice(self):
        try:
            resp = httpx.post(f"{BACKEND_URL}/voice/process", timeout=30)
            data = resp.json()
            text = data.get("text", "")
            response = data.get("response", "")
            QTimer.singleShot(0, lambda: self._show_result(text, response))
        except httpx.ConnectError:
            QTimer.singleShot(0, lambda: self._show_result("", "Backend not running."))
        except Exception as exc:
            QTimer.singleShot(0, lambda: self._show_result("", f"Error: {exc}"))

    def _show_result(self, text: str, response: str):
        self.text_label.setText(f'"{text}"' if text else "")
        self.response_label.setText(response)
        self.circle.set_state("done")
        self.status_label.setText('Tap 🎤 or say "Hey Qwen"')
        self._state = "idle"
        QTimer.singleShot(1500, lambda: self.circle.set_state("idle"))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 28, 28)
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        gradient.setColorAt(0, QColor(15, 15, 32, 235))
        gradient.setColorAt(1, QColor(25, 18, 48, 235))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(67, 97, 238, 50), 1))
        painter.drawPath(path)

    def closeEvent(self, event):
        wake_engine.stop()
        self.closed.emit()
        super().closeEvent(event)

import math
import webbrowser

from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QDialog,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.backend.config import settings
from app.resources.icon import get_small_icon_path

STYLE = """
QDialog {
    background: transparent;
}
QLineEdit {
    background: rgba(255,255,255,0.06);
    color: white;
    border: 1.5px solid rgba(255,255,255,0.12);
    border-radius: 14px;
    padding: 16px 20px;
    font-size: 15px;
    min-height: 22px;
    selection-background-color: #4361ee;
}
QLineEdit:focus {
    border: 1.5px solid #4361ee;
    background: rgba(67,97,238,0.08);
}
QPushButton#connect_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4361ee, stop:1 #3a0ca3);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 14px 32px;
    font-size: 15px;
    font-weight: bold;
    min-height: 22px;
}
QPushButton#connect_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a6ff5, stop:1 #4a0ca3);
}
QPushButton#link_btn {
    background: transparent;
    color: #4cc9f0;
    border: none;
    font-size: 13px;
    padding: 2px;
}
QPushButton#link_btn:hover { color: #7dd3fc; }
QPushButton#skip_btn {
    background: transparent;
    color: rgba(255,255,255,0.3);
    border: none;
    font-size: 13px;
    padding: 8px;
}
QPushButton#skip_btn:hover { color: rgba(255,255,255,0.6); }
"""


class ParticleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._particles = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(30)
        self._init_particles()

    def _init_particles(self):
        import random
        for _ in range(20):
            self._particles.append({
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "vx": random.uniform(-0.002, 0.002),
                "vy": random.uniform(-0.002, -0.006),
                "size": random.uniform(1.5, 3.5),
                "alpha": random.uniform(0.1, 0.4),
            })

    def _update(self):
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha"] -= 0.001
            if p["y"] < -0.05 or p["alpha"] <= 0:
                import random
                p["x"] = random.uniform(0, 1)
                p["y"] = 1.05
                p["alpha"] = random.uniform(0.1, 0.4)
                p["vx"] = random.uniform(-0.002, 0.002)
                p["vy"] = random.uniform(-0.002, -0.006)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        for p in self._particles:
            color = QColor(67, 97, 238)
            color.setAlphaF(p["alpha"])
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(
                p["x"] * w - p["size"] / 2,
                p["y"] * h - p["size"] / 2,
                p["size"], p["size"]
            ))
        painter.end()


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Qwen")
        self.setFixedSize(520, 580)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)
        self._setup_ui()
        self._center_on_screen()

    def _center_on_screen(self):
        screen = self.screen()
        if screen:
            c = screen.availableGeometry().center()
            self.move(int(c.x() - self.width() / 2), int(c.y() - self.height() / 2))

    def _setup_ui(self):
        self._particles = ParticleWidget(self)
        self._particles.setGeometry(0, 0, 520, 580)

        outer = QWidget(self)
        outer.setGeometry(0, 0, 520, 580)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(48, 50, 48, 40)
        layout.setSpacing(6)

        icon_label = QLabel()
        pm = QPixmap(get_small_icon_path()).scaled(
            88, 88, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        icon_label.setPixmap(pm)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)
        layout.addSpacing(10)

        title = QLabel("Welcome to Qwen")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("SF Pro Display", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent; letter-spacing: -0.5px;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Your AI voice assistant.\n"
            'Say <b>"Hey Qwen"</b> to start.'
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("SF Pro Text", 14))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.5); background: transparent;")
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        api_label = QLabel("API Key")
        api_label.setFont(QFont("SF Pro Text", 12, QFont.Weight.Medium))
        api_label.setStyleSheet("color: rgba(255,255,255,0.6); background: transparent; padding-left: 2px;")
        layout.addWidget(api_label)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Paste your Google AI Studio API key")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_input)

        link_layout = QHBoxLayout()
        link_layout.setContentsMargins(0, 0, 0, 0)
        link_btn = QPushButton("Get a free key at Google AI Studio →")
        link_btn.setObjectName("link_btn")
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/apikey"))
        link_layout.addWidget(link_btn)
        link_layout.addStretch()
        layout.addLayout(link_layout)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("SF Pro Text", 12))
        self.status_label.setStyleSheet("color: #ff6b6b; background: transparent;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        layout.addSpacing(16)

        self.connect_btn = QPushButton("Connect to Google AI Studio")
        self.connect_btn.setObjectName("connect_btn")
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.clicked.connect(self._connect)
        self.connect_btn.setMinimumHeight(52)
        layout.addWidget(self.connect_btn)

        skip_btn = QPushButton("Skip for now")
        skip_btn.setObjectName("skip_btn")
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        skip_btn.clicked.connect(self._skip)
        layout.addWidget(skip_btn)
        layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 28, 28)
        gradient = QLinearGradient(0, 0, rect.width(), rect.height())
        gradient.setColorAt(0, QColor(12, 12, 28, 240))
        gradient.setColorAt(1, QColor(22, 14, 40, 240))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        painter.setPen(QColor(67, 97, 238, 50))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), 28, 28)

    def _connect(self):
        key = self.api_input.text().strip()
        if not key:
            self.status_label.setText("Enter your API key")
            self.status_label.setVisible(True)
            return
        if len(key) < 10:
            self.status_label.setText("Invalid API key format")
            self.status_label.setVisible(True)
            return
        settings.google_api_key = key
        settings.first_run = False
        self.accept()

    def _skip(self):
        settings.first_run = False
        self.accept()

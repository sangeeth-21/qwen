import webbrowser

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.backend.config import settings
from app.resources.icon import get_icon_path, get_small_icon_path

STYLE = """
QDialog {
    background-color: #0f0f1a;
}
QLabel {
    color: #e8e8f0;
    background: transparent;
}
QLineEdit {
    background-color: #1a1a2e;
    color: white;
    border: 2px solid #2a2a4a;
    border-radius: 14px;
    padding: 16px 20px;
    font-size: 15px;
    min-height: 22px;
    selection-background-color: #4361ee;
}
QLineEdit:focus {
    border: 2px solid #4361ee;
}
QPushButton#connect_btn {
    background-color: #4361ee;
    color: white;
    border: none;
    border-radius: 14px;
    padding: 14px 32px;
    font-size: 15px;
    font-weight: bold;
    min-height: 22px;
}
QPushButton#connect_btn:hover {
    background-color: #3f37c9;
}
QPushButton#connect_btn:disabled {
    background-color: #2a2a4a;
    color: #666;
}
QPushButton#link_btn {
    background: transparent;
    color: #4cc9f0;
    border: none;
    font-size: 13px;
    padding: 4px;
}
QPushButton#link_btn:hover {
    color: #7dd3fc;
}
QPushButton#skip_btn {
    background: transparent;
    color: #555;
    border: none;
    font-size: 13px;
    padding: 8px;
}
QPushButton#skip_btn:hover {
    color: #888;
}
"""


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Qwen")
        self.setFixedSize(500, 560)
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
            center = screen.availableGeometry().center()
            self.move(int(center.x() - self.width() / 2), int(center.y() - self.height() / 2))

    def _setup_ui(self):
        outer = QWidget(self)
        outer.setGeometry(0, 0, 500, 560)
        outer.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0f0f1a, stop:1 #1a1030);
            border-radius: 24px;
            border: 1px solid rgba(67,97,238,60);
        """)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(44, 48, 44, 40)
        layout.setSpacing(8)

        icon_label = QLabel()
        pixmap = QPixmap(get_small_icon_path()).scaled(
            80, 80, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        layout.addSpacing(8)

        title = QLabel("Welcome to Qwen")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("SF Pro Display", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Your voice-powered AI assistant.\n"
            "Say <b>\"Hey Qwen\"</b> to start a conversation."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("SF Pro Text", 14))
        subtitle.setStyleSheet("color: #9898b0; background: transparent; line-height: 1.5;")
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        api_label = QLabel("Google AI Studio API Key")
        api_label.setFont(QFont("SF Pro Text", 12, QFont.Weight.Medium))
        api_label.setStyleSheet("color: #c0c0d0; background: transparent;")
        layout.addWidget(api_label)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Paste your API key here...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_input)

        link_btn = QPushButton("Get a free API key →")
        link_btn.setObjectName("link_btn")
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.clicked.connect(
            lambda: webbrowser.open("https://aistudio.google.com/apikey")
        )
        layout.addWidget(link_btn)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("SF Pro Text", 12))
        self.status_label.setStyleSheet("color: #ff6b6b; background: transparent;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        layout.addSpacing(12)

        self.connect_btn = QPushButton("Connect to Google AI Studio")
        self.connect_btn.setObjectName("connect_btn")
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.clicked.connect(self._connect)
        self.connect_btn.setMinimumHeight(52)
        layout.addWidget(self.connect_btn)

        skip_btn = QPushButton("Skip for now — I'll configure later")
        skip_btn.setObjectName("skip_btn")
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        skip_btn.clicked.connect(self._skip)
        layout.addWidget(skip_btn)

        layout.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(15, 15, 26))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = self.rect()
        painter.drawRoundedRect(rect, 24, 24)

    def _connect(self):
        key = self.api_input.text().strip()
        if not key:
            self.status_label.setText("Please enter your API key")
            self.status_label.setVisible(True)
            return
        if len(key) < 10:
            self.status_label.setText("That doesn't look like a valid API key")
            self.status_label.setVisible(True)
            return
        settings.google_api_key = key
        settings.first_run = False
        self.accept()

    def _skip(self):
        settings.first_run = False
        self.accept()

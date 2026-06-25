from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.backend.config import settings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self._ai_tab(), "AI Provider")
        tabs.addTab(self._voice_tab(), "Voice")
        tabs.addTab(self._wake_tab(), "Wake Word")
        tabs.addTab(self._search_tab(), "Search")
        layout.addWidget(tabs)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _ai_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openrouter", "nvidia", "google"])
        form.addRow("Provider:", self.provider_combo)

        self.openrouter_key = QLineEdit()
        self.openrouter_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("OpenRouter API Key:", self.openrouter_key)

        self.openrouter_model = QLineEdit()
        form.addRow("OpenRouter Model:", self.openrouter_model)

        self.nvidia_key = QLineEdit()
        self.nvidia_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("NVIDIA API Key:", self.nvidia_key)

        self.google_key = QLineEdit()
        self.google_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Google AI Studio Key:", self.google_key)

        return w

    def _voice_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(["say", "piper"])
        form.addRow("TTS Engine:", self.tts_engine_combo)

        self.tts_voice = QLineEdit()
        form.addRow("TTS Voice:", self.tts_voice)

        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        form.addRow("Whisper Model:", self.whisper_model_combo)

        return w

    def _wake_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self.wake_enabled = QCheckBox("Enable wake word detection")
        form.addRow(self.wake_enabled)

        self.wake_model = QLineEdit()
        form.addRow("Wake Word Model:", self.wake_model)

        self.wake_sensitivity = QSlider()
        self.wake_sensitivity.setRange(0, 100)
        form.addRow("Sensitivity:", self.wake_sensitivity)

        self.wake_sensitivity_label = QLabel("0.5")
        form.addRow(self.wake_sensitivity_label)
        self.wake_sensitivity.valueChanged.connect(
            lambda v: self.wake_sensitivity_label.setText(f"{v/100:.2f}")
        )

        return w

    def _search_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self.search_provider_combo = QComboBox()
        self.search_provider_combo.addItems(["duckduckgo", "wikipedia"])
        form.addRow("Search Provider:", self.search_provider_combo)

        return w

    def _load_settings(self):
        self.provider_combo.setCurrentText(settings.ai_provider)
        self.openrouter_key.setText(settings.openrouter_api_key)
        self.openrouter_model.setText(settings.openrouter_model)
        self.nvidia_key.setText(settings.nvidia_api_key)
        self.google_key.setText(settings.google_ai_studio_key)
        self.tts_engine_combo.setCurrentText(settings.tts_engine)
        self.tts_voice.setText(settings.tts_voice)
        self.whisper_model_combo.setCurrentText(settings.whisper_model)
        self.wake_enabled.setChecked(settings.wake_word_enabled)
        self.wake_model.setText(settings.wake_word_model)
        self.wake_sensitivity.setValue(int(settings.wake_word_sensitivity * 100))
        self.search_provider_combo.setCurrentText(settings.search_provider)

    def _save_settings(self):
        settings.ai_provider = self.provider_combo.currentText()
        settings.openrouter_api_key = self.openrouter_key.text()
        settings.openrouter_model = self.openrouter_model.text()
        settings.nvidia_api_key = self.nvidia_key.text()
        settings.google_ai_studio_key = self.google_key.text()
        settings.tts_engine = self.tts_engine_combo.currentText()
        settings.tts_voice = self.tts_voice.text()
        settings.whisper_model = self.whisper_model_combo.currentText()
        settings.wake_word_enabled = self.wake_enabled.isChecked()
        settings.wake_word_model = self.wake_model.text()
        settings.wake_word_sensitivity = self.wake_sensitivity.value() / 100
        settings.search_provider = self.search_provider_combo.currentText()
        self.accept()

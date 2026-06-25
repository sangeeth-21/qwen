import logging
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from app.backend.config import settings

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, samplerate: int = 16000):
        self.samplerate = samplerate
        self._recording: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._is_recording = False

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self, device: int | None = None):
        self._recording = []
        self._is_recording = True

        def callback(indata, frames, time_info, status):
            if self._is_recording:
                self._recording.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="float32",
            device=device,
            callback=callback,
        )
        self._stream.start()
        logger.debug("Recording started")

    def stop(self) -> np.ndarray:
        self._is_recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._recording:
            logger.debug("No audio captured")
            return np.array([], dtype="float32")
        audio = np.concatenate(self._recording, axis=0).flatten()
        logger.debug("Recording stopped: %d samples", len(audio))
        return audio

    def save_wav(self, audio: np.ndarray, path: str | Path) -> str:
        path = Path(path)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            audio_int16 = (audio * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        return str(path)


class Transcriber:
    def __init__(self):
        self._model: WhisperModel | None = None

    def load(self):
        if self._model is not None:
            return
        logger.info("Loading Whisper model: %s on %s", settings.whisper_model, settings.whisper_device)
        self._model = WhisperModel(
            model_size_or_path=settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
        logger.info("Whisper model loaded")

    def transcribe(self, audio: np.ndarray | str) -> str:
        if self._model is None:
            self.load()
        segments, _ = self._model.transcribe(audio, language="en")
        return " ".join(seg.text.strip() for seg in segments)


recorder = AudioRecorder()
transcriber = Transcriber()

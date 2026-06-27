import logging
import queue
import threading

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from app.backend.config import settings

logger = logging.getLogger(__name__)


class WakeWordEngine:
    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._callback = None
        self._stream: sd.InputStream | None = None
        self._model: WhisperModel | None = None

    def load(self):
        if self._model is not None:
            return
        try:
            self._model = WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("Wake word model loaded")
        except Exception as exc:
            logger.warning("Wake word model failed: %s", exc)

    def set_callback(self, callback):
        self._callback = callback

    def start(self):
        if self._running:
            return
        self.load()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Wake word engine started")

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        logger.info("Wake word engine stopped")

    def _audio_callback(self, indata, frames, time_info, status):
        if self._running:
            self._audio_queue.put(indata.copy())

    def _detect(self, audio: np.ndarray) -> bool:
        if self._model is None:
            return False
        try:
            segments, _ = self._model.transcribe(audio, language="en")
            text = " ".join(seg.text.strip().lower() for seg in segments)
            for phrase in ["hey qwen", "hey queen", "hay queen", "hey q wen", "hey quin"]:
                if phrase in text:
                    logger.info("Wake word: '%s'", text)
                    return True
        except Exception:
            pass
        return False

    def _run(self):
        self._stream = sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()
        buffer = np.array([], dtype="float32")

        while self._running:
            try:
                chunk = self._audio_queue.get(timeout=0.05)
                buffer = np.concatenate([buffer, chunk.flatten()])
                if len(buffer) >= 32000:
                    segment = buffer[:32000]
                    buffer = buffer[16000:]
                    if settings.wake_word_enabled and self._detect(segment):
                        if self._callback:
                            self._callback()
            except queue.Empty:
                pass


engine = WakeWordEngine()

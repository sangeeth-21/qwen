import asyncio
import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.backend.ai_engine import chat_stream
from app.backend.config import settings
from app.backend.tts import speak
from app.backend.voice import recorder, transcriber

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_conversation_history: list[dict] = []


class ChatRequest(BaseModel):
    text: str


class ConfigUpdate(BaseModel):
    key: str
    value: str


@app.on_event("startup")
async def startup():
    logger.info("Backend server started")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "configured": bool(settings.google_api_key),
    }


@app.get("/config")
async def get_config():
    return {
        "google_api_key": bool(settings.google_api_key),
        "google_model": settings.google_model,
        "first_run": settings.first_run,
        "tts_voice": settings.tts_voice,
    }


@app.post("/config")
async def update_config(update: ConfigUpdate):
    if not hasattr(settings, update.key):
        raise HTTPException(status_code=400, detail=f"Unknown key: {update.key}")
    setattr(settings, update.key, update.value)
    if update.key == "google_api_key":
        settings.first_run = False
    return {"ok": True}


@app.post("/conversation/reset")
async def reset_conversation():
    _conversation_history.clear()
    return {"ok": True}


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    _conversation_history.append({"role": "user", "content": req.text})
    result = ""
    async for chunk in chat_stream(_conversation_history):
        result += chunk
    _conversation_history.append({"role": "assistant", "content": result})
    return {"response": result}


@app.post("/voice/process")
async def voice_process():
    audio = recorder.stop()
    if len(audio) < 1600:
        raise HTTPException(status_code=400, detail="No audio captured")

    text = transcriber.transcribe(audio)
    text = text.strip()
    if not text:
        return {"text": "", "response": "I didn't catch that. Could you repeat?"}

    _conversation_history.append({"role": "user", "content": text})
    result = ""
    async for chunk in chat_stream(_conversation_history):
        result += chunk
    _conversation_history.append({"role": "assistant", "content": result})

    asyncio.create_task(speak(result))
    return {"text": text, "response": result}


@app.post("/record/start")
async def record_start():
    recorder.start()
    return {"ok": True}


@app.post("/record/stop")
async def record_stop():
    audio = recorder.stop()
    if len(audio) < 1600:
        return {"text": ""}
    text = transcriber.transcribe(audio)
    return {"text": text.strip()}


@app.post("/speak")
async def speak_endpoint(text: str):
    asyncio.create_task(speak(text))
    return {"ok": True}

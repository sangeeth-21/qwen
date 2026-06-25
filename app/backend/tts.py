import asyncio
import subprocess

from app.backend.config import settings


async def speak(text: str) -> None:
    voice = settings.tts_voice
    cmd = ["say", "-v", voice, text]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    await proc.wait()


def speak_sync(text: str) -> None:
    voice = settings.tts_voice
    subprocess.run(["say", "-v", voice, text], capture_output=True)

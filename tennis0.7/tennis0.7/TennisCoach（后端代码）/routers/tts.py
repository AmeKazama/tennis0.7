import io
import os
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.staticfiles import StaticFiles


router = APIRouter(tags=["tts"])

BASE_DIR = Path(__file__).resolve().parent.parent
SAVE_DIR = BASE_DIR / "tts_audio"


def register_tts_static(app):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/audio", StaticFiles(directory=SAVE_DIR), name="audio")


async def tts_convert(text: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    try:
        import edge_tts
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="TTS dependency is missing. Please install edge-tts.",
        ) from exc

    communicate = edge_tts.Communicate(text, voice)
    audio_buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])

    audio_buffer.seek(0)
    return audio_buffer.read()


@router.post("/api/tts")
async def api_tts(request: Request):
    data = await request.json()
    text = data.get("text", "Welcome to Tennis AI Coach")
    voice = data.get("voice", "zh-CN-XiaoxiaoNeural")

    audio = await tts_convert(text, voice)

    filename = f"tts_{int(time.time() * 1000)}.mp3"
    filepath = SAVE_DIR / filename
    os.makedirs(SAVE_DIR, exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(audio)

    base_url = str(request.base_url).rstrip("/")
    return {"url": f"{base_url}/audio/{filename}"}

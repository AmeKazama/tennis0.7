from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import edge_tts
import io
import os
import time
from pathlib import Path

app = FastAPI()

SAVE_DIR = Path(__file__).resolve().parent / "tts_audio"
os.makedirs(SAVE_DIR, exist_ok=True)

# 挂载静态文件目录
app.mount("/audio", StaticFiles(directory=SAVE_DIR), name="audio")


async def tts_convert(text: str, voice="zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    audio_buffer.seek(0)
    return audio_buffer.read()


@app.post("/api/tts")
async def api_tts(request: Request):
    data = await request.json()
    text = data.get("text", "欢迎使用网球AI教练")
    voice = data.get("voice", "zh-CN-XiaoxiaoNeural")

    audio = await tts_convert(text, voice)

    filename = f"tts_{int(time.time() * 1000)}.mp3"
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(audio)
    print(f"[TTS] 已保存: {filepath}")

    # 返回JSON，包含可访问的URL
    base_url = str(request.base_url).rstrip("/")
    return {"url": f"{base_url}/audio/{filename}"}


if __name__ == "__main__":
    uvicorn.run(app, host="10.24.51.159", port=9002)

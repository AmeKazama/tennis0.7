class FileStorageError(Exception):
    pass


async def save_audio_file(audio, play_date):
    import uuid
    import os
    from pathlib import Path

    allowed_extensions = {".wav", ".mp3", ".m4a", ".pcm", ".amr"}
    original_name = audio.filename or ""
    extension = Path(original_name).suffix.lower()
    if extension not in allowed_extensions:
        raise FileStorageError("暂不支持该音频格式")

    content = await audio.read()
    if not content:
        raise FileStorageError("音频文件为空")

    if not _looks_like_audio(content, extension):
        raise FileStorageError("暂不支持该音频格式")

    upload_root = Path(os.getenv("UPLOAD_AUDIO_ROOT", "uploads/audio"))
    url_prefix = os.getenv("UPLOAD_AUDIO_URL_PREFIX", "/uploads/audio").rstrip("/")
    upload_dir = upload_root / play_date.strftime("%Y") / play_date.strftime("%m") / play_date.strftime("%d")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}{extension}"
    file_path = upload_dir / file_name
    with open(file_path, "wb") as f:
        f.write(content)

    audio_url = f"{url_prefix}/{play_date:%Y/%m/%d}/{file_name}"
    return audio_url, str(file_path)


def _looks_like_audio(content: bytes, extension: str) -> bool:
    if content.startswith(b"RIFF"):
        return extension == ".wav"
    if content.startswith(b"#!AMR"):
        return extension == ".amr"
    if content.startswith(b"ID3"):
        return extension == ".mp3"
    if len(content) > 12 and content[4:8] == b"ftyp":
        return extension in {".m4a", ".mp3"}
    if extension == ".pcm":
        return True
    return extension in {".mp3", ".m4a"} and len(content) > 0

class FileStorageError(Exception):
    pass


async def save_audio_file(audio, play_date):
    import os
    from pathlib import Path
    upload_dir = Path("uploads/audio") / str(play_date)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / audio.filename
    with open(file_path, "wb") as f:
        content = await audio.read()
        f.write(content)
    return f"/uploads/audio/{play_date}/{audio.filename}", str(file_path)

from datetime import datetime
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from db_models.ball_diary import BallDiary
from services.file_storage import FileStorageError, save_audio_file
from services.speech_recognition_service import (
    BaiduSpeechRecognitionService,
    SpeechRecognitionError,
)
from utils.response import error, success

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/diary", tags=["diary"])
speech_service = BaiduSpeechRecognitionService()


@router.get("/list")
async def list_diaries(
    user_id: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    diaries = (
        db.query(BallDiary)
        .filter(BallDiary.user_id == user_id)
        .order_by(BallDiary.create_time.desc())
        .limit(limit)
        .all()
    )

    return success(
        message="查询成功",
        data=[
            {
                "id": diary.id,
                "user_id": diary.user_id,
                "play_date": diary.play_date.strftime("%Y-%m-%d"),
                "content": diary.content,
                "audioUrl": diary.audio_url,
                "mood": diary.mood,
                "opponent": diary.opponent,
                "score": diary.score,
                "sourceType": diary.source_type,
                "createTime": diary.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for diary in diaries
        ],
    )


@router.post("/voice")
async def create_voice_diary(
    user_id: int = Form(...),
    play_date: str = Form(...),
    mood: str | None = Form(None),
    opponent: str | None = Form(None),
    score: str | None = Form(None),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if user_id is None:
        return error("用户 ID 不能为空")
    if not play_date:
        return error("打球日期不能为空")
    if audio is None or not audio.filename:
        return error("音频文件不能为空")

    try:
        parsed_play_date = datetime.strptime(play_date, "%Y-%m-%d").date()
    except ValueError:
        return error("打球日期格式不正确，请使用 YYYY-MM-DD")

    try:
        audio_url, audio_path = await save_audio_file(audio, parsed_play_date)
    except FileStorageError as exc:
        logger.warning("Save audio failed, userId=%s, filename=%s, error=%s", user_id, audio.filename, exc)
        return error(str(exc))

    try:
        content = speech_service.recognize(str(audio_path))
    except SpeechRecognitionError:
        logger.exception("Speech recognition failed, userId=%s, audioPath=%s", user_id, audio_path)
        return error("语音识别失败，请重试")

    diary = BallDiary(
        user_id=user_id,
        play_date=parsed_play_date,
        content=content,
        audio_url=audio_url,
        mood=mood,
        opponent=opponent,
        score=score,
        source_type="voice",
        create_time=datetime.now(),
        update_time=datetime.now(),
    )

    try:
        db.add(diary)
        db.commit()
        db.refresh(diary)
    except Exception as e:
        logger.exception(e)
        db.rollback()
        return error(f"日记保存失败：{str(e)}", code=400)

    return success(
        message="语音日记保存成功",
        data={
            "id": diary.id,
            "content": diary.content,
            "audioUrl": diary.audio_url,
        },
    )

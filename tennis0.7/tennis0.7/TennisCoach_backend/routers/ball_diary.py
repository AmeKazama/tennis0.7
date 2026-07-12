from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.ball_diary import BallDiary
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ball_diary", tags=["ball_diary"])


@router.post("/")
def create_diary(
    user_id: int,
    play_date: str,
    content: Optional[str] = None,
    audio_url: Optional[str] = None,
    mood: Optional[str] = None,
    opponent: Optional[str] = None,
    score: Optional[str] = None,
    source_type: str = "voice",
    db: Session = Depends(get_db),
):
    try:
        try:
            play_date_obj = datetime.strptime(play_date, "%Y-%m-%d").date()
        except ValueError:
            return error("日期格式不正确，请使用 YYYY-MM-DD", code=400)

        diary = BallDiary(
            user_id=user_id,
            play_date=play_date_obj,
            content=content,
            audio_url=audio_url,
            mood=mood,
            opponent=opponent,
            score=score,
            source_type=source_type,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.add(diary)
        db.commit()
        db.refresh(diary)
        return success(message="创建成功", data={"id": diary.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create diary failed")
        return error(f"创建失败：{exc}", code=400)


@router.get("/{diary_id}")
def get_diary(diary_id: int, db: Session = Depends(get_db)):
    try:
        diary = db.query(BallDiary).filter(BallDiary.id == diary_id).first()
        if not diary:
            return error("日记不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": diary.id,
                "user_id": diary.user_id,
                "play_date": diary.play_date.strftime("%Y-%m-%d"),
                "content": diary.content,
                "audio_url": diary.audio_url,
                "mood": diary.mood,
                "opponent": diary.opponent,
                "score": diary.score,
                "source_type": diary.source_type,
                "create_time": diary.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as exc:
        logger.exception("Get diary failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/list")
def list_diaries(
    user_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(BallDiary).filter(BallDiary.user_id == user_id)
        if year:
            query = query.filter(BallDiary.play_date >= f"{year}-01-01").filter(
                BallDiary.play_date <= f"{year}-12-31"
            )
        if month:
            query = query.filter(BallDiary.play_date >= f"{year}-{month:02d}-01").filter(
                BallDiary.play_date <= f"{year}-{month:02d}-31"
            )
        total = query.count()
        diaries = query.order_by(
            BallDiary.play_date.desc()
        ).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": d.id,
                    "user_id": d.user_id,
                    "play_date": d.play_date.strftime("%Y-%m-%d"),
                    "content": d.content,
                    "mood": d.mood,
                    "opponent": d.opponent,
                    "score": d.score,
                    "source_type": d.source_type,
                    "create_time": d.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for d in diaries
            ],
            total=total,
            page=page,
            size=size
        )
    except Exception as exc:
        logger.exception("List diaries failed")
        return error(f"查询失败：{exc}", code=400)


@router.put("/{diary_id}")
def update_diary(
    diary_id: int,
    play_date: Optional[str] = None,
    content: Optional[str] = None,
    mood: Optional[str] = None,
    opponent: Optional[str] = None,
    score: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        diary = db.query(BallDiary).filter(BallDiary.id == diary_id).first()
        if not diary:
            return error("日记不存在", code=404)

        if play_date is not None:
            try:
                diary.play_date = datetime.strptime(play_date, "%Y-%m-%d").date()
            except ValueError:
                return error("日期格式不正确，请使用 YYYY-MM-DD", code=400)
        if content is not None:
            diary.content = content
        if mood is not None:
            diary.mood = mood
        if opponent is not None:
            diary.opponent = opponent
        if score is not None:
            diary.score = score

        diary.update_time = datetime.now()
        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update diary failed")
        return error(f"更新失败：{exc}", code=400)


@router.delete("/{diary_id}")
def delete_diary(diary_id: int, db: Session = Depends(get_db)):
    try:
        diary = db.query(BallDiary).filter(BallDiary.id == diary_id).first()
        if not diary:
            return error("日记不存在", code=404)
        db.delete(diary)
        db.commit()
        return success(message="删除成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete diary failed")
        return error(f"删除失败：{exc}", code=400)
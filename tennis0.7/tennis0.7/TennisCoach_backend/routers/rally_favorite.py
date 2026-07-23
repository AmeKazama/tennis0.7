import hashlib
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from db_models.rally_favorite import RallyFavorite
from utils.response import error, success


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rally/favorite", tags=["rally_favorite"])


class RallyFavoriteCreate(BaseModel):
    user_id: int = Field(gt=0)
    video_url: str = Field(min_length=1, max_length=1000)
    poster_url: Optional[str] = Field(default=None, max_length=1000)
    title: Optional[str] = Field(default=None, max_length=120)


def _video_key(video_url: str) -> str:
    return hashlib.sha256(video_url.strip().encode("utf-8")).hexdigest()


def _serialize(item: RallyFavorite) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "video_url": item.video_url,
        "poster_url": item.poster_url,
        "title": item.title or "收藏回合",
        "create_time": item.create_time.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.post("/")
def add_rally_favorite(payload: RallyFavoriteCreate, db: Session = Depends(get_db)):
    video_url = payload.video_url.strip()
    video_key = _video_key(video_url)
    try:
        existing = db.query(RallyFavorite).filter(
            RallyFavorite.user_id == payload.user_id,
            RallyFavorite.video_key == video_key,
        ).first()
        if existing:
            return success(message="该回合已收藏", data=_serialize(existing))

        item = RallyFavorite(
            user_id=payload.user_id,
            video_key=video_key,
            video_url=video_url,
            poster_url=(payload.poster_url or "").strip() or None,
            title=(payload.title or "").strip() or "收藏回合",
            create_time=datetime.now(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return success(message="收藏成功", data=_serialize(item))
    except Exception as exc:
        db.rollback()
        logger.exception("Add rally favorite failed")
        return error(f"收藏失败：{exc}", code=400)


@router.get("/list")
def list_rally_favorites(
    user_id: int = Query(..., gt=0),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(RallyFavorite).filter(RallyFavorite.user_id == user_id)
        items = query.order_by(RallyFavorite.create_time.desc()).offset(
            (page - 1) * size
        ).limit(size).all()
        return success(
            message="查询成功",
            data=[_serialize(item) for item in items],
        )
    except Exception as exc:
        logger.exception("List rally favorites failed")
        return error(f"查询失败：{exc}", code=400)


@router.delete("/{favorite_id}")
def remove_rally_favorite(
    favorite_id: int,
    user_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    try:
        item = db.query(RallyFavorite).filter(
            RallyFavorite.id == favorite_id,
            RallyFavorite.user_id == user_id,
        ).first()
        if not item:
            return error("收藏回合不存在", code=404)

        db.delete(item)
        db.commit()
        return success(message="取消收藏成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Remove rally favorite failed")
        return error(f"取消收藏失败：{exc}", code=400)

from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.user_badge import UserBadge
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user_badge", tags=["user_badge"])


@router.post("/")
def grant_badge(
    user_id: int,
    badge_code: str,
    badge_name: str,
    badge_icon: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        existing = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_code == badge_code
        ).first()
        if existing:
            return error("已拥有该勋章", code=400)

        badge = UserBadge(
            user_id=user_id,
            badge_code=badge_code,
            badge_name=badge_name,
            badge_icon=badge_icon,
            description=description,
            earned_time=datetime.now()
        )
        db.add(badge)
        db.commit()
        db.refresh(badge)
        return success(message="勋章授予成功", data={"id": badge.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Grant badge failed")
        return error(f"授予失败：{exc}", code=400)


@router.get("/list")
def list_user_badges(user_id: int, db: Session = Depends(get_db)):
    try:
        badges = db.query(UserBadge).filter(
            UserBadge.user_id == user_id
        ).order_by(UserBadge.earned_time.desc()).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": b.id,
                    "badge_code": b.badge_code,
                    "badge_name": b.badge_name,
                    "badge_icon": b.badge_icon,
                    "description": b.description,
                    "earned_time": b.earned_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for b in badges
            ]
        )
    except Exception as exc:
        logger.exception("List user badges failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/{badge_id}")
def get_badge_detail(badge_id: int, db: Session = Depends(get_db)):
    try:
        badge = db.query(UserBadge).filter(UserBadge.id == badge_id).first()
        if not badge:
            return error("勋章不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": badge.id,
                "user_id": badge.user_id,
                "badge_code": badge.badge_code,
                "badge_name": badge.badge_name,
                "badge_icon": badge.badge_icon,
                "description": badge.description,
                "earned_time": badge.earned_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as exc:
        logger.exception("Get badge detail failed")
        return error(f"查询失败：{exc}", code=400)
from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.user_training_stats import UserTrainingStats
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user_training_stats", tags=["user_training_stats"])


@router.get("/{user_id}")
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    try:
        stats = db.query(UserTrainingStats).filter(UserTrainingStats.user_id == user_id).first()
        if not stats:
            return error("用户统计数据不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": stats.id,
                "user_id": stats.user_id,
                "training_count": stats.training_count,
                "total_duration_seconds": stats.total_duration_seconds,
                "avg_score": stats.avg_score,
                "best_score": stats.best_score,
                "forehand_count": stats.forehand_count,
                "backhand_count": stats.backhand_count,
                "serve_count": stats.serve_count,
                "forehand_avg_score": stats.forehand_avg_score,
                "backhand_avg_score": stats.backhand_avg_score
            }
        )
    except Exception as exc:
        logger.exception("Get user stats failed")
        return error(f"查询失败：{exc}", code=400)


@router.post("/")
def create_or_update_stats(
    user_id: int,
    training_count: Optional[int] = 0,
    total_duration_seconds: Optional[float] = 0,
    avg_score: Optional[float] = 0,
    best_score: Optional[float] = 0,
    forehand_count: Optional[int] = 0,
    backhand_count: Optional[int] = 0,
    serve_count: Optional[int] = 0,
    forehand_avg_score: Optional[float] = 0,
    backhand_avg_score: Optional[float] = 0,
    db: Session = Depends(get_db),
):
    try:
        stats = db.query(UserTrainingStats).filter(UserTrainingStats.user_id == user_id).first()
        if stats:
            # 更新
            if training_count is not None:
                stats.training_count = training_count
            if total_duration_seconds is not None:
                stats.total_duration_seconds = total_duration_seconds
            if avg_score is not None:
                stats.avg_score = avg_score
            if best_score is not None:
                stats.best_score = best_score
            if forehand_count is not None:
                stats.forehand_count = forehand_count
            if backhand_count is not None:
                stats.backhand_count = backhand_count
            if serve_count is not None:
                stats.serve_count = serve_count
            if forehand_avg_score is not None:
                stats.forehand_avg_score = forehand_avg_score
            if backhand_avg_score is not None:
                stats.backhand_avg_score = backhand_avg_score
            db.commit()
            return success(message="更新成功")
        else:
            # 创建
            new_stats = UserTrainingStats(
                user_id=user_id,
                training_count=training_count or 0,
                total_duration_seconds=total_duration_seconds or 0,
                avg_score=avg_score or 0,
                best_score=best_score or 0,
                forehand_count=forehand_count or 0,
                backhand_count=backhand_count or 0,
                serve_count=serve_count or 0,
                forehand_avg_score=forehand_avg_score or 0,
                backhand_avg_score=backhand_avg_score or 0
            )
            db.add(new_stats)
            db.commit()
            db.refresh(new_stats)
            return success(message="创建成功", data={"id": new_stats.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create/update stats failed")
        return error(f"操作失败：{exc}", code=400)

from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.training_video_record import TrainingVideoRecord
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/training_video_record", tags=["training_video_record"])


@router.post("/")
def create_video_record(
    user_id: int,
    video_url: str,
    title: Optional[str] = None,
    cover_url: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    file_size: Optional[int] = None,
    source_type: str = "upload",
    analysis_id: Optional[str] = None,
    shot_type: Optional[str] = None,
    score: Optional[float] = None,
    db: Session = Depends(get_db),
):
    try:
        record = TrainingVideoRecord(
            user_id=user_id,
            title=title,
            video_url=video_url,
            cover_url=cover_url,
            duration_seconds=duration_seconds,
            file_size=file_size,
            source_type=source_type,
            analysis_id=analysis_id,
            shot_type=shot_type,
            score=score,
            create_time=datetime.now()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return success(message="创建成功", data={"id": record.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create video record failed")
        return error(f"创建失败：{exc}", code=400)


@router.get("/{record_id}")
def get_video_record(record_id: int, db: Session = Depends(get_db)):
    try:
        record = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.id == record_id
        ).first()
        if not record:
            return error("记录不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": record.id,
                "user_id": record.user_id,
                "title": record.title,
                "video_url": record.video_url,
                "cover_url": record.cover_url,
                "duration_seconds": record.duration_seconds,
                "file_size": record.file_size,
                "source_type": record.source_type,
                "analysis_id": record.analysis_id,
                "shot_type": record.shot_type,
                "score": record.score,
                "create_time": record.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as exc:
        logger.exception("Get video record failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/list")
def list_video_records(
    user_id: int,
    source_type: Optional[str] = None,
    shot_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.user_id == user_id
        )
        if source_type:
            query = query.filter(TrainingVideoRecord.source_type == source_type)
        if shot_type:
            query = query.filter(TrainingVideoRecord.shot_type == shot_type)
        total = query.count()
        records = query.order_by(
            TrainingVideoRecord.create_time.desc()
        ).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": r.id,
                    "title": r.title,
                    "video_url": r.video_url,
                    "cover_url": r.cover_url,
                    "duration_seconds": r.duration_seconds,
                    "source_type": r.source_type,
                    "shot_type": r.shot_type,
                    "score": r.score,
                    "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for r in records
            ],
            total=total,
            page=page,
            size=size
        )
    except Exception as exc:
        logger.exception("List video records failed")
        return error(f"查询失败：{exc}", code=400)


@router.put("/{record_id}")
def update_video_record(
    record_id: int,
    title: Optional[str] = None,
    video_url: Optional[str] = None,
    cover_url: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    file_size: Optional[int] = None,
    shot_type: Optional[str] = None,
    score: Optional[float] = None,
    db: Session = Depends(get_db),
):
    try:
        record = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.id == record_id
        ).first()
        if not record:
            return error("记录不存在", code=404)

        if title is not None:
            record.title = title
        if video_url is not None:
            record.video_url = video_url
        if cover_url is not None:
            record.cover_url = cover_url
        if duration_seconds is not None:
            record.duration_seconds = duration_seconds
        if file_size is not None:
            record.file_size = file_size
        if shot_type is not None:
            record.shot_type = shot_type
        if score is not None:
            record.score = score

        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update video record failed")
        return error(f"更新失败：{exc}", code=400)


@router.delete("/{record_id}")
def delete_video_record(record_id: int, db: Session = Depends(get_db)):
    try:
        record = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.id == record_id
        ).first()
        if not record:
            return error("记录不存在", code=404)
        db.delete(record)
        db.commit()
        return success(message="删除成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete video record failed")
        return error(f"删除失败：{exc}", code=400)
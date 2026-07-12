import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.training_video_record import TrainingVideoRecord
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/videos", tags=["videos"])

# 视频上传目录
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的视频格式
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".webm"}


def generate_video_filename(original_filename: str) -> str:
    """生成唯一的视频文件名"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ext = os.path.splitext(original_filename)[1].lower()
    return f"{timestamp}_{hash(original_filename + str(datetime.now().timestamp()))}{ext}"


def get_video_url(filename: str) -> str:
    """获取视频访问URL"""
    return f"/uploads/videos/{filename}"


@router.post("/upload", summary="Upload video to private library")
async def upload_video(
    file: UploadFile = File(..., description="Video file"),
    user_id: int = Form(default=1, description="User ID"),
    title: Optional[str] = Form(default=None, description="Video title"),
    description: Optional[str] = Form(default=None, description="Video description"),
    source_type: str = Form(default="upload", description="Source type"),
    cover_url: Optional[str] = Form(default=None, description="Cover URL"),
    duration_seconds: Optional[float] = Form(default=None, description="Video duration in seconds"),
    db: Session = Depends(get_db),
):
    """
    Upload video to private library. Video is set to private by default.
    """
    try:
        if not file.filename:
            return error("Video file is required", code=400)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return error(f"Unsupported video format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}", code=400)

        filename = generate_video_filename(file.filename)
        file_path = UPLOAD_DIR / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        video_url = get_video_url(filename)

        record = TrainingVideoRecord(
            user_id=user_id,
            title=title or file.filename,
            description=description,
            video_url=video_url,
            cover_url=cover_url,
            duration_seconds=duration_seconds,
            file_size=os.path.getsize(file_path),
            source_type=source_type,
            visibility="private",
            status="uploaded",
            like_count=0,
            comment_count=0,
            favorite_count=0,
            view_count=0,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return success(
            message="Upload successful, saved to private library",
            data={
                "id": record.id,
                "user_id": record.user_id,
                "title": record.title,
                "description": record.description,
                "video_url": record.video_url,
                "src": record.video_url,
                "cover_url": record.cover_url,
                "visibility": record.visibility,
                "status": record.status,
                "type": "video",
                "create_time": record.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as exc:
        db.rollback()
        logger.exception("Upload video failed")
        return error(f"Upload failed: {exc}", code=500)


@router.get("/my", summary="Get my video list")
def get_my_videos(
    user_id: int = Query(default=1, description="User ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Get current user's video list (including private and public, excluding deleted).
    """
    try:
        query = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.user_id == user_id,
            TrainingVideoRecord.status != "deleted"
        )
        total = query.count()

        records = query.order_by(
            TrainingVideoRecord.create_time.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return success(
            message="Query successful",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "list": [
                    {
                        "id": r.id,
                        "user_id": r.user_id,
                        "title": r.title,
                        "description": r.description,
                        "video_url": r.video_url,
                        "src": r.video_url,
                        "cover_url": r.cover_url,
                        "visibility": r.visibility,
                        "status": r.status,
                        "like_count": r.like_count,
                        "comment_count": r.comment_count,
                        "favorite_count": r.favorite_count,
                        "view_count": r.view_count,
                        "publish_time": r.publish_time.strftime("%Y-%m-%d %H:%M:%S") if r.publish_time else None,
                        "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for r in records
                ]
            }
        )
    except Exception as exc:
        logger.exception("Get my videos failed")
        return error(f"Query failed: {exc}", code=400)


@router.get("/{video_id}", summary="Get video detail")
def get_video_detail(
    video_id: int,
    user_id: int = Query(default=1, description="Current user ID"),
    db: Session = Depends(get_db),
):
    """
    Get video detail. Private video can only be viewed by its owner.
    """
    try:
        record = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.id == video_id,
            TrainingVideoRecord.status != "deleted"
        ).first()

        if not record:
            return error("Video not found", code=404)

        if record.visibility == "private" and record.user_id != user_id:
            return error("Permission denied", code=403)

        return success(
            message="Query successful",
            data={
                "id": record.id,
                "user_id": record.user_id,
                "title": record.title,
                "description": record.description,
                "video_url": record.video_url,
                "cover_url": record.cover_url,
                "duration_seconds": record.duration_seconds,
                "file_size": record.file_size,
                "source_type": record.source_type,
                "analysis_id": record.analysis_id,
                "shot_type": record.shot_type,
                "score": record.score,
                "visibility": record.visibility,
                "status": record.status,
                "like_count": record.like_count,
                "comment_count": record.comment_count,
                "favorite_count": record.favorite_count,
                "view_count": record.view_count,
                "publish_time": record.publish_time.strftime("%Y-%m-%d %H:%M:%S") if record.publish_time else None,
                "create_time": record.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as exc:
        logger.exception("Get video detail failed")
        return error(f"Query failed: {exc}", code=400)


@router.post("/{video_id}/publish", summary="Publish video to public feed")
def publish_video(
    video_id: int,
    user_id: int = Form(default=1, description="User ID"),
    content: Optional[str] = Form(default=None, description="Publish content"),
    db: Session = Depends(get_db),
):
    """
    Publish video to public feed. Video will appear in home feed after publishing.
    """
    try:
        record = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.id == video_id
        ).first()

        if not record:
            return error("Video not found", code=404)

        if record.user_id != user_id:
            return error("Permission denied", code=403)

        if record.status == "deleted":
            return error("Deleted video cannot be published", code=400)

        record.visibility = "public"
        record.status = "published"
        record.publish_time = datetime.now()
        if content is not None:
            record.description = content
        record.update_time = datetime.now()

        db.commit()
        db.refresh(record)

        return success(
            message="Publish successful, video is now visible in public feed",
            data={
                "id": record.id,
                "user_id": record.user_id,
                "title": record.title,
                "description": record.description,
                "video_url": record.video_url,
                "visibility": record.visibility,
                "status": record.status,
                "publish_time": record.publish_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as exc:
        db.rollback()
        logger.exception("Publish video failed")
        return error(f"Publish failed: {exc}", code=400)


@router.post("/{video_id}/private", summary="Set video to private")
def make_private(
    video_id: int,
    user_id: int = Form(default=1, description="User ID"),
    db: Session = Depends(get_db),
):
    """
    Set public video back to private.
    """
    try:
        record = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.id == video_id
        ).first()

        if not record:
            return error("Video not found", code=404)

        if record.user_id != user_id:
            return error("Permission denied", code=403)

        record.visibility = "private"
        record.status = "uploaded"
        record.update_time = datetime.now()
        db.commit()

        return success(
            message="Video set to private",
            data={
                "id": record.id,
                "visibility": record.visibility,
                "status": record.status,
            }
        )
    except Exception as exc:
        db.rollback()
        logger.exception("Set private failed")
        return error(f"Operation failed: {exc}", code=400)


@router.delete("/{video_id}", summary="Delete video")
def delete_video(
    video_id: int,
    user_id: int = Query(default=1, description="User ID"),
    db: Session = Depends(get_db),
):
    """
    Soft delete video (mark as deleted, file is not actually removed).
    """
    try:
        record = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.id == video_id
        ).first()

        if not record:
            return error("Video not found", code=404)

        if record.user_id != user_id:
            return error("Permission denied", code=403)

        record.status = "deleted"
        record.update_time = datetime.now()
        db.commit()

        return success(message="Delete successful")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete video failed")
        return error(f"Delete failed: {exc}", code=400)
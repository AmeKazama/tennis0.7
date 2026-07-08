import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import engine, get_db
from db_models.training_video_record import TrainingVideoRecord
from db_models.user_profile import UserProfile
from utils.response import error, success

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/videos", tags=["videos"])

VIDEO_DIR = Path("uploads/videos")
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".webm"}
_table_ready = False


def _ensure_table() -> None:
    global _table_ready
    if _table_ready:
        return
    TrainingVideoRecord.__table__.create(bind=engine, checkfirst=True)
    UserProfile.__table__.create(bind=engine, checkfirst=True)
    _table_ready = True


def _public_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return path.replace("\\", "/")


def _serialize_video(record: TrainingVideoRecord, profile: Optional[UserProfile] = None) -> dict:
    create_time = record.create_time.strftime("%Y-%m-%d %H:%M:%S") if record.create_time else None
    update_time = record.update_time.strftime("%Y-%m-%d %H:%M:%S") if record.update_time else None
    publish_time = record.publish_time.strftime("%Y-%m-%d %H:%M:%S") if record.publish_time else None
    nickname = profile.nickname if profile and profile.nickname else f"用户{record.user_id}"

    return {
        "id": record.id,
        "user_id": record.user_id,
        "nickname": nickname,
        "avatar_url": profile.avatar_url if profile else None,
        "title": record.title or "网球训练视频",
        "description": record.description,
        "desc": record.description or record.title or "分享一次新的网球训练",
        "video_url": _public_url(record.video_url),
        "src": _public_url(record.video_url),
        "cover_url": _public_url(record.cover_url),
        "cover": _public_url(record.cover_url),
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
        "publish_time": publish_time,
        "create_time": create_time,
        "update_time": update_time,
        "type": "video",
    }


@router.post("/upload")
async def upload_private_video(
    file: UploadFile = File(...),
    user_id: int = Form(1),
    title: str | None = Form(None),
    description: str | None = Form(None),
    source_type: str = Form("upload"),
    cover_url: str | None = Form(None),
    duration_seconds: float | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    上传到用户私人视频库。默认不会进入首页公开流。
    首页只展示 visibility=public 且 status=published 的视频。
    """
    _ensure_table()

    if file is None or not file.filename:
        return error("视频文件不能为空")

    ext = Path(file.filename).suffix.lower() or ".mp4"
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return error(f"不支持的视频格式：{ext}")

    video_bytes = await file.read()
    if not video_bytes:
        return error("视频文件为空")

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
    save_path = VIDEO_DIR / filename
    save_path.write_bytes(video_bytes)

    video_url = f"/uploads/videos/{filename}"
    record = TrainingVideoRecord(
        user_id=user_id,
        title=title or Path(file.filename).stem or "网球训练视频",
        description=description,
        video_url=video_url,
        cover_url=cover_url,
        duration_seconds=duration_seconds,
        file_size=len(video_bytes),
        source_type=source_type or "upload",
        visibility="private",
        status="uploaded",
    )

    try:
        db.add(record)

        profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if profile is None:
            profile = UserProfile(id=user_id)
            db.add(profile)
            db.flush()
        profile.training_video_count = int(profile.training_video_count or 0) + 1
        profile.update_time = datetime.now()

        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        logger.exception("Save uploaded video failed")
        raise HTTPException(status_code=500, detail=f"视频记录保存失败：{exc}") from exc

    return success(message="上传成功，已保存到私人库", data=_serialize_video(record, profile))


@router.get("/my")
def list_my_videos(
    user_id: int = 1,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    _ensure_table()
    page = max(1, page)
    page_size = max(1, min(page_size, 50))

    query = db.query(TrainingVideoRecord).filter(
        TrainingVideoRecord.user_id == user_id,
        TrainingVideoRecord.status != "deleted",
    )
    total = query.count()
    records = (
        query.order_by(TrainingVideoRecord.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    return success(
        message="查询成功",
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [_serialize_video(record, profile) for record in records],
        },
    )


@router.post("/{video_id}/publish")
def publish_video(
    video_id: int,
    user_id: int = Form(1),
    content: str | None = Form(None),
    db: Session = Depends(get_db),
):
    _ensure_table()
    record = (
        db.query(TrainingVideoRecord)
        .filter(
            TrainingVideoRecord.id == video_id,
            TrainingVideoRecord.user_id == user_id,
            TrainingVideoRecord.status != "deleted",
        )
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="视频不存在或无权发布")

    if content:
        record.description = content
    record.visibility = "public"
    record.status = "published"
    record.publish_time = datetime.now()
    record.update_time = datetime.now()

    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if profile is not None:
        profile.post_count = int(profile.post_count or 0) + 1
        profile.update_time = datetime.now()

    db.commit()
    db.refresh(record)

    return success(message="发布成功，公开视频流已可见", data=_serialize_video(record, profile))


@router.post("/{video_id}/private")
def set_video_private(
    video_id: int,
    user_id: int = Form(1),
    db: Session = Depends(get_db),
):
    _ensure_table()
    record = (
        db.query(TrainingVideoRecord)
        .filter(
            TrainingVideoRecord.id == video_id,
            TrainingVideoRecord.user_id == user_id,
            TrainingVideoRecord.status != "deleted",
        )
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="视频不存在或无权操作")

    record.visibility = "private"
    record.status = "uploaded"
    record.update_time = datetime.now()
    db.commit()
    db.refresh(record)

    return success(message="已设为私密", data=_serialize_video(record))

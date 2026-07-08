import os
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import engine, get_db
from db_models.training_video_record import TrainingVideoRecord
from db_models.user_profile import UserProfile

router = APIRouter(tags=["feed"])

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = BASE_DIR / "static"
VIDEO_DIR = STATIC_ROOT / "videos"
COVER_DIR = STATIC_ROOT / "covers"
DEFAULT_PAGE_SIZE = 3
_table_ready = False


def register_feed_static(app):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


def _ensure_video_table() -> None:
    global _table_ready
    if _table_ready:
        return
    TrainingVideoRecord.__table__.create(bind=engine, checkfirst=True)
    UserProfile.__table__.create(bind=engine, checkfirst=True)
    _table_ready = True


def _serialize_feed_video(record: TrainingVideoRecord, profile: UserProfile | None = None):
    nickname = profile.nickname if profile and profile.nickname else f"用户{record.user_id}"
    publish_time = record.publish_time.strftime("%Y-%m-%d %H:%M:%S") if record.publish_time else None

    return {
        "id": record.id,
        "user_id": record.user_id,
        "nickname": nickname,
        "author": f"@{nickname}",
        "avatar_url": profile.avatar_url if profile else None,
        "title": record.title or "网球训练视频",
        "desc": record.description or record.title or "分享一次新的网球训练",
        "video_url": record.video_url,
        "src": record.video_url,
        "cover_url": record.cover_url,
        "cover": record.cover_url,
        "like_count": record.like_count,
        "comment_count": record.comment_count,
        "favorite_count": record.favorite_count,
        "view_count": record.view_count,
        "publish_time": publish_time,
        "type": "video",
        "source": "database",
    }


def scan_video_resource():
    video_list = []

    if not VIDEO_DIR.exists():
        return video_list

    for file_name in os.listdir(VIDEO_DIR):
        if not file_name.lower().endswith(".mp4"):
            continue

        file_no = file_name[:-4]
        cover_name = f"{file_no}.png"
        cover_full_path = COVER_DIR / cover_name
        if not cover_full_path.exists():
            continue

        video_item = {
            "id": int(file_no) if file_no.isdigit() else len(video_list) + 1,
            "title": f"Tennis lesson {file_no}",
            "desc": "Tennis training video",
            "video_url": f"/static/videos/{file_name}",
            "cover_url": f"/static/covers/{cover_name}",
        }
        video_list.append(video_item)

    video_list.sort(key=lambda x: x["id"])
    return video_list


@router.get("/api/feed/list", summary="Short video feed list")
def get_feed_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, gt=0),
    db: Session = Depends(get_db),
):
    try:
        _ensure_video_table()
        query = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.visibility == "public",
            TrainingVideoRecord.status == "published",
        )
        total = query.count()
        records = (
            query.order_by(
                TrainingVideoRecord.publish_time.desc(),
                TrainingVideoRecord.create_time.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        if records:
            profiles = {
                profile.id: profile
                for profile in db.query(UserProfile).filter(
                    UserProfile.id.in_([record.user_id for record in records])
                ).all()
            }
            return {
                "code": 200,
                "msg": "success",
                "message": "success",
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": [
                    _serialize_feed_video(record, profiles.get(record.user_id))
                    for record in records
                ],
            }
    except Exception:
        # 数据库未配置或表结构未同步时，继续使用静态资源兜底，避免首页空白。
        pass

    all_video_data = scan_video_resource()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    return {
        "code": 200,
        "msg": "success",
        "total": len(all_video_data),
        "page": page,
        "page_size": page_size,
        "data": all_video_data[start_idx:end_idx],
    }

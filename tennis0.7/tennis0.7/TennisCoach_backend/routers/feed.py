import os
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from db_models.training_video_record import TrainingVideoRecord
from db_models.user_profile import UserProfile

router = APIRouter(tags=["feed"])

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = BASE_DIR / "static"
VIDEO_DIR = STATIC_ROOT / "videos"
COVER_DIR = STATIC_ROOT / "covers"
DEFAULT_PAGE_SIZE = 10


def register_feed_static(app):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


def scan_video_resource():
    """扫描本地静态视频文件，作为兜底数据"""
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

        video_list.append({
            "id": int(file_no) if file_no.isdigit() else len(video_list) + 1,
            "nickname": "网球训练者",
            "avatar_url": None,
            "title": f"Tennis lesson {file_no}",
            "desc": "Tennis training video",
            "src": f"/static/videos/{file_name}",
            "video_url": f"/static/videos/{file_name}",
            "cover_url": f"/static/covers/{cover_name}",
            "like_count": 0,
            "comment_count": 0,
            "favorite_count": 0,
            "view_count": 0,
            "source": "static_fallback",
        })

    video_list.sort(key=lambda x: x["id"])
    return video_list


@router.get("/api/feed/list", summary="短视频信息流")
def get_feed_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, gt=0, le=50),
    db: Session = Depends(get_db),
):
    """首页短视频 feed 流，优先返回数据库中的公开视频，无数据时降级到静态文件兜底"""
    try:
        query = db.query(TrainingVideoRecord).filter(
            TrainingVideoRecord.visibility == "public",
            TrainingVideoRecord.status == "published"
        )
        total = query.count()

        records = query.order_by(
            desc(TrainingVideoRecord.publish_time),
            desc(TrainingVideoRecord.create_time)
        ).offset((page - 1) * page_size).limit(page_size).all()

        if records:
            user_ids = list(set(r.user_id for r in records))
            users = db.query(UserProfile).filter(UserProfile.id.in_(user_ids)).all()
            user_map = {u.id: u for u in users}

            data = []
            for r in records:
                user = user_map.get(r.user_id)
                data.append({
                    "id": r.id,
                    "user_id": r.user_id,
                    "nickname": user.nickname if user else f"用户{r.user_id}",
                    "avatar_url": user.avatar_url if user else None,
                    "title": r.title,
                    "desc": getattr(r, "description", None) or "",
                    "src": r.video_url,
                    "video_url": r.video_url,
                    "cover_url": r.cover_url,
                    "like_count": r.like_count if hasattr(r, "like_count") else 0,
                    "comment_count": r.comment_count if hasattr(r, "comment_count") else 0,
                    "favorite_count": r.favorite_count if hasattr(r, "favorite_count") else 0,
                    "view_count": r.view_count if hasattr(r, "view_count") else 0,
                    "publish_time": r.publish_time.strftime("%Y-%m-%d %H:%M:%S") if r.publish_time else None,
                    "source": "database",
                })

            return {
                "code": 200,
                "msg": "success",
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": data,
            }

        static_data = scan_video_resource()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        return {
            "code": 200,
            "msg": "success",
            "total": len(static_data),
            "page": page,
            "page_size": page_size,
            "data": static_data[start_idx:end_idx],
        }

    except Exception as e:
        static_data = scan_video_resource()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        return {
            "code": 200,
            "msg": "success",
            "total": len(static_data),
            "page": page,
            "page_size": page_size,
            "data": static_data[start_idx:end_idx],
            "warning": f"数据库暂不可用，使用静态数据兜底: {str(e)}",
        }
import os
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.staticfiles import StaticFiles


router = APIRouter(tags=["feed"])

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = BASE_DIR / "static"
VIDEO_DIR = STATIC_ROOT / "videos"
COVER_DIR = STATIC_ROOT / "covers"
DEFAULT_PAGE_SIZE = 3


def register_feed_static(app):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


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
):
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

from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.community_post import CommunityPost
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/community_post", tags=["community_post"])


@router.post("/")
def create_post(
    user_id: int,
    content: Optional[str] = None,
    media_type: Optional[str] = None,
    media_url: Optional[str] = None,
    cover_url: Optional[str] = None,
    visibility: str = "public",
    db: Session = Depends(get_db),
):
    try:
        post = CommunityPost(
            user_id=user_id,
            content=content,
            media_type=media_type,
            media_url=media_url,
            cover_url=cover_url,
            visibility=visibility,
            status="published",
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return success(message="发布成功", data={"id": post.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create post failed")
        return error(f"发布失败：{exc}", code=400)


@router.get("/list")
def list_posts(
    user_id: Optional[int] = None,
    status: Optional[str] = "published",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(CommunityPost)
        if user_id:
            query = query.filter(CommunityPost.user_id == user_id)
        if status:
            query = query.filter(CommunityPost.status == status)
        posts = query.order_by(
            CommunityPost.create_time.desc()
        ).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "content": p.content,
                    "media_type": p.media_type,
                    "media_url": p.media_url,
                    "cover_url": p.cover_url,
                    "like_count": p.like_count,
                    "comment_count": p.comment_count,
                    "favorite_count": p.favorite_count,
                    "create_time": p.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for p in posts
            ]
        )
    except Exception as exc:
        logger.exception("List posts failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    try:
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if not post:
            return error("帖子不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": post.id,
                "user_id": post.user_id,
                "content": post.content,
                "media_type": post.media_type,
                "media_url": post.media_url,
                "cover_url": post.cover_url,
                "like_count": post.like_count,
                "comment_count": post.comment_count,
                "favorite_count": post.favorite_count,
                "visibility": post.visibility,
                "status": post.status,
                "create_time": post.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as exc:
        logger.exception("Get post failed")
        return error(f"查询失败：{exc}", code=400)


@router.put("/{post_id}")
def update_post(
    post_id: int,
    content: Optional[str] = None,
    media_type: Optional[str] = None,
    media_url: Optional[str] = None,
    cover_url: Optional[str] = None,
    visibility: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if not post:
            return error("帖子不存在", code=404)

        if content is not None:
            post.content = content
        if media_type is not None:
            post.media_type = media_type
        if media_url is not None:
            post.media_url = media_url
        if cover_url is not None:
            post.cover_url = cover_url
        if visibility is not None:
            post.visibility = visibility
        if status is not None:
            post.status = status

        post.update_time = datetime.now()
        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update post failed")
        return error(f"更新失败：{exc}", code=400)


@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    try:
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if not post:
            return error("帖子不存在", code=404)
        db.delete(post)
        db.commit()
        return success(message="删除成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete post failed")
        return error(f"删除失败：{exc}", code=400)


@router.post("/{post_id}/like")
def like_post(post_id: int, db: Session = Depends(get_db)):
    try:
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if not post:
            return error("帖子不存在", code=404)
        post.like_count += 1
        post.update_time = datetime.now()
        db.commit()
        return success(message="点赞成功", data={"like_count": post.like_count})
    except Exception as exc:
        db.rollback()
        logger.exception("Like post failed")
        return error(f"点赞失败：{exc}", code=400)

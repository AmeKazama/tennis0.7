from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.user_follow import UserFollow
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user_follow", tags=["user_follow"])


# ========== 关注用户 ==========

@router.post("/")
def follow_user(
    follower_id: int,
    following_id: int,
    db: Session = Depends(get_db),
):
    try:
        # 检查是否已关注
        existing = db.query(UserFollow).filter(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id
        ).first()
        if existing:
            return error("已关注该用户", code=400)

        follow = UserFollow(
            follower_id=follower_id,
            following_id=following_id,
            create_time=datetime.now()
        )
        db.add(follow)
        db.commit()
        db.refresh(follow)
        return success(message="关注成功", data={"id": follow.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Follow user failed")
        return error(f"关注失败：{exc}", code=400)


# ========== 取消关注 ==========

@router.delete("/")
def unfollow_user(
    follower_id: int,
    following_id: int,
    db: Session = Depends(get_db),
):
    try:
        follow = db.query(UserFollow).filter(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id
        ).first()
        if not follow:
            return error("未关注该用户", code=404)

        db.delete(follow)
        db.commit()
        return success(message="取消关注成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Unfollow user failed")
        return error(f"取消关注失败：{exc}", code=400)


# ========== 获取关注列表（我关注的） ==========

@router.get("/following")
def get_following_list(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(UserFollow).filter(UserFollow.follower_id == user_id)
        total = query.count()
        follows = query.order_by(UserFollow.create_time.desc()).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": f.id,
                    "following_id": f.following_id,
                    "create_time": f.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for f in follows
            ],
            total=total,
            page=page,
            size=size
        )
    except Exception as exc:
        logger.exception("Get following list failed")
        return error(f"查询失败：{exc}", code=400)


# ========== 获取粉丝列表（关注我的） ==========

@router.get("/followers")
def get_followers_list(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(UserFollow).filter(UserFollow.following_id == user_id)
        total = query.count()
        follows = query.order_by(UserFollow.create_time.desc()).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": f.id,
                    "follower_id": f.follower_id,
                    "create_time": f.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for f in follows
            ],
            total=total,
            page=page,
            size=size
        )
    except Exception as exc:
        logger.exception("Get followers list failed")
        return error(f"查询失败：{exc}", code=400)


# ========== 检查是否已关注 ==========

@router.get("/check")
def check_follow(
    follower_id: int,
    following_id: int,
    db: Session = Depends(get_db),
):
    try:
        follow = db.query(UserFollow).filter(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id
        ).first()
        return success(message="查询成功", data={"is_following": follow is not None})
    except Exception as exc:
        logger.exception("Check follow failed")
        return error(f"查询失败：{exc}", code=400)
from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.user_profile import UserProfile
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user_profile", tags=["user_profile"])


# ========== 增（Create） ==========

@router.post("/")
def create_user_profile(
    nickname: Optional[str] = "网球训练者",
    avatar_url: Optional[str] = None,
    bio: Optional[str] = None,
    region: Optional[str] = None,
    city: Optional[str] = None,
    club_name: Optional[str] = None,
    tennis_level: Optional[str] = None,
    dominant_hand: Optional[str] = None,
    gender: Optional[str] = None,
    birthday: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        # 解析 birthday
        birthday_date = None
        if birthday:
            birthday_date = datetime.strptime(birthday, "%Y-%m-%d").date()

        user = UserProfile(
            nickname=nickname,
            avatar_url=avatar_url,
            bio=bio,
            region=region,
            city=city,
            club_name=club_name,
            tennis_level=tennis_level,
            dominant_hand=dominant_hand,
            gender=gender,
            birthday=birthday_date,
            phone=phone,
            email=email,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return success(message="创建成功", data={"id": user.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create user profile failed, phone=%s", phone)
        return error(f"创建失败：{exc}", code=400)


# ========== 查（Read） ==========

@router.get("/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            return error("用户不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": user.id,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "region": user.region,
                "city": user.city,
                "club_name": user.club_name,
                "tennis_level": user.tennis_level,
                "dominant_hand": user.dominant_hand,
                "gender": user.gender,
                "birthday": user.birthday.strftime("%Y-%m-%d") if user.birthday else None,
                "phone": user.phone,
                "email": user.email,
                "followers_count": user.followers_count,
                "following_count": user.following_count,
                "favorite_count": user.favorite_count,
                "post_count": user.post_count,
                "training_video_count": user.training_video_count,
                "analysis_count": user.analysis_count,
                "device_count": user.device_count,
                "badge_count": user.badge_count,
                "create_time": user.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "update_time": user.update_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except Exception as exc:
        logger.exception("Get user profile failed, userId=%s", user_id)
        return error(f"查询失败：{exc}", code=400)


# ========== 列表（List） ==========

@router.get("/list")
def list_user_profiles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(UserProfile)
        if keyword:
            query = query.filter(
                UserProfile.nickname.like(f"%{keyword}%") |
                UserProfile.phone.like(f"%{keyword}%")
            )
        total = query.count()
        users = query.order_by(UserProfile.id.desc()).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": user.id,
                    "nickname": user.nickname,
                    "avatar_url": user.avatar_url,
                    "phone": user.phone,
                    "email": user.email,
                    "tennis_level": user.tennis_level,
                }
                for user in users
            ],
            total=total,
            page=page,
            size=size,
        )
    except Exception as exc:
        logger.exception("List user profiles failed")
        return error(f"查询失败：{exc}", code=400)


# ========== 改（Update） ==========

@router.put("/{user_id}")
def update_user_profile(
    user_id: int,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None,
    bio: Optional[str] = None,
    region: Optional[str] = None,
    city: Optional[str] = None,
    club_name: Optional[str] = None,
    tennis_level: Optional[str] = None,
    dominant_hand: Optional[str] = None,
    gender: Optional[str] = None,
    birthday: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            return error("用户不存在", code=404)

        if nickname is not None:
            user.nickname = nickname
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if bio is not None:
            user.bio = bio
        if region is not None:
            user.region = region
        if city is not None:
            user.city = city
        if club_name is not None:
            user.club_name = club_name
        if tennis_level is not None:
            user.tennis_level = tennis_level
        if dominant_hand is not None:
            user.dominant_hand = dominant_hand
        if gender is not None:
            user.gender = gender
        if birthday is not None:
            user.birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
        if phone is not None:
            user.phone = phone
        if email is not None:
            user.email = email

        user.update_time = datetime.now()
        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update user profile failed, userId=%s", user_id)
        return error(f"更新失败：{exc}", code=400)


# ========== 删（Delete） ==========

@router.delete("/{user_id}")
def delete_user_profile(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            return error("用户不存在", code=404)
        db.delete(user)
        db.commit()
        return success(message="删除成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete user profile failed, userId=%s", user_id)
        return error(f"删除失败：{exc}", code=400)
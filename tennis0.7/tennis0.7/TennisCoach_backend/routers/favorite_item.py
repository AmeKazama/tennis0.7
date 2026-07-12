from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.favorite_item import FavoriteItem
from db_models.favorite_folder import FavoriteFolder
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/favorite_item", tags=["favorite_item"])


@router.post("/")
def add_favorite(
    user_id: int,
    target_type: str,
    target_id: int,
    folder_id: Optional[int] = None,
    title: Optional[str] = None,
    poster_url: Optional[str] = None,
    author_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        # 检查是否已收藏
        existing = db.query(FavoriteItem).filter(
            FavoriteItem.user_id == user_id,
            FavoriteItem.target_type == target_type,
            FavoriteItem.target_id == target_id
        ).first()
        if existing:
            return error("已收藏该项目", code=400)

        # 如果指定了收藏夹，检查是否存在
        if folder_id:
            folder = db.query(FavoriteFolder).filter(
                FavoriteFolder.id == folder_id,
                FavoriteFolder.user_id == user_id
            ).first()
            if not folder:
                return error("收藏夹不存在", code=404)

        item = FavoriteItem(
            user_id=user_id,
            folder_id=folder_id,
            target_type=target_type,
            target_id=target_id,
            title=title,
            poster_url=poster_url,
            author_name=author_name,
            create_time=datetime.now()
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        # 更新收藏夹计数
        if folder_id:
            folder = db.query(FavoriteFolder).filter(FavoriteFolder.id == folder_id).first()
            if folder:
                folder.item_count += 1
                folder.update_time = datetime.now()
                db.commit()

        return success(message="收藏成功", data={"id": item.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Add favorite failed")
        return error(f"收藏失败：{exc}", code=400)


@router.get("/list")
def list_favorites(
    user_id: int,
    target_type: Optional[str] = None,
    folder_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(FavoriteItem).filter(FavoriteItem.user_id == user_id)
        if target_type:
            query = query.filter(FavoriteItem.target_type == target_type)
        if folder_id is not None:
            query = query.filter(FavoriteItem.folder_id == folder_id)
        total = query.count()
        items = query.order_by(
            FavoriteItem.create_time.desc()
        ).offset((page - 1) * size).limit(size).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": i.id,
                    "folder_id": i.folder_id,
                    "target_type": i.target_type,
                    "target_id": i.target_id,
                    "title": i.title,
                    "poster_url": i.poster_url,
                    "author_name": i.author_name,
                    "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for i in items
            ],
            total=total,
            page=page,
            size=size
        )
    except Exception as exc:
        logger.exception("List favorites failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/check")
def check_favorite(
    user_id: int,
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db),
):
    try:
        item = db.query(FavoriteItem).filter(
            FavoriteItem.user_id == user_id,
            FavoriteItem.target_type == target_type,
            FavoriteItem.target_id == target_id
        ).first()
        return success(
            message="查询成功",
            data={"is_favorited": item is not None}
        )
    except Exception as exc:
        logger.exception("Check favorite failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/{favorite_id}")
def get_favorite(favorite_id: int, db: Session = Depends(get_db)):
    try:
        item = db.query(FavoriteItem).filter(FavoriteItem.id == favorite_id).first()
        if not item:
            return error("收藏记录不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": item.id,
                "user_id": item.user_id,
                "folder_id": item.folder_id,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "title": item.title,
                "poster_url": item.poster_url,
                "author_name": item.author_name,
                "create_time": item.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as exc:
        logger.exception("Get favorite failed")
        return error(f"查询失败：{exc}", code=400)


@router.delete("/{favorite_id}")
def remove_favorite(favorite_id: int, db: Session = Depends(get_db)):
    try:
        item = db.query(FavoriteItem).filter(FavoriteItem.id == favorite_id).first()
        if not item:
            return error("收藏记录不存在", code=404)

        folder_id = item.folder_id
        db.delete(item)
        db.commit()

        # 更新收藏夹计数
        if folder_id:
            folder = db.query(FavoriteFolder).filter(FavoriteFolder.id == folder_id).first()
            if folder and folder.item_count > 0:
                folder.item_count -= 1
                folder.update_time = datetime.now()
                db.commit()

        return success(message="取消收藏成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Remove favorite failed")
        return error(f"取消收藏失败：{exc}", code=400)
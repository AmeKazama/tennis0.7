from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.favorite_folder import FavoriteFolder
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/favorite_folder", tags=["favorite_folder"])


@router.post("/")
def create_folder(
    user_id: int,
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        folder = FavoriteFolder(
            user_id=user_id,
            name=name,
            description=description,
            item_count=0,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return success(message="创建成功", data={"id": folder.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Create folder failed")
        return error(f"创建失败：{exc}", code=400)


@router.get("/list")
def list_folders(user_id: int, db: Session = Depends(get_db)):
    try:
        folders = db.query(FavoriteFolder).filter(
            FavoriteFolder.user_id == user_id
        ).order_by(FavoriteFolder.create_time.desc()).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": f.id,
                    "name": f.name,
                    "description": f.description,
                    "item_count": f.item_count,
                    "create_time": f.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for f in folders
            ]
        )
    except Exception as exc:
        logger.exception("List folders failed")
        return error(f"查询失败：{exc}", code=400)


@router.get("/{folder_id}")
def get_folder(folder_id: int, db: Session = Depends(get_db)):
    try:
        folder = db.query(FavoriteFolder).filter(FavoriteFolder.id == folder_id).first()
        if not folder:
            return error("收藏夹不存在", code=404)
        return success(
            message="查询成功",
            data={
                "id": folder.id,
                "user_id": folder.user_id,
                "name": folder.name,
                "description": folder.description,
                "item_count": folder.item_count,
                "create_time": folder.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as exc:
        logger.exception("Get folder failed")
        return error(f"查询失败：{exc}", code=400)


@router.put("/{folder_id}")
def update_folder(
    folder_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        folder = db.query(FavoriteFolder).filter(FavoriteFolder.id == folder_id).first()
        if not folder:
            return error("收藏夹不存在", code=404)

        if name is not None:
            folder.name = name
        if description is not None:
            folder.description = description

        folder.update_time = datetime.now()
        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update folder failed")
        return error(f"更新失败：{exc}", code=400)


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    try:
        folder = db.query(FavoriteFolder).filter(FavoriteFolder.id == folder_id).first()
        if not folder:
            return error("收藏夹不存在", code=404)
        db.delete(folder)
        db.commit()
        return success(message="删除成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Delete folder failed")
        return error(f"删除失败：{exc}", code=400)
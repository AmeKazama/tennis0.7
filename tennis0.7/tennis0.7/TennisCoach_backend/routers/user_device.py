from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from db_models.user_device import UserDevice
from utils.response import success, error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user_device", tags=["user_device"])


# ========== 绑定设备 ==========

@router.post("/")
def bind_device(
    user_id: int,
    device_name: str,
    device_type: Optional[str] = None,
    device_sn: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        # 检查该设备SN是否已被绑定
        if device_sn:
            existing = db.query(UserDevice).filter(
                UserDevice.device_sn == device_sn,
                UserDevice.bind_status == "active"
            ).first()
            if existing:
                return error("该设备已被其他用户绑定", code=400)

        device = UserDevice(
            user_id=user_id,
            device_name=device_name,
            device_type=device_type,
            device_sn=device_sn,
            bind_status="active",
            last_active_time=datetime.now(),
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return success(message="设备绑定成功", data={"id": device.id})
    except Exception as exc:
        db.rollback()
        logger.exception("Bind device failed")
        return error(f"绑定失败：{exc}", code=400)


# ========== 解绑设备 ==========

@router.put("/{device_id}/unbind")
def unbind_device(device_id: int, db: Session = Depends(get_db)):
    try:
        device = db.query(UserDevice).filter(UserDevice.id == device_id).first()
        if not device:
            return error("设备不存在", code=404)

        device.bind_status = "inactive"
        device.update_time = datetime.now()
        db.commit()
        return success(message="设备解绑成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Unbind device failed")
        return error(f"解绑失败：{exc}", code=400)


# ========== 获取用户设备列表 ==========

@router.get("/list")
def list_user_devices(
    user_id: int,
    status: Optional[str] = Query(None, description="active/inactive/unbound"),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(UserDevice).filter(UserDevice.user_id == user_id)
        if status:
            query = query.filter(UserDevice.bind_status == status)
        devices = query.order_by(UserDevice.create_time.desc()).all()
        return success(
            message="查询成功",
            data=[
                {
                    "id": d.id,
                    "user_id": d.user_id,
                    "device_name": d.device_name,
                    "device_type": d.device_type,
                    "device_sn": d.device_sn,
                    "bind_status": d.bind_status,
                    "last_active_time": d.last_active_time.strftime("%Y-%m-%d %H:%M:%S") if d.last_active_time else None,
                    "create_time": d.create_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for d in devices
            ]
        )
    except Exception as exc:
        logger.exception("List user devices failed")
        return error(f"查询失败：{exc}", code=400)


# ========== 更新设备活跃时间 ==========

@router.put("/{device_id}/active")
def update_device_active(device_id: int, db: Session = Depends(get_db)):
    try:
        device = db.query(UserDevice).filter(UserDevice.id == device_id).first()
        if not device:
            return error("设备不存在", code=404)

        device.last_active_time = datetime.now()
        device.update_time = datetime.now()
        db.commit()
        return success(message="更新成功")
    except Exception as exc:
        db.rollback()
        logger.exception("Update device active failed")
        return error(f"更新失败：{exc}", code=400)
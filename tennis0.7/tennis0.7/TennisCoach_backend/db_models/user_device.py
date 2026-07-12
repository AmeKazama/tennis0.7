from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserDevice(Base):
    __tablename__ = "user_device"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    device_name = Column(String(120), nullable=False, comment="设备名称")
    device_type = Column(String(50), nullable=True, comment="设备类型：watch/sensor/racket/phone")
    device_sn = Column(String(120), nullable=True, comment="设备序列号")
    bind_status = Column(String(30), nullable=False, default="active", comment="绑定状态：active/inactive/unbound")
    last_active_time = Column(DateTime, nullable=True, comment="最近活跃时间")
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment="绑定时间")
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
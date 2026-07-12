from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserBadge(Base):
    __tablename__ = "user_badge"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    badge_code = Column(String(80), nullable=False, comment="勋章编码")
    badge_name = Column(String(120), nullable=False, comment="勋章名称")
    badge_icon = Column(String(500), nullable=True, comment="勋章图标URL")
    description = Column(String(255), nullable=True, comment="勋章描述")
    earned_time = Column(DateTime, nullable=False, default=datetime.now, comment="获得时间")
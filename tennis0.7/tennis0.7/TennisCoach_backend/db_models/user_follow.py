from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserFollow(Base):
    __tablename__ = "user_follow"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    follower_id = Column(BigInteger, nullable=False, comment="关注者用户ID")
    following_id = Column(BigInteger, nullable=False, comment="被关注者用户ID")
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment="关注时间")
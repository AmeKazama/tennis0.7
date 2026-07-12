from sqlalchemy import Column, BigInteger, String, Integer, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    nickname = Column(String(80), nullable=False, default="网球训练者", comment="用户昵称")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    bio = Column(String(255), nullable=True, comment="个人简介")
    region = Column(String(100), nullable=True, comment="地区/省份")
    city = Column(String(100), nullable=True, comment="城市")
    club_name = Column(String(100), nullable=True, comment="常去俱乐部或球场")
    tennis_level = Column(String(50), nullable=True, comment="网球水平")
    dominant_hand = Column(String(20), nullable=True, comment="持拍手")
    gender = Column(String(20), nullable=True, comment="性别")
    birthday = Column(Date, nullable=True, comment="生日")
    phone = Column(String(30), nullable=True, comment="手机号")
    email = Column(String(120), nullable=True, comment="邮箱")
    followers_count = Column(Integer, nullable=False, default=0, comment="粉丝数")
    following_count = Column(Integer, nullable=False, default=0, comment="关注数")
    favorite_count = Column(Integer, nullable=False, default=0, comment="收藏数")
    post_count = Column(Integer, nullable=False, default=0, comment="发布数")
    training_video_count = Column(Integer, nullable=False, default=0, comment="训练视频数量")
    analysis_count = Column(Integer, nullable=False, default=0, comment="动作分析次数")
    device_count = Column(Integer, nullable=False, default=0, comment="绑定设备数")
    badge_count = Column(Integer, nullable=False, default=0, comment="荣誉勋章数")
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
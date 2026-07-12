from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class TrainingVideoRecord(Base):
    __tablename__ = "training_video_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="上传用户ID")
    title = Column(String(120), nullable=True, comment="视频标题")
    description = Column(Text, nullable=True, comment="视频描述/发布文案")
    video_url = Column(String(500), nullable=False, comment="视频URL或存储路径")
    cover_url = Column(String(500), nullable=True, comment="封面URL")
    duration_seconds = Column(Float, nullable=True, comment="视频时长，秒")
    file_size = Column(BigInteger, nullable=True, comment="文件大小，字节")
    source_type = Column(String(30), nullable=False, default="upload", comment="来源：camera/album/upload/analysis")
    analysis_id = Column(String(64), nullable=True, index=True, comment="关联动作分析任务ID")
    shot_type = Column(String(40), nullable=True, index=True, comment="主要动作类型")
    score = Column(Float, nullable=True, comment="关联分析评分，0-100")
    visibility = Column(String(20), nullable=False, default="private", index=True, comment="private/public/friends")
    status = Column(String(20), nullable=False, default="uploaded", index=True, comment="uploaded/published/deleted")
    like_count = Column(Integer, nullable=False, default=0, comment="点赞数")
    comment_count = Column(Integer, nullable=False, default=0, comment="评论数")
    favorite_count = Column(Integer, nullable=False, default=0, comment="收藏数")
    view_count = Column(Integer, nullable=False, default=0, comment="播放/浏览数")
    publish_time = Column(DateTime, nullable=True, index=True, comment="发布时间")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

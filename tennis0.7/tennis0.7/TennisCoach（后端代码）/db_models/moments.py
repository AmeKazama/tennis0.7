"""
朋友圈数据模型
包含动态、点赞、评论、分享等表结构
"""
from sqlalchemy import BigInteger, Column, DateTime, String, Text, Integer, ForeignKey, Index
from sqlalchemy.sql import func

from database import Base


class Moments(Base):
    """朋友圈动态表"""
    __tablename__ = "moments"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    content = Column(Text, nullable=False, comment="动态内容")
    images = Column(Text, nullable=True, comment="图片JSON数组")
    video_url = Column(String(500), nullable=True, comment="视频URL")
    location = Column(String(200), nullable=True, comment="位置")
    likes_count = Column(Integer, default=0, comment="点赞数")
    comments_count = Column(Integer, default=0, comment="评论数")
    shares_count = Column(Integer, default=0, comment="分享数")
    is_top = Column(Integer, default=0, comment="是否置顶 0-否 1-是")
    visibility = Column(String(20), default="public", comment="可见性 public/friends/private")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class MomentLike(Base):
    """动态点赞表"""
    __tablename__ = "moment_likes"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    moment_id = Column(BigInteger, ForeignKey("moments.id", ondelete="CASCADE"), nullable=False, index=True, comment="动态ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="点赞时间")

    __table_args__ = (
        Index("idx_moment_user", "moment_id", "user_id", unique=True),
    )


class MomentComment(Base):
    """动态评论表"""
    __tablename__ = "moment_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    moment_id = Column(BigInteger, ForeignKey("moments.id", ondelete="CASCADE"), nullable=False, index=True, comment="动态ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    parent_id = Column(BigInteger, ForeignKey("moment_comments.id", ondelete="CASCADE"), nullable=True, comment="父评论ID（回复）")
    content = Column(Text, nullable=False, comment="评论内容")
    likes_count = Column(Integer, default=0, comment="点赞数")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="评论时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class MomentShare(Base):
    """动态分享表"""
    __tablename__ = "moment_shares"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    moment_id = Column(BigInteger, ForeignKey("moments.id", ondelete="CASCADE"), nullable=False, index=True, comment="动态ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    share_type = Column(String(20, collation="utf8mb4"), default="internal", comment="分享类型 internal/wechat/friend_circle")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="分享时间")


class MomentStats(Base):
    """朋友圈数据统计表（按日聚合）"""
    __tablename__ = "moment_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    stat_date = Column(DateTime, nullable=False, index=True, comment="统计日期")
    posts_count = Column(Integer, default=0, comment="发布动态数")
    likes_received = Column(Integer, default=0, comment="收到的点赞数")
    comments_received = Column(Integer, default=0, comment="收到的评论数")
    shares_received = Column(Integer, default=0, comment="收到的分享数")
    likes_given = Column(Integer, default=0, comment="发出的点赞数")
    comments_given = Column(Integer, default=0, comment="发出的评论数")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        Index("idx_user_date", "user_id", "stat_date", unique=True),
    )

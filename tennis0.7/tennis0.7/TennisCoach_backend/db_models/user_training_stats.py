from sqlalchemy import BigInteger, Column, DateTime, Float, Integer
from sqlalchemy.sql import func

from database import Base


class UserTrainingStats(Base):
    __tablename__ = "user_training_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, unique=True, index=True, comment="用户ID")
    training_count = Column(Integer, nullable=False, default=0, comment="总训练次数")
    total_duration_seconds = Column(Float, nullable=False, default=0, comment="累计训练时长，秒")
    avg_score = Column(Float, nullable=False, default=0, comment="总平均分")
    best_score = Column(Float, nullable=False, default=0, comment="历史最高分")
    forehand_count = Column(Integer, nullable=False, default=0, comment="正手片段数")
    backhand_count = Column(Integer, nullable=False, default=0, comment="反手片段数")
    serve_count = Column(Integer, nullable=False, default=0, comment="发球片段数")
    forehand_avg_score = Column(Float, nullable=False, default=0, comment="正手平均分")
    backhand_avg_score = Column(Float, nullable=False, default=0, comment="反手平均分")
    serve_avg_score = Column(Float, nullable=False, default=0, comment="发球平均分")
    last_training_time = Column(DateTime, nullable=True, comment="最近训练时间")
    consecutive_days = Column(Integer, nullable=False, default=0, comment="连续训练天数")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

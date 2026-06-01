from sqlalchemy import BigInteger, Column, Date, DateTime, String, Text
from sqlalchemy.sql import func

from database import Base


class BallDiary(Base):
    __tablename__ = "ball_diary"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    play_date = Column(Date, nullable=False, index=True, comment="打球日期")
    content = Column(Text, nullable=True, comment="语音识别后的文字内容")
    audio_url = Column(String(500), nullable=True, comment="音频文件路径")
    mood = Column(String(50), nullable=True, comment="心情")
    opponent = Column(String(100), nullable=True, comment="对手")
    score = Column(String(100), nullable=True, comment="比分")
    source_type = Column(String(20), nullable=False, default="voice", comment="来源类型")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

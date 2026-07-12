from sqlalchemy import Column, BigInteger, String, Double, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class TrainingVideoRecord(Base):
    __tablename__ = "training_video_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    title = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)
    cover_url = Column(String(500), nullable=True)
    duration_seconds = Column(Double, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    source_type = Column(String(30), nullable=False, default="upload")
    analysis_id = Column(String(64), nullable=True)
    shot_type = Column(String(40), nullable=True)
    score = Column(Double, nullable=True)
    visibility = Column(String(20), nullable=False, default="private")
    status = Column(String(20), nullable=False, default="uploaded")
    like_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    favorite_count = Column(Integer, nullable=False, default=0)
    view_count = Column(Integer, nullable=False, default=0)
    publish_time = Column(DateTime, nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
from sqlalchemy import Column, BigInteger, String, Integer, Double, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ActionAnalysisSegment(Base):
    __tablename__ = "action_analysis_segment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, nullable=True)
    analysis_id = Column(String(64), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    segment_index = Column(Integer, nullable=False, default=1)
    shot_type = Column(String(40), nullable=True)
    grade = Column(String(40), nullable=True)
    distance = Column(Double, nullable=True)
    score = Column(Double, nullable=True)
    best_match = Column(String(255), nullable=True)
    start_frame = Column(Integer, nullable=True)
    end_frame = Column(Integer, nullable=True)
    impact_frame = Column(Integer, nullable=True)
    fps = Column(Double, nullable=True)
    duration_seconds = Column(Double, nullable=True)
    pose_video_url = Column(String(500), nullable=True)
    standard_video_url = Column(String(500), nullable=True)
    worst_phase = Column(String(80), nullable=True)
    worst_keyframe = Column(String(80), nullable=True)
    phase_distances_json = Column(Text, nullable=True)
    keyframe_distances_json = Column(Text, nullable=True)
    top_issues_json = Column(Text, nullable=True)
    coach_advice = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
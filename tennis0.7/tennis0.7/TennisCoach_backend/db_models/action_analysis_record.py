from sqlalchemy import Column, BigInteger, String, Integer, Double, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ActionAnalysisRecord(Base):
    __tablename__ = "action_analysis_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(String(64), nullable=False, unique=True)
    user_id = Column(BigInteger, nullable=False)
    source_page = Column(String(80), nullable=True)
    file_name = Column(String(255), nullable=True)
    selected_player = Column(String(80), nullable=True)
    selected_stroke = Column(String(40), nullable=True)
    detected_shot_type = Column(String(40), nullable=True)
    best_match = Column(String(255), nullable=True)
    grade = Column(String(40), nullable=True)
    distance = Column(Double, nullable=True)
    training_duration_seconds = Column(Double, nullable=True)
    segment_count = Column(Integer, nullable=False, default=0)
    score = Column(Double, nullable=True)
    forehand_score = Column(Double, nullable=True)
    backhand_score = Column(Double, nullable=True)
    serve_score = Column(Double, nullable=True)
    forehand_count = Column(Integer, nullable=False, default=0)
    backhand_count = Column(Integer, nullable=False, default=0)
    serve_count = Column(Integer, nullable=False, default=0)
    pose_video_url = Column(String(500), nullable=True)
    standard_video_url = Column(String(500), nullable=True)
    worst_phase = Column(String(80), nullable=True)
    worst_keyframe = Column(String(80), nullable=True)
    report_text = Column(Text, nullable=True)
    coach_advice = Column(Text, nullable=True)
    segments_json = Column(Text, nullable=True)
    summary_json = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="success")
    error_message = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
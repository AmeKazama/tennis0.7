from sqlalchemy import BigInteger, Column, DateTime, Float, String, Text
from sqlalchemy.sql import func

from database import Base


class ActionAnalysisRecord(Base):
    __tablename__ = "action_analysis_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_id = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(BigInteger, nullable=False, default=1, index=True)
    source_page = Column(String(80), nullable=True)
    file_name = Column(String(255), nullable=True)
    selected_player = Column(String(80), nullable=True)
    selected_stroke = Column(String(40), nullable=True)
    detected_shot_type = Column(String(40), nullable=True, index=True)
    best_match = Column(String(255), nullable=True)
    grade = Column(String(40), nullable=True)
    distance = Column(Float, nullable=True)
    report_text = Column(Text, nullable=True)
    coach_advice = Column(Text, nullable=True)
    segments_json = Column(Text, nullable=True)
    summary_json = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="success", index=True)
    error_message = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False, server_default=func.now())
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

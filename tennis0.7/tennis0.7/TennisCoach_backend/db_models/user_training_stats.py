from sqlalchemy import Column, BigInteger, Integer, Double, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserTrainingStats(Base):
    __tablename__ = "user_training_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    training_count = Column(Integer, nullable=False, default=0)
    total_duration_seconds = Column(Double, nullable=False, default=0)
    avg_score = Column(Double, nullable=False, default=0)
    best_score = Column(Double, nullable=False, default=0)
    forehand_count = Column(Integer, nullable=False, default=0)
    backhand_count = Column(Integer, nullable=False, default=0)
    serve_count = Column(Integer, nullable=False, default=0)
    forehand_avg_score = Column(Double, nullable=False, default=0)
    backhand_avg_score = Column(Double, nullable=False, default=0)
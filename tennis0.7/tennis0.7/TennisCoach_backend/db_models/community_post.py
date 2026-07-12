from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CommunityPost(Base):
    __tablename__ = "community_post"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    content = Column(Text, nullable=True)
    media_type = Column(String(20), nullable=True)
    media_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    like_count = Column(BigInteger, nullable=False, default=0)
    comment_count = Column(BigInteger, nullable=False, default=0)
    favorite_count = Column(BigInteger, nullable=False, default=0)
    visibility = Column(String(20), nullable=False, default="public")
    status = Column(String(20), nullable=False, default="published")
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
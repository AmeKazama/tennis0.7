from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FavoriteItem(Base):
    __tablename__ = "favorite_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    folder_id = Column(BigInteger, nullable=True)
    target_type = Column(String(30), nullable=False)
    target_id = Column(BigInteger, nullable=False)
    title = Column(String(120), nullable=True)
    poster_url = Column(String(500), nullable=True)
    author_name = Column(String(80), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
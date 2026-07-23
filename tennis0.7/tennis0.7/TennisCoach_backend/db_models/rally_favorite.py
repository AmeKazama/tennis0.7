from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, String, UniqueConstraint

from database import Base


class RallyFavorite(Base):
    __tablename__ = "rally_favorite"
    __table_args__ = (
        UniqueConstraint("user_id", "video_key", name="uk_rally_favorite_user_video"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    video_key = Column(String(64), nullable=False)
    video_url = Column(String(1000), nullable=False)
    poster_url = Column(String(1000), nullable=True)
    title = Column(String(120), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)

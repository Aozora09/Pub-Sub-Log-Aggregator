# aggregator/models.py
from sqlalchemy import Column, String, Integer, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, index=True)  # UUID
    topic = Column(String, index=True)
    source = Column(String)
    payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # SYARAT T4 & T9: Dedup Store Persisten
    # Mencegah (topic + event_id) yang sama masuk dua kali di level DATABASE
    __table_args__ = (
        UniqueConstraint('topic', 'event_id', name='uq_topic_event_id'),
    )

class Stats(Base):
    __tablename__ = "stats"

    topic = Column(String, primary_key=True)
    count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
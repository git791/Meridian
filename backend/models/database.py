from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from contextlib import contextmanager
from core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    attendees = Column(Text)
    status = Column(String(50), default="scheduled")
    reminders_sent = Column(Text, default="[]") # JSON list like ["1d", "1h"]

class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text)          # JSON blob of full summary dict
    attendees = Column(Text)        # JSON list of emails
    created_at = Column(DateTime, server_default=func.now())

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
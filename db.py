from sqlalchemy import create_engine, Column, String, DateTime, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Load database URL from environment (populated from secrets.toml in Streamlit Cloud)
DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("db_url", "sqlite:///truth_social.db"))

# SQLite uses the built-in sqlite3 driver; no external dependency needed
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Post(Base):
    __tablename__ = 'posts'
    id = Column(String, primary_key=True, index=True)
    author = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    text = Column(Text)
    processed_tokens = Column(JSON)
    sentiment = Column(Float)
    embedding = Column(JSON)

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(String, primary_key=True, index=True)
    post_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    text = Column(Text)
    processed_tokens = Column(JSON)
    sentiment = Column(Float)
    embedding = Column(JSON)


def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_URL}")  # Shows where DB file/url lives

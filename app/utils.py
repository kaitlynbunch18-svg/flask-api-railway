from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import Config
from app.models import Base

engine = create_engine(Config.DATABASE_URL, future=True, echo=False, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

def init_db():
    Base.metadata.create_all(bind=engine)

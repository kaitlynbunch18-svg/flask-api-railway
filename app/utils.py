from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import Config
from app.models import Base

# Add SSL mode for Railway Postgres
DATABASE_URL = Config.DATABASE_URL
if "sslmode" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

engine = create_engine(
    DATABASE_URL, 
    future=True, 
    echo=False, 
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

def init_db():
    Base.metadata.create_all(bind=engine)

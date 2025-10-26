from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pos_app.config import settings

class Base(DeclarativeBase):
    pass

def get_engine():
    return create_engine(settings.DATABASE_URL, future=True)

def get_session_maker(engine=None):
    engine = engine or get_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

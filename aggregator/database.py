# aggregator/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Mengambil URL DB dari Environment Variable (diset di docker-compose)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@storage:5432/events_db")

engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory untuk interaksi DB
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency Injection untuk FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
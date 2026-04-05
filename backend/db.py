import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


DATABASE_URL = (
    f"postgresql+asyncpg://{_require('POSTGRES_USER')}:{_require('POSTGRES_PASSWORD')}"
    f"@{_require('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{_require('POSTGRES_DB')}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    BigInteger,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base

# ---- URL PostgreSQL (ASYNC) ----
DB_USER = "postgres"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "auto_ria_bot"

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ---- Async engine ----
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

# ---- Async session ----
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


# ---- DB utils ----
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---- MODELS ----
class Filter(Base):
    __tablename__ = "Filter"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)

    min_price = Column(Integer)
    max_price = Column(Integer)
    min_year = Column(Integer)
    max_year = Column(Integer)

    city = Column(Integer)
    mark_car = Column(Integer)

    page_count = Column(Integer, default=0)
    last_checked = Column(DateTime, default=datetime.utcnow)


class SentCar(Base):
    __tablename__ = "SentCar"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(
        BigInteger,
        ForeignKey("Filter.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    car_link = Column(Text, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "car_link", name="unique_user_car"),
    )


class CountCar(Base):
    __tablename__ = "CountCar"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(
        BigInteger,
        ForeignKey("Filter.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    count = Column(Integer, default=0)

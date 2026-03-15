"""PostgreSQL metadata store using SQLAlchemy async."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, JSON, Integer
from typing import List, Optional
from config import settings


class Base(DeclarativeBase):
    pass


class ChunkMetadata(Base):
    __tablename__ = "chunk_metadata"

    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(String)
    filename: Mapped[str] = mapped_column(String)
    page_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_metadata: Mapped[dict] = mapped_column(JSON)


class MetadataStore:
    """Async Postgres metadata."""

    def __init__(self):
        self.engine = create_async_engine(settings.postgres_url)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def store_chunk_metadata(self, session: AsyncSession, metadata: dict):
        """Store chunk metadata."""
        record = ChunkMetadata(**metadata)
        session.add(record)

    async def get_chunk_metadata(self, session: AsyncSession, chunk_id: str) -> Optional[dict]:
        """Get metadata by ID."""
        result = await session.get(ChunkMetadata, chunk_id)
        if result:
            return {c.name: getattr(result, c.name) for c in result.__table__.columns if c.name != 'chunk_id'}
        return None


_metadata_store = None


async def get_metadata_store() -> MetadataStore:
    global _metadata_store
    if _metadata_store is None:
        _metadata_store = MetadataStore()
        await _metadata_store.create_tables()
    return _metadata_store


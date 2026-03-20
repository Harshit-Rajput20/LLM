"""PostgreSQL metadata store using SQLAlchemy 2.0."""

import logging
from sqlalchemy import create_engine, String, JSON, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

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
    """Postgres metadata store."""

    def __init__(self):
        self.engine = create_engine(settings.postgres_url)
        self.session_maker = sessionmaker(self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def store_chunk_metadata(self, metadata: dict):
        """Store chunk metadata."""
        with self.session_maker() as session:
            record = ChunkMetadata(**metadata)
            session.add(record)
            session.commit()

    def get_chunk_metadata(self, chunk_id: str) -> Optional[dict]:
        """Get metadata by ID."""
        with self.session_maker() as session:
            result = session.get(ChunkMetadata, chunk_id)
            if result:
                return {
                    "document_id": result.document_id,
                    "filename": result.filename,
                    "page_num": result.page_num,
                    "chunk_metadata": result.chunk_metadata
                }
            return None

_metadata_store = None

def get_metadata_store() -> MetadataStore:
    global _metadata_store
    if _metadata_store is None:
        _metadata_store = MetadataStore()
        _metadata_store.create_tables()
    return _metadata_store


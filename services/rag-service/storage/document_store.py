"""MinIO document storage layer."""

from minio import Minio
from io import BytesIO
import asyncio
from typing import Optional
from config import settings


class DocumentStore:
    """Async MinIO client for raw chunk storage."""

    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False
        )
        self.bucket = "rag-documents"
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def store_chunk(self, chunk_id: str, text: str):
        """Store text chunk as object."""
        data = BytesIO(text.encode('utf-8'))
        self.client.put_object(self.bucket, chunk_id, data, len(text))

    async def get_chunk(self, chunk_id: str) -> Optional[str]:
        """Get text chunk."""
        try:
            obj = self.client.get_object(self.bucket, chunk_id)
            return str(obj.read(), 'utf-8')
        except:
            return None

    async def delete_chunk(self, chunk_id: str):
        """Delete chunk."""
        self.client.remove_object(settings.bucket, chunk_id)


_document_store = None


async def get_document_store() -> DocumentStore:
    global _document_store
    if _document_store is None:
        _document_store = DocumentStore()
    return _document_store


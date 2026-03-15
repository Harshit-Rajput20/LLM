"""Elasticsearch keyword index layer."""

from elasticsearch import AsyncElasticsearch
from typing import List, Dict
from config import settings


class KeywordIndex:
    """Async ES for BM25 keyword search."""

    INDEX_NAME = "rag_chunks"

    def __init__(self):
        self.client = AsyncElasticsearch(settings.elasticsearch_url)

    async def create_index(self):
        """Create index w/ text analyzer."""
        mapping = {
            "mappings": {
                "properties": {
                    "text": {"type": "text", "analyzer": "standard"},
                    "metadata": {"type": "object", "enabled": True}
                }
            }
        }
        if not await self.client.indices.exists(index=self.INDEX_NAME):
            await self.client.indices.create(index=self.INDEX_NAME, body=mapping)

    async def index_chunk(self, id: str, text: str, metadata: Dict):
        """Index chunk."""
        doc = {"text": text, "metadata": metadata}
        await self.client.index(index=self.INDEX_NAME, id=id, document=doc)

    async def search(self, query: str, top_k: int) -> List[Dict]:
        """BM25 search."""
        results = await self.client.search(
            index=self.INDEX_NAME,
            body={"query": {"match": {"text": query}}},
            size=top_k
        )
        return [{"score": hit["_score"], "payload": hit["_source"]} for hit in results["hits"]["hits"]]


_keyword_index = None


async def get_keyword_index() -> KeywordIndex:
    global _keyword_index
    if _keyword_index is None:
        _keyword_index = KeywordIndex()
        await _keyword_index.create_index()
    return _keyword_index


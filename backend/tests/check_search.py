# tests/check_search.py
import asyncio
from app.services.similarity_search import SimilaritySearchService

async def main():
    svc = SimilaritySearchService()
    results = await svc.semantic_search(
        user_id="d1335931-8ee7-46e4-a348-adae08b0e542",
        query="what are sparrows",
        n_results=3,
        min_score=0.1
    )
    for r in results:
        print(r)

asyncio.run(main())
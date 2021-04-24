from aiohttp_client_cache import CachedSession, SQLiteBackend
from aiolimiter import AsyncLimiter
from datetime import timedelta
from typing import Awaitable


class SemanticScholar:
    """Wrapper for the Semantic Scholar RESTful API."""

    def __init__(self, api_key: str = None, max_requests=100, window_size=300):
        """
        :param api_key: API key.
        :param max_requests: Max number of requests per window.
        :param window_size: Window size in seconds.
        """
        self._limiter = AsyncLimiter(max_requests, window_size)
        self._session = CachedSession(
            cache=SQLiteBackend(expire_after=timedelta(minutes=150))
        )
        if api_key is not None:
            self._session.headers.update({"x-api-key": api_key})
            self._base_url = "https://partner.semanticscholar.org/v1"
        else:
            self._base_url = "https://api.semanticscholar.org/v1"

    async def _get(self, endpoint: str, **kwargs):
        async with self._limiter:
            res = await self._session.get(f"{self._base_url}{endpoint}", **kwargs)
            return await res.json()

    async def get_paper(
        self, s2_id: str = None, arxiv_id: str = None, **kwargs
    ) -> Awaitable[dict]:
        if sum(i is None for i in (s2_id, arxiv_id)) != 1:
            raise ValueError("Exactly one type of paper ID must be provided.")

        paper_id = s2_id if s2_id is not None else f"arXiv:{arxiv_id}"
        return await self._get(f"/paper/{paper_id}", **kwargs)

    async def get_author(self, s2_id: str, **kwargs) -> Awaitable[dict]:
        return await self._get(f"/author/{s2_id}", **kwargs)

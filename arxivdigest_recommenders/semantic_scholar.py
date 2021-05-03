from aiohttp_client_cache import CachedSession, SQLiteBackend
from aiolimiter import AsyncLimiter
from datetime import timedelta
from typing import Optional
from arxivdigest_recommenders import config


class SemanticScholar:
    """Wrapper for the Semantic Scholar RESTful API."""

    _limiter = AsyncLimiter(
        config.S2_MAX_REQUESTS,
        config.S2_WINDOW_SIZE,
    )
    _base_url = (
        "https://partner.semanticscholar.org/v1"
        if config.S2_API_KEY is not None
        else "https://api.semanticscholar.org/v1"
    )

    def __init__(self):
        self._session: Optional[CachedSession] = None

    async def __aenter__(self):
        self._session = CachedSession(
            cache=SQLiteBackend(
                cache_name=config.S2_CACHE_PATH,
                urls_expire_after={
                    "*.semanticscholar.org/v1/paper": timedelta(days=30),
                    "*.semanticscholar.org/v1/author": timedelta(days=7),
                },
            )
        )
        if config.S2_API_KEY is not None:
            self._session.headers.update({"x-api-key": config.S2_API_KEY})
        return self

    async def __aexit__(self, *err):
        await self._session.close()
        self._session = None

    async def _get(self, endpoint: str, **kwargs) -> dict:
        async with self._limiter:
            res = await self._session.get(f"{self._base_url}{endpoint}", **kwargs)
            res.raise_for_status()
            return await res.json()

    async def get_paper(self, s2_id: str = None, arxiv_id: str = None, **kwargs):
        """Get paper metadata.

        Exactly one type of paper ID must be provided. The response is cached for 30 days by default.

        :param s2_id: S2 paper ID.
        :param arxiv_id: arXiv paper ID.
        :param kwargs: Additional arguments passed to the get method of the underlying CachedSession.
        :return: Paper metadata.
        """
        if sum(i is None for i in (s2_id, arxiv_id)) != 1:
            raise ValueError("Exactly one type of paper ID must be provided.")

        paper_id = s2_id if s2_id is not None else f"arXiv:{arxiv_id}"
        return await self._get(f"/paper/{paper_id}", **kwargs)

    async def get_author(self, s2_id: str, **kwargs):
        """Get author metadata.

        The response is cached for seven days by default.

        :param s2_id: S2 author ID.
        :param kwargs: Additional arguments passed to the get method of the underlying CachedSession.
        :return: Author metadata.
        """
        return await self._get(f"/author/{s2_id}", **kwargs)

import asyncio
from aiohttp import ClientSession
from aiolimiter import AsyncLimiter
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import timedelta, date
from collections import defaultdict
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
    _paper_locks = defaultdict(asyncio.Lock)
    _author_locks = defaultdict(asyncio.Lock)
    _sem: Optional[asyncio.Semaphore] = None
    _n = 0

    def __init__(self):
        self._session: Optional[ClientSession] = None
        self._db = AsyncIOMotorClient(config.MONGODB_HOST, config.MONGODB_PORT)[
            config.S2_CACHE_DB
        ]
        if SemanticScholar._sem is None:
            SemanticScholar._sem = asyncio.Semaphore(2000)

    async def __aenter__(self):
        self._session = ClientSession()
        if config.S2_API_KEY is not None:
            self._session.headers.update({"x-api-key": config.S2_API_KEY})
        return self

    async def __aexit__(self, *err):
        await self._session.close()
        self._session = None

    async def _get(self, endpoint: str, **kwargs) -> dict:
        async with SemanticScholar._limiter:
            res = await self._session.get(
                f"{SemanticScholar._base_url}{endpoint}", **kwargs
            )
            res.raise_for_status()
            return await res.json()

    async def paper(self, s2_id: str = None, arxiv_id: str = None, **kwargs):
        """Get paper metadata.

        Exactly one type of paper ID must be provided. Responses are cached for 30 days.

        :param s2_id: S2 paper ID.
        :param arxiv_id: arXiv paper ID.
        :param kwargs: Additional arguments passed to the get method of the underlying CachedSession.
        :return: Paper metadata.
        """
        if sum(i is None for i in (s2_id, arxiv_id)) != 1:
            raise ValueError("Exactly one type of paper ID must be provided.")

        paper_id = s2_id if s2_id is not None else f"arXiv:{arxiv_id}"
        async with SemanticScholar._sem, SemanticScholar._paper_locks[paper_id]:
            cached = await self._db.papers.find_one({"_id": paper_id})
            if (
                cached
                and date.fromisoformat(cached["date"])
                + timedelta(days=config.S2_PAPER_EXPIRATION)
                >= date.today()
            ):
                return cached["data"]
            paper = {
                "date": date.today().isoformat(),
                "data": await self._get(f"/paper/{paper_id}", **kwargs),
            }
            if cached:
                await self._db.papers.replace_one({"_id": paper_id}, paper)
            else:
                await self._db.papers.insert_one({"_id": paper_id, **paper})
            return paper["data"]

    async def author(self, s2_id: str, **kwargs):
        """Get author metadata.

        Responses are cached for seven days.

        :param s2_id: S2 author ID.
        :param kwargs: Additional arguments passed to the get method of the underlying CachedSession.
        :return: Author metadata.
        """
        async with SemanticScholar._sem, SemanticScholar._author_locks[s2_id]:
            cached = await self._db.authors.find_one({"_id": s2_id})
            if (
                cached
                and date.fromisoformat(cached["date"])
                + timedelta(days=config.S2_AUTHOR_EXPIRATION)
                >= date.today()
            ):
                return cached["data"]
            author = {
                "date": date.today().isoformat(),
                "data": await self._get(f"/author/{s2_id}", **kwargs),
            }
            if cached:
                await self._db.authors.replace_one({"_id": s2_id}, author)
            else:
                await self._db.authors.insert_one({"_id": s2_id, **author})
            return author["data"]

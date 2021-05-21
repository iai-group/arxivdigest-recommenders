import asyncio
from aiohttp import ClientSession, ClientResponseError
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import timedelta, date
from collections import defaultdict
from typing import Optional, List

from arxivdigest_recommenders.util import gather, AsyncRateLimiter
from arxivdigest_recommenders.log import get_logger
from arxivdigest_recommenders import config


logger = get_logger(__name__, "SemanticScholar")


class SemanticScholar:
    """Wrapper for the Semantic Scholar RESTful API."""

    _limiter = AsyncRateLimiter(
        config.S2_MAX_REQUESTS,
        config.S2_WINDOW_SIZE,
    )
    _base_url = (
        "https://partner.semanticscholar.org/v1"
        if config.S2_API_KEY is not None
        else "https://api.semanticscholar.org/v1"
    )
    _db = None
    _locks = defaultdict(asyncio.Lock)
    _errors = {}
    requests = 0
    cache_hits = 0
    cache_misses = 0
    errors = 0

    def __init__(self):
        self._session: Optional[ClientSession] = None

    async def __aenter__(self):
        self._session = ClientSession(raise_for_status=True)
        if SemanticScholar._db is None:
            SemanticScholar._db = AsyncIOMotorClient(
                config.MONGODB_HOST, config.MONGODB_PORT
            )[config.S2_CACHE_DB]
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
            SemanticScholar.requests += 1
            if SemanticScholar.requests % 100 == 0:
                logger.debug("Requests/errors: %d/%d", SemanticScholar.requests, SemanticScholar.errors)
            return await res.json()

    async def _cached_get(self, endpoint: str, collection: str, max_age: int) -> dict:
        if endpoint in SemanticScholar._errors:
            # There's no point in refetching and relogging exceptions for endpoints that have already responded with
            # error codes, so we just reraise any previous exception.
            raise SemanticScholar._errors[endpoint]
        async with SemanticScholar._locks[endpoint]:
            try:
                cached = await SemanticScholar._db[collection].find_one(
                    {"_id": endpoint}
                )
                if cached and date.fromisoformat(cached["expiration"]) >= date.today():
                    SemanticScholar.cache_hits += 1
                    return cached["data"]
                SemanticScholar.cache_misses += 1
                doc = {
                    "expiration": (date.today() + timedelta(days=max_age)).isoformat(),
                    "data": await self._get(endpoint),
                }
                await SemanticScholar._db[collection].replace_one(
                    {"_id": endpoint}, doc, upsert=True
                )
                return doc["data"]
            except ClientResponseError as e:
                logger.warn("%s: %s %s.", endpoint, e.status, e.message)
                SemanticScholar.errors += 1
                SemanticScholar._errors[endpoint] = e
                raise

    async def paper(self, s2_id: str = None, arxiv_id: str = None):
        """Get paper metadata.

        Exactly one type of paper ID must be provided.

        :param s2_id: S2 paper ID.
        :param arxiv_id: arXiv paper ID.
        :return: Paper metadata.
        """
        if sum(i is None for i in (s2_id, arxiv_id)) != 1:
            raise ValueError("Exactly one type of paper ID must be provided.")

        paper_id = s2_id if s2_id is not None else f"arXiv:{arxiv_id}"
        return await self._cached_get(
            f"/paper/{paper_id}",
            "papers",
            config.S2_PAPER_EXPIRATION,
        )

    async def author(self, s2_id: str):
        """Get author metadata.

        :param s2_id: S2 author ID.
        :return: Author metadata.
        """
        return await self._cached_get(
            f"/author/{s2_id}",
            "authors",
            config.S2_AUTHOR_EXPIRATION,
        )

    async def author_papers(
        self,
        author: dict = None,
        s2_id: str = None,
        max_age=config.MAX_PAPER_AGE,
    ) -> List[dict]:
        """Get metadata of an author's published papers.

        :param author: S2 author metadata.
        :param s2_id: S2 author ID.
        :param max_age: Max paper age.
        :return: Metadata of published papers.
        """
        if sum(i is None for i in (author, s2_id)) != 1:
            raise ValueError("Either S2 author data or S2 author ID must be provided.")

        if author is None:
            author = await self.author(s2_id)

        min_year = -1 if max_age is None else date.today().year - max_age
        return await gather(
            *[
                self.paper(s2_id=paper["paperId"])
                for paper in author["papers"]
                if paper["year"] is not None and paper["year"] >= min_year
            ]
        )

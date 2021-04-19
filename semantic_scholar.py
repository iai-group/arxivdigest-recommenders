from requests_cache import CachedSession
from datetime import datetime, timedelta
from itertools import dropwhile
from time import sleep
from typing import List


class SemanticScholar:
    """Wrapper for the Semantic Scholar RESTful API."""

    def __init__(self, api_key: str = None, max_requests=100, window_size=300):
        """
        :param api_key: API key.
        :param max_requests: Max number of requests per window.
        :param window_size: Window size in seconds.
        """
        self.max_requests = max_requests
        self.window_size = timedelta(seconds=window_size)
        self.window_requests: List[datetime] = []
        self.session = CachedSession(expire_after=300)
        if api_key is not None:
            self.session.headers.update({"x-api-key": api_key})
            self.base_url = "https://partner.semanticscholar.org/v1"
        else:
            self.base_url = "https://api.semanticscholar.org/v1"

    def _get(self, endpoint: str, **kwargs):
        now = datetime.now()
        self.window_requests = list(
            dropwhile(lambda t: t < now - self.window_size, self.window_requests)
        )
        if len(self.window_requests) >= self.max_requests:
            sleep_duration = self.window_size - (now - self.window_requests[0])
            sleep(sleep_duration.total_seconds())
        self.window_requests.append(now)

        return self.session.get(f"{self.base_url}{endpoint}", **kwargs).json()

    def get_paper(self, s2_id: str = None, arxiv_id: str = None, **kwargs) -> dict:
        if sum(i is None for i in (s2_id, arxiv_id)) != 1:
            raise ValueError("Exactly one type of paper ID must be provided.")

        paper_id = s2_id if s2_id is not None else f"arXiv:{arxiv_id}"
        return self._get(f"/paper/{paper_id}", **kwargs)

    def get_author(self, s2_id: str, **kwargs) -> dict:
        return self._get(f"/author/{s2_id}", **kwargs)

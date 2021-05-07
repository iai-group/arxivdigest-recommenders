import asyncio
import numpy as np
from urllib.parse import urlparse
from typing import Optional, List, Tuple, Any


def extract_s2_id(user: dict) -> Optional[str]:
    """Extract S2 ID from a user's Semantic Scholar profile link.

    :param user: User.
    :return: User S2 author ID.
    """
    s2_id = str(urlparse(user["semantic_scholar_profile"]).path).split("/")[-1]
    return s2_id if len(s2_id) > 0 else None


def pad_shortest(a: list, b: list, pad: Any = 0) -> Tuple[list, list]:
    """Pad the shortest of two lists in order to make them the same length.

    :param a: Vector a.
    :param b: Vector b.
    :param pad: Padding object.
    :return: Padded vectors.
    """
    len_diff = len(a) - len(b)
    if len_diff > 0:
        b = b + [pad] * len_diff
    elif len_diff < 0:
        a = a + [pad] * abs(len_diff)
    return a, b


def padded_cosine_sim(a: List[int], b: List[int]) -> float:
    """Find the cosine similarity between two vectors. The shortest vector is padded with zeros.

    :param a: Vector a.
    :param b: Vector b.
    :return: Cosine similarity.
    """
    if all(v == 0 for v in a) or all(v == 0 for v in b):
        return 0.0
    a, b = pad_shortest(a, b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


async def gather(*args):
    """Wrapper around asyncio.gather that ignores and excludes exceptions."""
    results = await asyncio.gather(*args, return_exceptions=True)
    return [result for result in results if not isinstance(result, Exception)]

import numpy as np
from urllib.parse import urlparse
from typing import Optional, List


def extract_s2_id(user: dict) -> Optional[str]:
    """Extract S2 ID from a user's Semantic Scholar profile link.

    :param user: User.
    :return: User S2 author ID.
    """
    s2_id = str(urlparse(user["semantic_scholar_profile"]).path).split("/")[-1]
    return s2_id if len(s2_id) > 0 else None


def padded_cosine_sim(a: List[int], b: List[int]) -> float:
    """Find the cosine similarity between two vectors. The shortest vector is padded with zeros.

    :param a: Vector a.
    :param b: Vector b.
    :return: Cosine similarity.
    """
    if sum(a) == 0 or sum(b) == 0:
        return 0
    len_diff = len(a) - len(b)
    if len_diff > 0:
        b = b + [0] * len_diff
    elif len_diff < 0:
        a = a + [0] * abs(len_diff)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

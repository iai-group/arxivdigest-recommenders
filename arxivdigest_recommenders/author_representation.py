import numpy as np
from typing import List, Dict, Any

from arxivdigest_recommenders import config


def venue_author_representation(
    venues: List[str], published_papers: List[Dict[str, Any]]
) -> np.ndarray:
    """Create an author vector representation based on the venues an author has published at.

    The returned vector is N-dimensional, where N is the number of venues that have been discovered thus far. Each value
    in the vector corresponds to a certain venue and represents the number of times the author has published there.

    :param venues: List of venues. Venues the author has published at that are not already in this list are appended.
    :param published_papers: Papers published by the author.
    :return: Author vector representation.
    """
    author_venues = (paper["venue"] for paper in published_papers if paper["venue"])
    num_author_venues = sum(int(paper["venue"] is not None) for paper in published_papers)
    representation = np.zeros(len(venues) + num_author_venues, dtype=int)
    for author_venue in author_venues:
        if author_venue.lower() in config.VENUE_BLACKLIST:
            continue
        if author_venue not in venues:
            venues.append(author_venue)
        venue_index = venues.index(author_venue)
        representation[venue_index] += 1
    return np.trim_zeros(representation, "b")

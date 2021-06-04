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
    author_venues = [paper["venue"] for paper in published_papers if paper["venue"]]
    for venue in author_venues:
        if venue.lower() not in config.VENUE_BLACKLIST and venue not in venues:
            venues.append(venue)
    return np.array([author_venues.count(venue) for venue in venues])

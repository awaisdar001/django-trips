import re
from datetime import timedelta
from typing import List, Optional


def format_trip_duration(duration: Optional[timedelta]) -> Optional[str]:
    """
    Formats a trip's duration as a human-readable "N Days M Nights" string.

    A single-day trip has no overnight stay, so it's rendered without a
    nights component.

    Example:
        >>> format_trip_duration(timedelta(days=7))
        '7 Days 6 Nights'
        >>> format_trip_duration(timedelta(days=1))
        '1 Day'
    """
    if not duration:
        return None

    days = duration.days
    if days <= 0:
        return None
    if days == 1:
        return "1 Day"

    nights = days - 1
    night_label = "Night" if nights == 1 else "Nights"
    return f"{days} Days {nights} {night_label}"


def tokenize(data) -> List[str]:
    """
    Splits the input string into a list of non-empty tokens based on spaces and plus signs.

    This function splits the given string `data` on one or more spaces or '+' characters,
    trims any surrounding whitespace from each token, and filters out any empty tokens.

    Example:
        >>> tokenize("naran+ kaghan  gilgit")
        ['naran', 'kaghan', 'gilgit']
    """
    tokens = re.split(r"[ +]+", data)
    return [token.strip() for token in tokens if token.strip()]

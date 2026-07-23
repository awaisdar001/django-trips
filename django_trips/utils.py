from datetime import timedelta
from typing import Optional


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

import re
from typing import List


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

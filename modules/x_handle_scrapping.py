import re

def get_twitter_handle_from_url(url: str) -> str | None:
    """
    Checks if the given URL is a Twitter or X.com link and extracts the handle if it is.

    Args:
        url: The URL to check.

    Returns:
        The Twitter handle (e.g., '@username') if the URL is a valid Twitter/X link
        and a handle can be extracted, otherwise None.
    """
    url_lower = url.lower()
    if 'twitter.com' not in url_lower and 'x.com' not in url_lower:
        return None

    match = re.search(r'(?:twitter\.com|x\.com)/(\w+)', url)
    if match:
        return match.group(1)
    
    return None
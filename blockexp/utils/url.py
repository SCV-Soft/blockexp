from typing import Tuple, Optional
from urllib.parse import ParseResult, urlparse

from requests.auth import HTTPBasicAuth


def get_scheme(url: str) -> str:
    pr: ParseResult = urlparse(url)
    return pr.scheme


def parse_url(url: str) -> Tuple[str, Optional[HTTPBasicAuth]]:
    pr: ParseResult = urlparse(url)
    if pr.username or pr.password:
        assert pr.username and pr.password
        auth = HTTPBasicAuth(pr.username, pr.password)
        url = url.replace(f'{pr.username}:{pr.password}@', '')
    else:
        auth = None

    return url, auth
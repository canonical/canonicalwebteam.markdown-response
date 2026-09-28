"""URL helpers shared between frontmatter extraction and link resolution."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def strip_query_param(url, param):
    """Return *url* with the given query parameter removed.

    Other query parameters, the path, and the fragment are preserved.
    """
    if not url or not param:
        return url

    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key != param
    ]
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )

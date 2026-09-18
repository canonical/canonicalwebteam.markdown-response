"""Serve /page.md as the Markdown rendering of /page.

The llms.txt spec (https://llmstxt.org/) links to pages with a .md
suffix. Flask matches the URL before any request hook runs, so
/page.md would 404 before it could be rewritten: the rewrite has
to happen at the WSGI layer, before the request reaches Flask.
"""

INDEX = "index"


class SuffixMiddleware:
    """WSGI middleware rewriting /page<suffix> to /page?<param>=<value>.

    Paths under the app's static URL path are left alone so that static
    files which happen to end in the suffix keep being served.
    """

    def __init__(self, app, suffix, query_param, query_value):
        self.wsgi_app = app.wsgi_app
        self.suffix = suffix
        self.query = f"{query_param}={query_value}"
        self.static_prefix = (
            app.static_url_path.rstrip("/") + "/"
            if app.static_url_path
            else None
        )

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")

        if path.endswith(self.suffix) and not self._is_static(path):
            environ["PATH_INFO"] = strip_suffix(path, self.suffix)
            query = environ.get("QUERY_STRING", "")
            environ["QUERY_STRING"] = (
                f"{query}&{self.query}" if query else self.query
            )

        return self.wsgi_app(environ, start_response)

    def _is_static(self, path):
        return self.static_prefix is not None and path.startswith(
            self.static_prefix
        )


def add_suffix(path, suffix):
    """Return the Markdown URL path for *path*.

    A path ending in a slash (the homepage or a directory) gets
    index<suffix>.
    """
    if path.endswith("/"):
        return path + INDEX + suffix

    return path + suffix


def strip_suffix(path, suffix):
    """Return the page path that *path* is the Markdown URL of."""
    index = INDEX + suffix

    if path.endswith("/" + index):
        return path[: -len(index)]

    return path[: -len(suffix)] or "/"

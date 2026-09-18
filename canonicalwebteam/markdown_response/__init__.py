"""Flask extension to serve HTML pages as Markdown via ?format=md."""

import logging

from bs4 import BeautifulSoup
from flask import abort, current_app, request

from .converter import (
    DEFAULT_CONTENT_SELECTOR,
    DEFAULT_STRIP_CLASSES,
    DEFAULT_STRIP_ELEMENTS,
    convert_html_to_markdown,
)
from .frontmatter import extract_frontmatter
from .suffix import SuffixMiddleware, add_suffix, strip_suffix

__all__ = ["MarkdownResponse", "add_suffix", "strip_suffix"]

logger = logging.getLogger(__name__)


class MarkdownResponse:
    """Flask extension that adds ?format=md support to all HTML responses.

    Usage:
        app = Flask(__name__)
        MarkdownResponse(app)

    Or with the application factory pattern:
        md = MarkdownResponse()
        md.init_app(app)

    Configuration via constructor kwargs:
        MarkdownResponse(app,
            content_selector="#main-content",
            strip_elements=["script", "style", "nav", "noscript"],
            strip_classes=["u-hide", "u-off-screen"],
            query_param="format",
            query_value="md",
            suffix=".md",
            is_private=lambda view: False,
            cache_control="public, max-age=3600",
        )
    """

    def __init__(self, app=None, **kwargs):
        self.content_selector = kwargs.get(
            "content_selector", DEFAULT_CONTENT_SELECTOR
        )
        self.strip_elements = kwargs.get(
            "strip_elements", DEFAULT_STRIP_ELEMENTS
        )
        self.strip_classes = kwargs.get("strip_classes", DEFAULT_STRIP_CLASSES)
        self.query_param = kwargs.get("query_param", "format")
        self.query_value = kwargs.get("query_value", "md")
        self.suffix = kwargs.get("suffix")
        self.is_private = kwargs.get("is_private")
        self.cache_control = kwargs.get("cache_control")

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Register the after_request handler on the Flask app."""
        app.extensions["markdown_response"] = self
        app.after_request(self._handle_markdown_request)

        if self.is_private is not None:
            app.before_request(self._block_private_markdown)

        if self.suffix:
            app.wsgi_app = SuffixMiddleware(
                app, self.suffix, self.query_param, self.query_value
            )
            app.context_processor(self._template_context)

    def is_markdown_request(self):
        """Whether the current request asks for Markdown."""
        return request.args.get(self.query_param) == self.query_value

    def markdown_path(self):
        """The Markdown URL path of the current page, or None.

        None when no suffix is configured, when the page is private or
        when the request matched no view.
        """
        if not self.suffix:
            return None

        view = current_app.view_functions.get(request.endpoint)

        if view is None or self._is_private_view(view):
            return None

        return add_suffix(request.path, self.suffix)

    def _is_private_view(self, view):
        return self.is_private is not None and self.is_private(view)

    def _template_context(self):
        return {"markdown_path": self.markdown_path()}

    def _block_private_markdown(self):
        """Answer a Markdown request for a private page with 404."""
        if not self.is_markdown_request():
            return

        view = current_app.view_functions.get(request.endpoint)

        if view is not None and self._is_private_view(view):
            abort(404)

    def _handle_markdown_request(self, response):
        """Convert HTML responses to Markdown when ?format=md is present."""
        if not self.is_markdown_request():
            return response

        if "text/html" not in response.content_type:
            return response

        if response.status_code != 200:
            return response

        try:
            html = response.get_data(as_text=True)
            soup = BeautifulSoup(html, "html.parser")

            frontmatter = extract_frontmatter(html, soup=soup)

            # Use og:url as base for resolving relative links
            og_url = soup.find("meta", attrs={"property": "og:url"})
            base_url = (
                og_url["content"].strip()
                if og_url and og_url.get("content")
                else request.url
            )

            markdown_body = convert_html_to_markdown(
                html,
                content_selector=self.content_selector,
                strip_elements=self.strip_elements,
                strip_classes=self.strip_classes,
                soup=soup,
                base_url=base_url,
            )

            markdown_output = frontmatter + "\n" + markdown_body
            response.set_data(markdown_output)
            response.content_type = "text/markdown; charset=utf-8"

            if self.cache_control:
                response.headers["Cache-Control"] = self.cache_control
        except Exception:
            logger.exception("Failed to convert response to Markdown")

        return response

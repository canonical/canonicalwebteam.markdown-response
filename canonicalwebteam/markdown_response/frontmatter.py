"""Extract metadata from HTML <head> into YAML frontmatter."""

import re

import yaml
from bs4 import BeautifulSoup

from .urls import strip_query_param

# Suffixes stripped from the end of <title> content by default. Sites
# commonly append a site name to every page title (often via a shared
# template), which is redundant once the title is used as frontmatter.
DEFAULT_TITLE_SUFFIXES = [
    " | Canonical",
    " | Trusted open source for enterprises",
    " | Ubuntu",
]


def extract_frontmatter(
    html, soup=None, title_suffixes=None, strip_query_param_name=None
):
    """Parse HTML and return YAML frontmatter string from <head> meta tags.

    Returns a string like:
        ---
        title: Page Title
        description: Page description
        url: https://canonical.com/page
        ---

    If *soup* is provided it is used directly, avoiding a redundant parse.

    *title_suffixes* overrides the list of suffixes stripped from the end
    of the page title (defaults to DEFAULT_TITLE_SUFFIXES).

    *strip_query_param_name*, if given, is a query parameter name to
    remove from the extracted `url` (og:url), leaving other query
    parameters intact.
    """
    if soup is None:
        soup = BeautifulSoup(html, "html.parser")
    if title_suffixes is None:
        title_suffixes = DEFAULT_TITLE_SUFFIXES
    meta = {}

    # Title — collapse internal whitespace, then strip common suffixes
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title = re.sub(r"\s+", " ", title_tag.string).strip()
        for suffix in title_suffixes:
            title = title.removesuffix(suffix)
        title = title.strip()
        if title:
            meta["title"] = title

    # Description
    desc = _get_meta(soup, "description")
    if desc:
        meta["description"] = desc

    # URL
    url = _get_meta_property(soup, "og:url")
    if url:
        if strip_query_param_name:
            url = strip_query_param(url, strip_query_param_name)
        meta["url"] = url

    # Author
    author = _get_meta(soup, "author")
    if author and author != "Canonical Ltd":
        meta["author"] = author

    # Keywords
    keywords = _get_meta(soup, "keywords")
    if keywords:
        meta["keywords"] = keywords

    # Blog-specific: date and tags
    date = _get_meta_property(soup, "article:published_time")
    if date:
        meta["date"] = date

    tags = _get_all_meta_properties(soup, "article:tag")
    if tags:
        meta["tags"] = tags

    if not meta:
        return ""

    frontmatter = yaml.dump(
        meta, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
    return f"---\n{frontmatter}---\n"


def _get_meta(soup, name):
    """Get content from <meta name="..."> tag."""
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def _get_meta_property(soup, prop):
    """Get content from <meta property="..."> tag."""
    tag = soup.find("meta", attrs={"property": prop})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def _get_all_meta_properties(soup, prop):
    """Get content from all <meta property="..."> tags as a list.

    Returns a list of strings, or None if no matching tags are found.
    If only one tag is found, returns a single-element list for
    consistent YAML list output.
    """
    tags = soup.find_all("meta", attrs={"property": prop})
    values = [
        t["content"].strip() for t in tags if t.get("content")
    ]
    return values if values else None

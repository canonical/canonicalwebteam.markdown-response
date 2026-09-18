# canonicalwebteam.markdown-response

Flask extension that adds `?format=md` support to all HTML responses, converting pages to clean Markdown with YAML frontmatter. Designed for LLM and crawler optimization.

## Installation

```bash
pip install canonicalwebteam.markdown-response
```

## Usage

```python
from canonicalwebteam.markdown_response import MarkdownResponse

app = Flask(__name__)
MarkdownResponse(app)
```

Or with the application factory pattern:

```python
md = MarkdownResponse()
md.init_app(app)
```

Any page can now be accessed as Markdown by appending `?format=md` to the URL.

## Configuration

```python
MarkdownResponse(app,
    content_selector="#main-content",  # CSS selector for content extraction
    strip_elements=["script", "style", "nav", "noscript"],  # Tags to remove
    strip_classes=["u-hide", "u-off-screen"],  # Classes to remove
    query_param="format",  # Query parameter name
    query_value="md",  # Query parameter value
    suffix=None,  # e.g. ".md" to also serve /page.md
    is_private=None,  # callable(view) -> True for pages with no Markdown
    cache_control=None,  # Cache-Control header for Markdown responses
)
```

## Serving pages at `/page.md`

The [llms.txt spec](https://llmstxt.org/) links to pages with a `.md` suffix. Pass `suffix=".md"` to serve every page that way too:

```python
MarkdownResponse(app, suffix=".md")
```

- `/about.md` is the Markdown of `/about`
- `/index.md` is the Markdown of `/`, and `/docs/index.md` of `/docs/`
- Paths under the app's static URL path are left alone, so static files ending in `.md` are still served as files

The rewrite happens at the WSGI layer (before Flask matches the URL), so it works for every route without changes to views. The query parameter keeps working alongside it; set `query_param` to something private (for example `_markdown`) if the suffix should be the only public way to ask for Markdown.

Templates get a `markdown_path` variable with the Markdown URL path of the current page (or `None`), for advertising the alternate:

```html
{% if markdown_path %}
  <link rel="alternate" type="text/markdown" href="https://example.com{{ markdown_path }}" />
{% endif %}
```

`add_suffix(path, suffix)` and `strip_suffix(path, suffix)` are exported for building such URLs elsewhere, for instance in an `llms.txt`.

## Private pages

Pages behind login should not have a Markdown version. Pass `is_private`, a callable that receives the view function of the current request and returns `True` for such pages:

```python
def is_login_gated(view):
    while view is not None:
        if getattr(view, "__name__", None) == "is_user_logged_in":
            return True
        view = getattr(view, "__wrapped__", None)
    return False

MarkdownResponse(app, suffix=".md", is_private=is_login_gated)
```

A Markdown request for a private page is answered with `404`, and its `markdown_path` is `None`. The HTML page is unaffected.

## Template-level exclusion

Add `data-md-strip` to any HTML element to exclude it from the Markdown output:

```html
<section data-md-strip>
    <form>This form won't appear in markdown output</form>
</section>
```

## How it works

1. An `after_request` handler intercepts responses when `?format=md` is present
2. Only processes HTML 200 responses (JSON, XML, errors pass through)
3. Extracts the content area using BeautifulSoup (`#main-content` by default)
4. Strips unwanted elements (scripts, styles, nav, hidden elements, `data-md-strip`)
5. Converts remaining HTML to Markdown via markdownify
6. Prepends YAML frontmatter extracted from `<head>` meta tags
7. Returns with `Content-Type: text/markdown; charset=utf-8` (and `Cache-Control` when `cache_control` is set)

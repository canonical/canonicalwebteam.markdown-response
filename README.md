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
)
```

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
7. Returns with `Content-Type: text/markdown; charset=utf-8`

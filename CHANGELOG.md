## [0.3.0] - 2026-09-18
### Added
- Optional `suffix` (e.g. `".md"`): serve `/page.md` as the Markdown rendering of `/page`, with `index.md` for the homepage and directory paths. Paths under the app's static URL path are not rewritten
- `markdown_path` template variable (only when `suffix` is set): the Markdown URL path of the current page, or `None`
- Optional `is_private(view)` callable: Markdown requests for private pages are answered with 404 and their `markdown_path` is `None`
- Optional `cache_control`: the `Cache-Control` header set on Markdown responses
- `add_suffix(path, suffix)` and `strip_suffix(path, suffix)` helpers

All new options are off by default: `MarkdownResponse(app)` behaves as in 0.2.0.

## [0.2.0] - 2026-04-07
### Changed
- Parse HTML once per request instead of twice, improving performance on large pages
- Resolve relative links to absolute URLs using `og:url` (or `request.url` as fallback)
- Capture all `article:tag` meta tags as a YAML list instead of only the first

## [0.1.0] - 2026-03-26
### Added
- Initial release
- `MarkdownResponse` Flask extension class with `init_app` support
- `?format=md` query parameter converts HTML responses to Markdown
- YAML frontmatter extraction from `<head>` meta tags (title, description, url, author, keywords, date, tags)
- Content extraction via configurable CSS selector (defaults to `#main-content`)
- Strips scripts, styles, nav, noscript, hidden elements, and `data-md-strip` marked elements
- Configurable `content_selector`, `strip_elements`, `strip_classes`, `query_param`, `query_value`
- Graceful error handling with fallback to original HTML response

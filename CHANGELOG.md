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

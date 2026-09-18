import unittest
import flask
from canonicalwebteam.markdown_response.frontmatter import (
    extract_frontmatter,
)
from canonicalwebteam.markdown_response.converter import (
    convert_html_to_markdown,
)
from canonicalwebteam.markdown_response import (
    MarkdownResponse,
    add_suffix,
    strip_suffix,
)


class TestFrontmatter(unittest.TestCase):
    def test_extracts_title(self):
        html = """
        <html>
        <head>
            <title>What is Kubernetes | Canonical</title>
            <meta name="description" content="Learn about Kubernetes" />
            <meta property="og:url"
                  content="https://canonical.com/blog/what-is-kubernetes" />
        </head>
        <body></body>
        </html>
        """
        result = extract_frontmatter(html)
        self.assertIn("title: What is Kubernetes", result)
        self.assertNotIn("| Canonical", result)

    def test_extracts_description_and_url(self):
        html = """
        <html>
        <head>
            <title>Test Page | Canonical</title>
            <meta name="description" content="A test page" />
            <meta property="og:url" content="https://canonical.com/test" />
        </head>
        <body></body>
        </html>
        """
        result = extract_frontmatter(html)
        self.assertIn("description: A test page", result)
        self.assertIn("url: https://canonical.com/test", result)

    def test_extracts_blog_specific_fields(self):
        html = """
        <html>
        <head>
            <title>Blog Post | Canonical</title>
            <meta name="description" content="A blog post" />
            <meta property="og:url"
                  content="https://canonical.com/blog/post" />
            <meta name="author" content="Jane Doe" />
            <meta property="article:published_time" content="2025-06-15" />
            <meta property="article:tag" content="kubernetes" />
        </head>
        <body></body>
        </html>
        """
        result = extract_frontmatter(html)
        self.assertIn("author: Jane Doe", result)
        self.assertIn("date: '2025-06-15'", result)
        self.assertIn("- kubernetes", result)

    def test_extracts_multiple_tags(self):
        html = """
        <html>
        <head>
            <title>Blog Post | Canonical</title>
            <meta property="article:tag" content="kubernetes" />
            <meta property="article:tag" content="cloud" />
            <meta property="article:tag" content="security" />
        </head>
        <body></body>
        </html>
        """
        result = extract_frontmatter(html)
        self.assertIn("- kubernetes", result)
        self.assertIn("- cloud", result)
        self.assertIn("- security", result)

    def test_omits_missing_fields(self):
        html = """
        <html>
        <head>
            <title>Simple Page | Canonical</title>
        </head>
        <body></body>
        </html>
        """
        result = extract_frontmatter(html)
        self.assertIn("title: Simple Page", result)
        self.assertNotIn("description:", result)
        self.assertNotIn("author:", result)
        self.assertNotIn("date:", result)
        self.assertNotIn("tags:", result)

    def test_frontmatter_has_delimiters(self):
        html = """
        <html>
        <head><title>Page | Canonical</title></head>
        <body></body>
        </html>
        """
        result = extract_frontmatter(html)
        self.assertTrue(result.startswith("---\n"))
        self.assertTrue(result.endswith("\n---\n"))

    def test_strips_whitespace_in_description(self):
        html = """
        <html>
        <head>
            <title>Page | Canonical</title>
            <meta name="description" content="
                Multi line description with extra spaces
            " />
        </head>
        <body></body>
        </html>
        """
        result = extract_frontmatter(html)
        self.assertIn(
            "description: Multi line description with extra spaces", result
        )


class TestConverter(unittest.TestCase):
    def test_extracts_main_content(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <nav><a href="/">Home</a><a href="/about">About</a></nav>
            <div id="main-content">
                <h1>Hello World</h1>
                <p>This is the content.</p>
            </div>
            <footer><p>Copyright 2025</p></footer>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("# Hello World", result)
        self.assertIn("This is the content.", result)
        self.assertNotIn("Home", result)
        self.assertNotIn("About", result)
        self.assertNotIn("Copyright", result)

    def test_strips_script_and_style_tags(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content">
                <h1>Page</h1>
                <script>alert('hi')</script>
                <style>.foo { color: red; }</style>
                <p>Content here.</p>
            </div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("Content here.", result)
        self.assertNotIn("alert", result)
        self.assertNotIn(".foo", result)

    def test_strips_nav_and_noscript(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content">
                <nav><a href="/nav-link">Nav</a></nav>
                <noscript>Enable JS</noscript>
                <p>Real content.</p>
            </div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("Real content.", result)
        self.assertNotIn("Nav", result)
        self.assertNotIn("Enable JS", result)

    def test_strips_hidden_elements(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content">
                <p>Visible content.</p>
                <div class="u-hide">Hidden stuff</div>
                <a class="u-off-screen">Skip link</a>
            </div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("Visible content.", result)
        self.assertNotIn("Hidden stuff", result)
        self.assertNotIn("Skip link", result)

    def test_falls_back_to_body(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <h1>No main-content div</h1>
            <p>Body content.</p>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("# No main-content div", result)
        self.assertIn("Body content.", result)

    def test_collapses_excessive_blank_lines(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content">
                <h1>Title</h1>
                <br><br><br><br><br>
                <p>After many breaks.</p>
            </div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertNotIn("\n\n\n\n", result)

    def test_strips_data_md_strip_elements(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content">
                <h1>Contact us</h1>
                <p>Get in touch with our team.</p>
                <section data-md-strip>
                    <form action="https://ubuntu.com/marketo/submit"
                          method="post" id="mktoForm_1234">
                        <label for="name">Name</label>
                        <input type="text" id="name" name="name" />
                        <button type="submit">Submit</button>
                    </form>
                </section>
            </div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("Contact us", result)
        self.assertIn("Get in touch with our team.", result)
        self.assertNotIn("Submit", result)
        self.assertNotIn("mktoForm", result)

    def test_preserves_elements_without_data_md_strip(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content">
                <form id="tab-selector">
                    <label>Pick a tab</label>
                </form>
            </div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(html)
        self.assertIn("Pick a tab", result)

    def test_resolves_relative_links(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content">
                <a href="/blog/post">Blog post</a>
                <a href="https://example.com/abs">Absolute</a>
            </div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(
            html, base_url="https://canonical.com/page"
        )
        self.assertIn("https://canonical.com/blog/post", result)
        self.assertIn("https://example.com/abs", result)
        self.assertNotIn("(/blog/post)", result)

    def test_custom_content_selector(self):
        html = """
        <html>
        <head><title>Test | Canonical</title></head>
        <body>
            <div id="main-content"><p>Wrong div.</p></div>
            <div id="custom-content"><p>Right div.</p></div>
        </body>
        </html>
        """
        result = convert_html_to_markdown(
            html, content_selector="#custom-content"
        )
        self.assertIn("Right div.", result)
        self.assertNotIn("Wrong div.", result)


class TestMarkdownResponse(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)

        @self.app.route("/test")
        def test_page():
            return """
            <html>
            <head>
                <title>Test Page | Canonical</title>
                <meta name="description" content="A test page" />
                <meta property="og:url"
                      content="https://canonical.com/test" />
            </head>
            <body>
                <nav><a href="/">Home</a></nav>
                <div id="main-content">
                    <h1>Test Page</h1>
                    <p>This is test content.</p>
                </div>
                <footer><p>Footer</p></footer>
            </body>
            </html>
            """

        MarkdownResponse(self.app)
        self.client = self.app.test_client()

    def test_normal_request_returns_html(self):
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        self.assertIn(b"<h1>Test Page</h1>", response.data)

    def test_format_md_returns_markdown(self):
        response = self.client.get("/test?format=md")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(b"# Test Page", response.data)
        self.assertIn(b"This is test content.", response.data)

    def test_format_md_has_frontmatter(self):
        response = self.client.get("/test?format=md")
        body = response.data.decode("utf-8")
        self.assertTrue(body.startswith("---\n"))
        self.assertIn("title: Test Page", body)
        self.assertIn("description: A test page", body)
        self.assertIn("url: https://canonical.com/test", body)

    def test_format_md_strips_navigation(self):
        response = self.client.get("/test?format=md")
        body = response.data.decode("utf-8")
        self.assertNotIn("Home", body)
        self.assertNotIn("Footer", body)

    def test_format_md_resolves_relative_links(self):
        @self.app.route("/links")
        def links_page():
            return """
            <html>
            <head>
                <title>Links | Canonical</title>
                <meta property="og:url"
                      content="https://canonical.com/links" />
            </head>
            <body>
                <div id="main-content">
                    <a href="/blog/post">Relative</a>
                    <a href="https://example.com">Absolute</a>
                </div>
            </body>
            </html>
            """

        response = self.client.get("/links?format=md")
        body = response.data.decode("utf-8")
        self.assertIn("https://canonical.com/blog/post", body)
        self.assertIn("https://example.com", body)

    def test_skips_non_html_responses(self):
        @self.app.route("/api")
        def api():
            return flask.jsonify({"key": "value"})

        response = self.client.get("/api?format=md")
        self.assertIn("application/json", response.content_type)

    def test_skips_non_200_responses(self):
        @self.app.route("/error")
        def error():
            return "<html><body>Not Found</body></html>", 404

        response = self.client.get("/error?format=md")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("text/markdown", response.content_type)

    def test_custom_content_selector(self):
        app2 = flask.Flask(__name__)

        @app2.route("/custom")
        def custom():
            return """
            <html>
            <head><title>Custom | Canonical</title></head>
            <body>
                <div id="wrapper"><p>Custom content.</p></div>
            </body>
            </html>
            """

        MarkdownResponse(app2, content_selector="#wrapper")
        client2 = app2.test_client()
        response = client2.get("/custom?format=md")
        self.assertIn(b"Custom content.", response.data)


PAGE = """
<html>
<head>
    <title>{title} | Canonical</title>
    <meta property="og:url" content="https://canonical.com{path}" />
</head>
<body>
    <div id="main-content"><h1>{title}</h1></div>
</body>
</html>
"""


def page(title, path):
    return PAGE.format(title=title, path=path)


def login_required(view):
    def is_user_logged_in(*args, **kwargs):
        return view(*args, **kwargs)

    is_user_logged_in.__wrapped__ = view
    return is_user_logged_in


def is_login_gated(view):
    while view is not None:
        if getattr(view, "__name__", None) == "is_user_logged_in":
            return True
        view = getattr(view, "__wrapped__", None)
    return False


def make_app(**kwargs):
    app = flask.Flask(__name__)

    @app.route("/")
    def home():
        return page("Home", "/")

    @app.route("/about")
    def about():
        return page("About", "/about")

    @app.route("/docs/")
    def docs():
        return page("Docs", "/docs/")

    @app.route("/account")
    @login_required
    def account():
        return page("Account", "/account")

    @app.route("/query")
    def query():
        return flask.jsonify(dict(flask.request.args))

    @app.route("/link")
    def link():
        return flask.render_template_string("{{ markdown_path }}")

    MarkdownResponse(app, **kwargs)
    return app


class TestSuffixHelpers(unittest.TestCase):
    def test_add_suffix(self):
        self.assertEqual(add_suffix("/about", ".md"), "/about.md")
        self.assertEqual(add_suffix("/", ".md"), "/index.md")
        self.assertEqual(add_suffix("/docs/", ".md"), "/docs/index.md")

    def test_strip_suffix(self):
        self.assertEqual(strip_suffix("/about.md", ".md"), "/about")
        self.assertEqual(
            strip_suffix("/about/publish.md", ".md"), "/about/publish"
        )
        self.assertEqual(strip_suffix("/index.md", ".md"), "/")
        self.assertEqual(strip_suffix("/docs/index.md", ".md"), "/docs/")
        self.assertEqual(strip_suffix("/.md", ".md"), "/")

    def test_round_trip(self):
        for path in ["/", "/about", "/about/publish", "/docs/"]:
            self.assertEqual(
                strip_suffix(add_suffix(path, ".md"), ".md"), path
            )


class TestDefaultsUnchanged(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.client = self.app.test_client()

    def test_suffix_is_not_served(self):
        self.assertEqual(self.client.get("/about.md").status_code, 404)

    def test_query_param_still_works(self):
        response = self.client.get("/about?format=md")
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(b"# About", response.data)

    def test_no_cache_control_header(self):
        response = self.client.get("/about?format=md")
        self.assertNotIn("Cache-Control", response.headers)

    def test_private_pages_are_not_blocked(self):
        response = self.client.get("/account?format=md")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)

    def test_no_markdown_path_in_templates(self):
        self.assertEqual(self.client.get("/link").data, b"")

    def test_markdown_path_is_none(self):
        with self.app.test_request_context("/about"):
            extension = self.app.extensions["markdown_response"]
            self.assertIsNone(extension.markdown_path())


class TestSuffix(unittest.TestCase):
    def setUp(self):
        self.app = make_app(suffix=".md")
        self.client = self.app.test_client()

    def test_suffix_returns_markdown(self):
        response = self.client.get("/about.md")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(b"# About", response.data)
        self.assertIn(b"title: About", response.data)

    def test_index_md_is_the_homepage(self):
        response = self.client.get("/index.md")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"# Home", response.data)

    def test_index_md_under_a_directory(self):
        response = self.client.get("/docs/index.md")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"# Docs", response.data)

    def test_html_is_still_served_without_suffix(self):
        response = self.client.get("/about")
        self.assertIn("text/html", response.content_type)
        self.assertIn(b"<h1>About</h1>", response.data)

    def test_existing_query_string_is_kept(self):
        response = self.client.get("/query.md?page=2")
        self.assertEqual(response.get_json(), {"page": "2", "format": "md"})

    def test_unknown_page_is_404(self):
        self.assertEqual(self.client.get("/missing.md").status_code, 404)

    def test_markdown_path_in_templates(self):
        self.assertEqual(self.client.get("/link").data, b"/link.md")

    def test_markdown_path_for_the_homepage(self):
        with self.app.test_request_context("/"):
            extension = self.app.extensions["markdown_response"]
            self.assertEqual(extension.markdown_path(), "/index.md")

    def test_static_files_are_left_alone(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as static_folder:
            with open(os.path.join(static_folder, "README.md"), "w") as f:
                f.write("# Not converted\n")

            app = flask.Flask(
                __name__,
                static_folder=static_folder,
                static_url_path="/static",
            )
            MarkdownResponse(app, suffix=".md")

            response = app.test_client().get("/static/README.md")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"# Not converted\n")

    def test_custom_query_param_is_internal(self):
        app = make_app(suffix=".md", query_param="_markdown", query_value="1")
        client = app.test_client()

        self.assertIn(b"# About", client.get("/about.md").data)
        self.assertIn("text/html", client.get("/about?format=md").content_type)


class TestPrivatePages(unittest.TestCase):
    def setUp(self):
        self.app = make_app(suffix=".md", is_private=is_login_gated)
        self.client = self.app.test_client()

    def test_private_page_has_no_markdown(self):
        self.assertEqual(self.client.get("/account.md").status_code, 404)
        self.assertEqual(
            self.client.get("/account?format=md").status_code, 404
        )

    def test_private_page_html_is_untouched(self):
        response = self.client.get("/account")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)

    def test_public_page_still_has_markdown(self):
        self.assertIn(b"# About", self.client.get("/about.md").data)

    def test_markdown_path_is_none_for_private_pages(self):
        with self.app.test_request_context("/account"):
            extension = self.app.extensions["markdown_response"]
            self.assertIsNone(extension.markdown_path())

    def test_markdown_path_is_none_for_unknown_pages(self):
        with self.app.test_request_context("/missing"):
            extension = self.app.extensions["markdown_response"]
            self.assertIsNone(extension.markdown_path())

    def test_is_private_without_suffix(self):
        app = make_app(is_private=is_login_gated)
        client = app.test_client()

        self.assertEqual(client.get("/account?format=md").status_code, 404)
        self.assertIn(b"# About", client.get("/about?format=md").data)


class TestCacheControl(unittest.TestCase):
    def test_header_is_set_on_markdown(self):
        app = make_app(cache_control="private, max-age=3600")
        response = app.test_client().get("/about?format=md")
        self.assertEqual(
            response.headers["Cache-Control"], "private, max-age=3600"
        )

    def test_header_is_not_set_on_html(self):
        app = make_app(cache_control="private, max-age=3600")
        response = app.test_client().get("/about")
        self.assertNotIn("Cache-Control", response.headers)

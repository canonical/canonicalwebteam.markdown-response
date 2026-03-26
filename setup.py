#! /usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="canonicalwebteam.markdown-response",
    version="0.1.0",
    author="Canonical webteam",
    author_email="webteam@canonical.com",
    url=(
        "https://github.com/canonical/"
        "canonicalwebteam.markdown-response"
    ),
    description=(
        "Flask extension to serve HTML pages as Markdown "
        "via ?format=md query parameter."
    ),
    packages=find_packages(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "Flask",
        "beautifulsoup4",
        "markdownify",
        "PyYAML",
    ],
)

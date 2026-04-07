"""
Rendering helpers for markdown-backed HTML snippets in templates.
"""

import re

import markdown

SAFE_TAGS = {
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "code",
    "pre",
    "span",
    "ul",
    "ol",
    "li",
    "a",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "hr",
    "div",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "img",
    "del",
    "s",
    "sub",
    "sup",
}


def _sanitize_html(html_str: str) -> str:
    """Escape tags that are not produced by the approved markdown renderer."""

    def replace_tag(match: re.Match[str]) -> str:
        tag_name = match.group(1).strip().split()[0].lower().lstrip("/")
        if tag_name in SAFE_TAGS:
            return match.group(0)
        return match.group(0).replace("<", "&lt;").replace(">", "&gt;")

    return re.sub(r"<(/?\s*[a-zA-Z][^>]*)>", replace_tag, html_str)


def markdown_to_safe_html(text: str) -> str:
    """Render markdown text to sanitized HTML."""
    if not text:
        return ""

    renderer = markdown.Markdown(extensions=["fenced_code", "codehilite"])
    return _sanitize_html(renderer.convert(text))

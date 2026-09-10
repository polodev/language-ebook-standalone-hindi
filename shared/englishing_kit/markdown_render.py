"""Markdown -> HTML for every `*_md` field in a course JSON.

The authoring rules live in docs/JSON-CONTENT-GUIDE.md. This module enforces them.

Two entry points, and picking the right one matters:

    render_inline(text)  -> HTML with NO wrapping <p>. For table cells, chips,
                            labels, headings, card fields.
    render_block(text)   -> full block HTML (<p>, <ul>, <h3>). For lesson intros,
                            grammar notes, descriptions.

Why the split is load-bearing: Python-Markdown wraps everything in <p>, and a <p>
inside a table cell brings its own margin. That grows the row by a couple of
millimetres, which silently pushes the 5th vocabulary row onto the next page and
quietly wrecks the pagination of an entire 700-page book. Use render_inline in
anything that is already inside a box.
"""
from __future__ import annotations

import html
import re
from typing import Any

import markdown as _markdown

# Deliberately minimal. Every extension added here has to render correctly in BOTH
# the PDF (Chrome) and the EPUB (XHTML-strict), so the bar for adding one is high.
#
# `tables` is here because a two-column contrast table (❌ wrong / ✅ right) is the single
# clearest way to teach a correction, and courses use it constantly. It was missing at
# first, which printed every table in the book as raw `| pipes |` — valid Markdown,
# rendered as garbage, and the build said nothing. Do not remove it.
_EXTENSIONS = ["sane_lists", "tables", "nl2br"]

# Emoji have no colour font embedded in the PDF, so they render as tofu. Strip them.
_EMOJI_RE = re.compile(
    "[" "\U0001F000-\U0001FAFF" "\U00002600-\U000027BF" "\U0000FE0E-\U0000FE0F" "\U0000200D" "]+"
)

_md = _markdown.Markdown(extensions=_EXTENSIONS, output_format="xhtml")

# Matches a <p>...</p> wrapping the whole string. Careful: this alone is not proof
# the content is a SINGLE paragraph — "<p>a</p><p>b</p>" also matches it, greedily.
# _BLOCK_TAG_RE is the second check that catches that case.
_SOLE_PARAGRAPH_RE = re.compile(r"^<p>(.*)</p>$", re.DOTALL)
_BLOCK_TAG_RE = re.compile(r"</?(?:p|ul|ol|li|h[1-6]|blockquote)\b[^>]*>")


def strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text)


def _convert(text: str) -> str:
    _md.reset()
    return _md.convert(text)


def render_block(value: Any, fallback: str = "") -> str:
    """Full block-level HTML: paragraphs, lists, headings, blockquotes."""
    text = strip_emoji(str(value if value not in (None, "") else fallback)).strip()
    if not text:
        return ""
    return _convert(text)


def render_inline(value: Any, fallback: str = "") -> str:
    """Inline HTML with no wrapping <p>. Safe inside a table cell or a chip."""
    text = strip_emoji(str(value if value not in (None, "") else fallback)).strip()
    if not text:
        return ""
    rendered = _convert(text).strip()
    match = _SOLE_PARAGRAPH_RE.match(rendered)
    if match and not _BLOCK_TAG_RE.search(match.group(1)):
        return match.group(1).strip()
    # Multi-block content reached an inline slot. Emitting block tags into a table
    # cell would corrupt the layout, so flatten to a single run instead. Inline
    # emphasis (<strong>, <em>, <code>, <a>) survives; block structure does not.
    flattened = _BLOCK_TAG_RE.sub(" ", rendered)
    return re.sub(r"\s+", " ", flattened).strip()


def render_inline_list(values: Any, limit: int | None = None, separator: str = ", ") -> str:
    """Render a list of `_md` strings into one inline run. For synonyms, collocations."""
    if not isinstance(values, list):
        return render_inline(values)
    items = [render_inline(v) for v in values if str(v or "").strip()]
    if limit is not None:
        items = items[:limit]
    return separator.join(items)


def escape(value: Any) -> str:
    """For NON-`_md` fields: identifiers, slugs, phonetics, URLs. Printed literally."""
    return html.escape(strip_emoji(str(value or "")), quote=True)


def plain_text(value: Any) -> str:
    """Markdown -> plain text. For EPUB metadata, <title>, and PDF bookmarks, where
    no markup is allowed."""
    stripped = re.sub(r"<[^>]+>", "", render_block(value))
    return html.unescape(re.sub(r"\s+", " ", stripped)).strip()


def render_field(data: dict, key: str, *, inline: bool = False, fallback: str = "") -> str:
    """Render `data[key]` by the `_md` suffix rule.

    A key ending in `_md` is rendered as Markdown; anything else is escaped and
    printed literally. Pass the key with or without the suffix — this resolves it.
    """
    if key.endswith("_md"):
        md_key, plain_key = key, key[:-3]
    else:
        md_key, plain_key = f"{key}_md", key

    if md_key in data:
        return render_inline(data[md_key], fallback) if inline else render_block(data[md_key], fallback)
    if plain_key in data:
        return escape(data[plain_key]) or escape(fallback)
    return escape(fallback)

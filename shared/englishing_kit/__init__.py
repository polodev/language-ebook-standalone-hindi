"""
englishing_kit — shared build tools for every language-ebooks course.

A course-specific generator imports from here instead of copy-pasting 1,400 lines
of Python. What lives here is everything that is *not* course-specific:

    config          paths, .env loading, brand constants
    markdown_render Markdown -> HTML for every `*_md` content field
    palettes        the 15-colour rotation used across all books
    fonts           @font-face CSS for the embedded Miriam Libre / Noto Serif Bengali stack
    render          headless-Chrome PDF rendering + EPUB packaging
    imagegen        multi-threaded OpenAI gpt-image generation + manifest

What does NOT live here: page layout. Each course designs its own pages, because a
vocabulary book and an interview course do not look alike and should not be forced to.

Usage from a course folder:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "shared"))
    from englishing_kit import markdown_render, palettes, render
"""

__version__ = "1.0.0"

from . import config, fonts, imagegen, markdown_render, palettes, render  # noqa: F401

__all__ = ["config", "fonts", "imagegen", "markdown_render", "palettes", "render"]

"""The colour system shared by every book.

Premium and colourful is the brief, and the mechanism that delivers it is rotation:
a palette is applied to a run of N items, then the next palette takes over. A reader
flipping the book sees continuous colour movement rather than one accent repeated
for 700 pages.

Each palette has four roles:
    accent  the strong colour: rules, numbers, headings
    deep    a darker shade of accent, for text that must stay readable on white
    soft    a near-white tint, for card and row backgrounds
    chip    a mid tint, for pills and badges

A course may override this list in its supplementary JSON under `design.palettes`.
"""
from __future__ import annotations

from typing import Any

PALETTES: list[dict[str, str]] = [
    {"name": "orange", "accent": "#f35816", "deep": "#9a3412", "soft": "#fff0e8", "chip": "#ffd8c4"},
    {"name": "teal", "accent": "#0f766e", "deep": "#115e59", "soft": "#ecfdf5", "chip": "#a7f3d0"},
    {"name": "blue", "accent": "#2563eb", "deep": "#1e3a8a", "soft": "#eff6ff", "chip": "#bfdbfe"},
    {"name": "magenta", "accent": "#c026d3", "deep": "#86198f", "soft": "#fdf4ff", "chip": "#f5d0fe"},
    {"name": "violet", "accent": "#7c3aed", "deep": "#5b21b6", "soft": "#f5f3ff", "chip": "#ddd6fe"},
    {"name": "rose", "accent": "#e11d48", "deep": "#9f1239", "soft": "#fff1f2", "chip": "#fecdd3"},
    {"name": "amber", "accent": "#d97706", "deep": "#92400e", "soft": "#fffbeb", "chip": "#fde68a"},
    {"name": "emerald", "accent": "#059669", "deep": "#065f46", "soft": "#ecfdf5", "chip": "#a7f3d0"},
    {"name": "cyan", "accent": "#0891b2", "deep": "#155e75", "soft": "#ecfeff", "chip": "#a5f3fc"},
    {"name": "sky", "accent": "#0284c7", "deep": "#075985", "soft": "#f0f9ff", "chip": "#bae6fd"},
    {"name": "indigo", "accent": "#4f46e5", "deep": "#3730a3", "soft": "#eef2ff", "chip": "#c7d2fe"},
    {"name": "fuchsia", "accent": "#a21caf", "deep": "#701a75", "soft": "#fdf4ff", "chip": "#f0abfc"},
    {"name": "pink", "accent": "#db2777", "deep": "#9d174d", "soft": "#fdf2f8", "chip": "#fbcfe8"},
    {"name": "slate", "accent": "#475569", "deep": "#1e293b", "soft": "#f8fafc", "chip": "#cbd5e1"},
    {"name": "lime", "accent": "#65a30d", "deep": "#3f6212", "soft": "#f7fee7", "chip": "#d9f99d"},
]

# Brand ink. Not part of the rotation — these stay constant on every page.
INK = {
    "text": "#111827",
    "muted": "#374151",
    "hairline": "#e5e7eb",
    "page": "#ffffff",
    "brand_orange": "#f35816",
    "brand_navy": "#0f172a",
}


def palette_for(index: int, rotate_every: int = 5, palettes: list[dict[str, str]] | None = None) -> dict[str, str]:
    """Palette for the item at `index` (0-based).

    Items 0-4 get palette 0, items 5-9 get palette 1, and so on, wrapping around.
    """
    table = palettes or PALETTES
    return table[(index // max(1, rotate_every)) % len(table)]


def palettes_from(supplementary: dict[str, Any]) -> list[dict[str, str]]:
    """Course-supplied palettes if present, otherwise the shared default."""
    configured = supplementary.get("design", {}).get("palettes")
    return configured if isinstance(configured, list) and configured else PALETTES

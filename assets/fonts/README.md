# Bundled publication fonts

`fonts.json` is the source of truth for family names, PDF/EPUB stacks, font files,
weights, source provenance, SHA256 hashes and SIL Open Font License 1.1 files.
The renderer verifies font hashes and embeds these exact binaries; no font network
requests or installed system fonts are required.

Miriam Libre and Noto Serif Bengali are the unchanged scaffold binaries. Their
original download revision was not recorded; the manifest explicitly records that
limitation rather than inventing provenance. Their existing OFL files are retained.
Noto Sans Devanagari Regular and Bold were obtained unmodified from the official
notofonts/noto-fonts repository at the pinned revision in `fonts.json`.

`glyph-coverage.json` records the Hindi Foundation source audit: all printable
characters are covered by both regular and bold stacks. This is glyph coverage,
not a substitute for visual shaping checks or bilingual editorial review.

"""Packaging regressions: deterministic archives and fail-closed resources."""
import importlib.util
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
from englishing_kit.render import write_epub, xhtml_page
spec = importlib.util.spec_from_file_location("check_epub", ROOT / "scripts/check_epub.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class EpubTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "book.epub"
        self.options = dict(title="Book", author="Publisher", language="bn", chapters=[("ch001.xhtml", "Chapter 1", xhtml_page("Chapter 1", '<p lang="hi">नमस्ते</p>'))], stylesheet="body { color: black; }", embed_fonts=False, identifier="urn:test:book", modified="2026-09-11T00:00:00Z")

    def test_valid_deterministic_archive(self):
        write_epub(self.path, **self.options)
        first = self.path.read_bytes()
        write_epub(self.path, **self.options)
        self.assertEqual(first, self.path.read_bytes())
        self.assertEqual(checker.check_epub(self.path)["spine_items"], 1)

    def test_missing_requested_assets_fail(self):
        for field in ("extra_images", "extra_fonts", "cover_image"):
            options = dict(self.options)
            missing = self.root / "missing.png"
            options[field] = missing if field == "cover_image" else [missing]
            with self.subTest(field=field), self.assertRaises(FileNotFoundError):
                write_epub(self.path, **options)

    def test_image_filename_collision_fails(self):
        paths = []
        for name in ("a", "b"):
            folder = self.root / name
            folder.mkdir()
            asset = folder / "same.png"
            asset.write_bytes(b"image")
            paths.append(asset)
        with self.assertRaises(ValueError):
            write_epub(self.path, extra_images=paths, **self.options)

    def test_reserved_chapter_name_fails(self):
        self.options["chapters"][0] = ("nav.xhtml", "Chapter", xhtml_page("Chapter", "<p>Hello</p>"))
        with self.assertRaises(ValueError):
            write_epub(self.path, **self.options)

    def test_invalid_xhtml_fails(self):
        self.options["chapters"][0] = ("ch001.xhtml", "Chapter", "<html><broken></html>")
        with self.assertRaises(Exception):
            write_epub(self.path, **self.options)

    def test_missing_default_font_fails(self):
        self.options["embed_fonts"] = True
        with patch("englishing_kit.render.fonts.epub_font_files", return_value=[self.root / "missing.ttf"]):
            with self.assertRaises(FileNotFoundError):
                write_epub(self.path, **self.options)

    def test_parent_path_chapter_fails(self):
        self.options["chapters"][0] = ("../escape.xhtml", "Chapter", xhtml_page("Chapter", "<p>Hello</p>"))
        with self.assertRaises(ValueError):
            write_epub(self.path, **self.options)

    def test_invalid_build_preserves_existing_archive(self):
        write_epub(self.path, **self.options)
        original = self.path.read_bytes()
        with self.assertRaises(FileNotFoundError):
            write_epub(self.path, cover_image=self.root / "missing.png", **self.options)
        self.assertEqual(original, self.path.read_bytes())

    def test_checker_rejects_missing_image(self):
        self.options["chapters"][0] = ("ch001.xhtml", "Chapter", xhtml_page("Chapter", '<img alt="missing" src="images/missing.png"/>'))
        write_epub(self.path, **self.options)
        with self.assertRaisesRegex(ValueError, "missing reference"):
            checker.check_epub(self.path)

    def test_checker_rejects_missing_font(self):
        self.options["stylesheet"] = "@font-face { src: url('fonts/missing.ttf'); }"
        write_epub(self.path, **self.options)
        with self.assertRaisesRegex(ValueError, "missing reference"):
            checker.check_epub(self.path)

    def test_checker_rejects_missing_fragment(self):
        self.options["chapters"][0] = ("ch001.xhtml", "Chapter", xhtml_page("Chapter", '<a href="#missing">Here</a>'))
        write_epub(self.path, **self.options)
        with self.assertRaisesRegex(ValueError, "missing fragment"):
            checker.check_epub(self.path)


if __name__ == "__main__":
    unittest.main()

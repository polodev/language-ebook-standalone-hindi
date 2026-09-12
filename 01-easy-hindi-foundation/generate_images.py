#!/usr/bin/env python3
"""Generate this book's declared artwork using the repo-local image pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT / "shared"))
from englishing_kit import config, imagegen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 10:
        parser.error("workers must be between 1 and 10")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/manage.py"), "assemble", "--book", BOOK.name],
        cwd=ROOT, check=True,
    )
    declaration = json.loads((BOOK / "generated/image-declaration.json").read_text())
    declaration["default_quality"] = "low"
    declaration["model"] = "gpt-image-2"
    for entry in declaration["images"]:
        entry["quality"] = "low"
    path = BOOK / f"bn-{BOOK.name}-images.json"
    path.write_text(json.dumps(declaration, ensure_ascii=False, indent=2) + "\n")
    specs = imagegen.specs_from_json(path)
    for spec in specs:
        spec.validate()
    if config.image_model() != declaration["model"]:
        raise SystemExit("Set OPENAI_IMAGE_MODEL=gpt-image-2 in the repository .env")
    print(f"{len(specs)} images; model={declaration['model']}; quality=low; workers={args.workers}", flush=True)
    if args.dry_run:
        print("Dry run: declarations validated; no API calls made.")
        return
    imagegen.generate_all(specs, BOOK, max_workers=args.workers)


if __name__ == "__main__":
    main()

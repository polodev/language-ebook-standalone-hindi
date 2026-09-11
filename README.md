# Hindi ebooks for Bangladeshi learners

Four book plans: Foundation (60 chapters), Intermediate (60), Advanced (60), and Vocabulary 7000+ Words & Phrases (234 chapters, 7,020 planned vocabulary targets). Plans and blank templates are not completed manuscripts; consult actual chapter files and validation for current progress.

Language: Standard Hindi, Devanagari. Locale: hi; language tag: hi-IN. Publisher: Englishing.app.

## Start authoring

Open the appropriate JSON prompt file and use the string for the desired chapter range in ChatGPT with access to this repository:

- [Easy Hindi Foundation](01-chatgpt-prompt.json) — 60 chapter plans; [single instruction file](01-easy-hindi-foundation/INSTRUCTIONS.md).
- [Easy Hindi Intermediate](02-chatgpt-prompt.json) — 60 chapter plans; [single instruction file](02-easy-hindi-intermediate/INSTRUCTIONS.md).
- [Easy Hindi Advanced](03-chatgpt-prompt.json) — 60 chapter plans; [single instruction file](03-easy-hindi-advanced/INSTRUCTIONS.md).
- [Easy Hindi Vocabulary: 7000+ Words & Phrases](04-chatgpt-prompt.json) — 234 chapter plans; [single instruction file](04-easy-hindi-vocabulary-7000-words/INSTRUCTIONS.md).

Each book's INSTRUCTIONS.md is its sole authoring instruction file. Read book.json for all chapter plans and chapter-template.json for the data shape. There is no separate shared authoring guide to reconcile. Each JSON value requests continuous completion of its chapter range, checks using available tools, and one pull request to main per chapter batch for the user to review and merge. Each 60-chapter book has six 10-chapter prompts; the 234-chapter vocabulary book has 24 prompts, ending at 231–234. Copy the decoded string value for the desired range as the ChatGPT request. Author chapter JSON and matching image-prompt text; the manager generates images and builds publications. If the connection cannot write, it must return complete files with exact destinations and report that Git delivery is incomplete.

## Foundation artwork

Generate or resume all 122 Foundation images (120 reading illustrations, cover and banner):

```bash
python3 01-easy-hindi-foundation/generate_images.py --dry-run --workers 10
python3 01-easy-hindi-foundation/generate_images.py --workers 10
```

The script validates and assembles the manuscript, saves the image declaration JSON, and calls the existing OpenAI image pipeline with at most ten concurrent requests. Model is `gpt-image-2`, quality is explicitly `low`; sizes come from the declaration. Completed image files are reused on rerun. Configure `OPENAI_API_KEY` privately in the ignored repository `.env`; never commit credentials. Generated artwork and its actual prompt manifest live under the book’s `assets/` folder. Artwork generation does not mark the book published.

## Manager tools

Python 3.10+; authoring management uses the standard library.

```bash
python3 scripts/manage.py status
python3 scripts/manage.py validate
python3 scripts/manage.py packet --book 01-easy-hindi-foundation --chapter 1
python3 scripts/manage.py validate --book 01-easy-hindi-foundation --complete
python3 scripts/manage.py assemble --book 01-easy-hindi-foundation
python3 -m unittest discover -s tests
```

Partial validation allows planned missing chapters; complete validation and assembly fail until every required chapter exists. Passing structural checks is not independent language approval. Generated packets and assembly output are ignored by Git. Install requirements.txt only for later render/image work; secrets belong in .env.

[The production playbook](docs/BUILD-PLAYBOOK.md) is for the manager. Final publication requires the new layout adapter, target fonts/licences, artwork and visual verification of PDF/EPUB outputs. Vendored primitives are reusable infrastructure, not a finished publication renderer. This repository works independently and can also be checked out as a submodule of the management repository.

## Hindi Foundation review build

All 60 chapters and 122 original illustrations are available on this content branch. Install `requirements.txt`, Google Chrome/Chromium and Poppler, then run:

```bash
python3 01-easy-hindi-foundation/generate_pdfs.py
python3 01-easy-hindi-foundation/make_previews.py
python3 -m unittest discover -s tests -q
python3 scripts/check_epub.py 01-easy-hindi-foundation/output/07-easy-hindi-foundation-bn-desktop.epub
```

Desktop PDFs use A4 portrait (210 × 297 mm), with sentence and vocabulary tables showing Hindi, pronunciation/romanization and Bangla meaning. The build creates six PDFs and two EPUBs under the ignored book `output/` folder. Use `--only OUTPUT_FILENAME` to rebuild one edition. Fonts and illustrations are local; rebuilding requires no API key. These are review editions; independent Hindi/Bangla editorial review remains pending. See the book’s `qa/release.json` for artifact checks.

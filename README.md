# Hindi ebooks for Bangladeshi learners

Four independent-book plans: Foundation (60 chapters), Intermediate (60), Advanced (60), Vocabulary 7000+ Words & Phrases (234 chapters, 7,020 future targets). This repository is ready for authoring, not a completed manuscript or tested publication renderer. No lesson prose has been written in this setup.

Language: Standard Hindi, Devanagari. Locale: hi; language tag: hi-IN. Publisher: Englishing.app. Five script items in EVERY chapter, plus two number cards every third chapter. Foundation begins with natural 2–4-word sentences and gradual progression. Chinese/kana/Hangul use appropriate script units. Each chapter has two distinct readings and two topic-specific image prompts.

## Start an authoring session

Give ChatGPT access to this repository, then use docs/CHATGPT-START-HERE.md. All instructions and chapter plans are tracked here; no access to the original English repository is needed. If the connection can only read files, return complete JSON with the exact destination path; the manager can import it. Do not claim a GitHub write occurred unless it actually did.

```text
Read AGENTS.md, language.json, docs/AUTHORING.md, docs/CONTENT-CONTRACT.md,
docs/IMAGE-GUIDELINE.md, and 01-easy-hindi-foundation/OUTLINE.md and book.json.
Author Foundation chapter 1 using chapter-template.json. Follow zero-background
script teaching, five script cards and the 2–4-word opening rule. Write both full
readings and matching image prompts. Save the planned chapters/ch001.json file
if writing is available; otherwise return the complete JSON with its exact path.
Mark only a complete draft as drafted. Do not generate images or publication files.
```

## Manager tools

Python 3.10+; the authoring manager uses only the standard library.

```bash
python3 scripts/manage.py status
python3 scripts/manage.py validate
python3 scripts/manage.py packet --book 01-easy-hindi-foundation --chapter 1
python3 scripts/manage.py validate --book 01-easy-hindi-foundation --complete
python3 scripts/manage.py assemble --book 01-easy-hindi-foundation
```

Partial validation allows planned missing files; complete validation and assembly intentionally fail until all chapters exist. They do not confer editorial approval. Packets/assembly are derived under generated/ and ignored by Git. Install requirements.txt only for later render/image work; secrets belong in .env. Production work is detailed in docs/BUILD-PLAYBOOK.md, and reference findings in docs/REFERENCE-ANALYSIS.md.

This is a dedicated Git repository. No symlinks, monorepo checkout dependency, parent Git repository or shared runtime outside this folder is required. Final publication requires implementing the new layout adapter, bundling target fonts/licences, generating artwork and verifying every output. Existing vendored primitives are reusable infrastructure, not a claim those steps are finished.

Please analyze and complete the entire manuscript of Easy Hindi Foundation for Bangladeshi Bangla-speaking learners, then git commit and push the completed source changes to this language repository's main branch.

Exact book URL: https://github.com/polodev/language-ebook-standalone-hindi/tree/main/01-easy-hindi-foundation
Single authoring instruction file: https://github.com/polodev/language-ebook-standalone-hindi/blob/main/01-easy-hindi-foundation/INSTRUCTIONS.md

Read this book's INSTRUCTIONS.md as the sole authoring instruction source. Use its book.json chapter plans and chapter-template.json as data, and inspect existing chapter files and progress before editing. The instructions contain the complete content style, pronunciation, reading, illustration-prompt, schema and review requirements. Preserve correct completed work. Work on this book only; do not write or change other books, validators or requirements to make checks pass.

Treat this as one continuous job covering ALL 60 planned chapters. Analyze every chapter plan, then finish missing or incomplete chapters in manageable batches without asking me to say “continue.” Do not stop after a sample or a batch, reduce the chapter count, or replace lessons with outlines, summaries or placeholders. Maintain an accurate authoring-progress.json checkpoint inside this book, recording completed IDs, validated IDs, failed checks, corrections and next unfinished chapter from actual files and results. Do not schedule background jobs or promise unattended continuation.

After every batch, run and fix the reported failures:
python3 scripts/manage.py validate --book 01-easy-hindi-foundation

Before reporting completion, confirm every planned chapter file exists, has the correct unique ID and satisfies every requirement in INSTRUCTIONS.md. Audit pronunciation coverage, natural language and translations as well as structural counts. Compute the actual complete chapter and section inventory. All 60/60 chapters must pass; a tooling test alone does not prove content is complete. Run:
python3 -m unittest discover -s tests
python3 scripts/manage.py validate --book 01-easy-hindi-foundation --complete
python3 scripts/manage.py assemble --book 01-easy-hindi-foundation

Git commit and push are required and authorized. Verify this repository, use main, and pull the latest main without discarding existing work. Stage only this book's intended source/progress changes. Commit using a human-readable local date/time and actual staged-diff counts, for example: Thu Sep 10, 5:11pm — 4 files modified, 2 files added, 1 file deleted. Run git push origin main, verify remote main contains the commit, and report its SHA and GitHub commit URL. Do not force-push or commit secrets or generated outputs. Do not substitute a pull request or ask again for authorization.

Report the actual 60/60 completion result, inventory, checks and outcomes, and remaining independent editorial-review needs. This is manuscript authoring; artwork generation and PDF/EPUB production belong to the manager. If access, tooling or a platform limit genuinely blocks completion, preserve completed files and an exact resume checkpoint, identify unfinished chapter IDs and state the blocker honestly. Return completed files with exact paths if writing is unavailable. Never claim successful tests, completed chapters or a push without evidence.

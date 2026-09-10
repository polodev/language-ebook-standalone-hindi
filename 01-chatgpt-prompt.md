Please analyze this book, read all its instructions, complete the entire book manuscript, then git commit and push the book changes to this language repository’s main branch.

Exact book URL:
https://github.com/polodev/language-ebook-standalone-hindi/tree/main/01-easy-hindi-foundation

Repository:
https://github.com/polodev/language-ebook-standalone-hindi

Book: Easy Hindi Foundation
Target language/variety: Standard Hindi, Devanagari (hi-IN).
Audience: Bangladeshi Bangla-speaking adult learners.

First read the repository’s AGENTS.md, language.json, docs/AUTHORING.md, docs/CONTENT-CONTRACT.md, docs/IMAGE-GUIDELINE.md, and this book’s OUTLINE.md, book.json, chapter-template.json and supplementary.json. Analyze any existing chapter files, rosters and progress before writing. Preserve correct completed work and finish the missing or incomplete work in this book only.

The reader starts with ZERO Hindi background and only knows English alphabet shapes. Start with natural 2–4-word sentences (or equivalent short language-aware units), then increase difficulty gradually according to book.json. Never let the readings exceed the opening chapter’s language load.

Complete all 60 planned chapters in order. Every chapter needs exactly five script-learning/review items; two additional number cards where the chapter plan requires them; 20 essential sentences; 10 vocabulary entries; a complete Bangla-supported story/article; a DIFFERENT target-language story/article with its full Bangla meaning; six speaking/recall tasks with model answers; and two image prompts matching the actual readings. Keep native script, romanization, Bangla pronunciation and natural Bangla meaning together as the contract requires. Teach the language’s actual writing system; never assume its sounds work like English or invent alphabet letters to fill the five-item quota.

For each chapter, write attractive, specific illustration prompts based on its topic and the actual scenes or article ideas. Follow the stable image keys and visual guideline. Require no readable text in generated art; letters, digits and titles will be typeset using real fonts later. Complete this book’s cover/banner prompt declarations too. Write prompt text only at this stage, not bitmap images.

Save complete UTF-8 JSON in this book’s planned chapters/chNNN.json paths, following its own schema and IDs. Keep lesson prose in JSON, never in Python. Do not substitute outlines, summaries, repetitive filler or placeholders for finished lessons. Respect the _md suffix rule and prohibition on raw HTML. Update source/status records truthfully and keep changes scoped to this book.

If execution is available, run:
python3 scripts/manage.py validate --book 01-easy-hindi-foundation --complete
python3 scripts/manage.py assemble --book 01-easy-hindi-foundation

Fix reported structural issues and review the language, translations, script progression and distinct readings. Structural validation is not independent bilingual approval. Do not mark the book published or claim that images, PDFs or EPUBs were generated; production belongs to the manager after content review.

Git delivery is required and authorized: work on the main branch of this language repository, commit the authored book changes, and push them to origin/main. Before editing, verify the repository and branch and pull the latest main without discarding existing work. After validation, stage only this book’s intended source changes, run git commit, and run git push origin main. Use a human-readable local date/time and staged-diff counts in the commit message, for example: Thu Sep 10, 5:11pm — 4 files modified, 2 files added, 1 file deleted. Do not commit secrets or generated outputs, and do not force-push. The requested Git delivery is directly to main; do not substitute a pull request or another branch. Verify the remote main contains the pushed commit and report its SHA and GitHub commit URL. This instruction authorizes the commit and push; do not ask for confirmation again. If GitHub write access is unavailable or a push is rejected, report the actual blocker and preserve/return the completed files; never claim a push succeeded without verification.

Treat this as ONE CONTINUOUS END-TO-END JOB to complete all 60 chapters. Analyze all 60 existing chapter plans in book.json before starting, then continue chapter by chapter or in manageable batches until the full manuscript and Git delivery are finished. Do not stop after an outline, sample, first chapter or batch. Do not ask me to say “continue” between chapters or batches. Do not reduce the chapter count or replace full chapters with summaries to fit one response. A batch is a working checkpoint, not the end of this task. Keep working in the active task; do not create scheduled or background jobs.

Maintain a book-specific completion checklist in this book’s authoring-progress.json. Record the planned chapter IDs, completed and structurally validated IDs, failed checks, corrections and next unfinished chapter. Update it from actual files and test results, not estimated progress. After each chapter or batch, run partial validation, fix failures and continue to the next unfinished chapter:
python3 scripts/manage.py validate --book 01-easy-hindi-foundation

Final completion gates — all must be satisfied before reporting the book complete:
1. Confirm every planned chapter from ch001 through ch060 exists, with no missing, duplicate or unindexed chapter files and no empty/template-only sections. The result must be 60/60 complete chapters.
2. Audit each chapter’s native-language text, Bangla support, five script items, scheduled number cards, required sentences/vocabulary, two distinct complete readings, full Bangla meaning, six speaking tasks and two reading-image prompts. Review language quality and gradual difficulty, not just array lengths. Builder/review chapters have the same mandatory core.
3. Compute the inventory from actual authored files: 1,200 essential sentences; 600 vocabulary entries with valid source-sentence references; 300 script-practice items; 40 number cards; 60 bridge readings and 60 different target-language readings; 360 speaking tasks; and 120 reading-image prompts, plus cover and banner declarations. Counts are structural evidence, not independent linguistic approval.
4. Run these checks, fix failures and rerun the affected checks:
python3 -m unittest discover -s tests
python3 scripts/manage.py validate --book 01-easy-hindi-foundation --complete
python3 scripts/manage.py assemble --book 01-easy-hindi-foundation
The unit tests check tooling, not whether the manuscript is complete; the complete-book validator and the actual chapter audit are both required. Do not weaken checks, delete failing chapters or change required totals to obtain a pass.
5. Commit the completed source changes and truthful progress/check records, push to this language repository’s main branch, and verify the remote commit as requested above. Report 60/60 completed chapters, computed inventory, test commands and actual results, commit SHA, GitHub commit URL and remaining editorial-review needs. Content completion does not mean publication approval.

If a genuine platform limit, missing tool capability or external blocker prevents further work, preserve complete chapter files and an exact resume checkpoint; explicitly mark the job unfinished and list the remaining chapter IDs. Never claim unattended continuation, successful tests or a GitHub push that did not happen. If GitHub writing is unavailable, return the complete files with exact destination paths for the manager to import and state that Git delivery remains incomplete.

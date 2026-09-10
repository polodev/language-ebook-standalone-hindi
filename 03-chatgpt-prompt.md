Please analyze this book, read all its instructions, complete the entire book manuscript, then git commit and push the book changes to this language repository’s main branch.

Exact book URL:
https://github.com/polodev/language-ebook-standalone-hindi/tree/main/03-easy-hindi-advanced

Repository:
https://github.com/polodev/language-ebook-standalone-hindi

Book: Easy Hindi Advanced
Target language/variety: Standard Hindi, Devanagari (hi-IN).
Audience: Bangladeshi Bangla-speaking adult learners.

First read the repository’s AGENTS.md, language.json, docs/AUTHORING.md, docs/CONTENT-CONTRACT.md, docs/IMAGE-GUIDELINE.md, and this book’s OUTLINE.md, book.json, chapter-template.json and supplementary.json. Analyze any existing chapter files, rosters and progress before writing. Preserve correct completed work and finish the missing or incomplete work in this book only.

This book follows Intermediate. Follow its planned B2–C1; optional C2-style stretch progression with natural Hindi grammar, register and situations. Continue script review, decoding and spelling practice at this level instead of restarting the alphabet. Builder and review chapters must retain all core sections.

Complete all 60 planned chapters in order. Every chapter needs exactly five script-learning/review items; two additional number cards where the chapter plan requires them; 15 essential sentences; 10 vocabulary entries; a complete Bangla-supported story/article; a DIFFERENT target-language story/article with its full Bangla meaning; six speaking/recall tasks with model answers; and two image prompts matching the actual readings. Keep native script, romanization, Bangla pronunciation and natural Bangla meaning together as the contract requires. Teach the language’s actual writing system; never assume its sounds work like English or invent alphabet letters to fill the five-item quota.

For each chapter, write attractive, specific illustration prompts based on its topic and the actual scenes or article ideas. Follow the stable image keys and visual guideline. Require no readable text in generated art; letters, digits and titles will be typeset using real fonts later. Complete this book’s cover/banner prompt declarations too. Write prompt text only at this stage, not bitmap images.

Save complete UTF-8 JSON in this book’s planned chapters/chNNN.json paths, following its own schema and IDs. Keep lesson prose in JSON, never in Python. Do not substitute outlines, summaries, repetitive filler or placeholders for finished lessons. Respect the _md suffix rule and prohibition on raw HTML. Update source/status records truthfully and keep changes scoped to this book.

If execution is available, run:
python3 scripts/manage.py validate --book 03-easy-hindi-advanced --complete
python3 scripts/manage.py assemble --book 03-easy-hindi-advanced

Fix reported structural issues and review the language, translations, script progression and distinct readings. Structural validation is not independent bilingual approval. Do not mark the book published or claim that images, PDFs or EPUBs were generated; production belongs to the manager after content review.

Git delivery is required and authorized: work on the main branch of this language repository, commit the authored book changes, and push them to origin/main. Before editing, verify the repository and branch and pull the latest main without discarding existing work. After validation, stage only this book’s intended source changes, run git commit, and run git push origin main. Use a human-readable local date/time and staged-diff counts in the commit message, for example: Thu Sep 10, 5:11pm — 4 files modified, 2 files added, 1 file deleted. Do not commit secrets or generated outputs, and do not force-push. The requested Git delivery is directly to main; do not substitute a pull request or another branch. Verify the remote main contains the pushed commit and report its SHA and GitHub commit URL. This instruction authorizes the commit and push; do not ask for confirmation again. If GitHub write access is unavailable or a push is rejected, report the actual blocker and preserve/return the completed files; never claim a push succeeded without verification.

Work through the whole requested book. At the end, report completed chapter IDs, actual counts, changed file paths, checks actually run and any remaining editorial work. If a session limit prevents finishing, save only complete chapter payloads, report exactly what remains and the next chapter to resume; never claim the full book is complete. If GitHub writing is unavailable, return the complete files with exact destination paths for the manager to import, and do not claim a commit or upload occurred.

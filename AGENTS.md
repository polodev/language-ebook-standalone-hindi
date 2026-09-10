# Hindi standalone book workspace

This is an independent repository for Bangladeshi learners of Hindi (hi-IN). Read README.md, language.json, docs/AUTHORING.md, docs/CONTENT-CONTRACT.md, docs/IMAGE-GUIDELINE.md, and the selected book's OUTLINE.md.

The owner uses ChatGPT with GitHub access to author lessons later. The manager scaffolds, validates, coordinates images and builds publications; do not author lesson content unless the owner explicitly assigns that role. Current state is scaffolded, not drafted or published. Work in this checkout only; never require the original language-ebooks repository to assemble or build.

Four books: Foundation, Intermediate, Advanced and Vocabulary 7000+ Words & Phrases. Each has its own JSON source map and chapter profile. Every chapter includes FIVE script items, scheduled TWO additional number cards, sentences, vocabulary, two distinct readings, six speaking tasks and two matching image prompts. Builder/review chapters have no exemption. Foundation starts with natural 2–4-word lines (language-aware equivalents for unspaced scripts), then gradually increases complexity. Follow language.json instead of transplanting English alphabet assumptions.

JSON is source of truth. Use Python 3 for structural edits; UTF-8, ensure_ascii=False, indent=2. *_md fields are Markdown; all other strings literal; no raw HTML. Stable IDs are joins, not translated labels. Colours, titles, copy, URLs and prompts live in JSON, never new Python constants. Publisher is Englishing.app; all book titles begin Easy; Bengali book titles transliterate. Generated images contain no readable text; glyphs and titles use actual fonts.

Keep content, editorial, image and publication statuses separate. Never claim blank templates are lessons. Validate after authoring. Production requires bilingual review, target-font coverage, artwork and visual PDF/EPUB checks. Do not commit secrets or regenerable output. Follow the user's requested chapter/batch scope. No paid images, background jobs or publishing just because authoring was requested. The user has authorized this initial repository creation, commit and push; do not request that authorization again.

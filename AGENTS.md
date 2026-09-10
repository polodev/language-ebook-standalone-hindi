# Hindi standalone book workspace

This independent repository prepares four books for Bangladeshi learners of Hindi (hi). For authoring, read only the selected book's INSTRUCTIONS.md for content, schema, language, image-prompt and completion requirements. Its book.json and chapter-template.json are the chapter plan and data shape. The four root NN-chatgpt-prompt.md files are copy-ready task requests. Do not recreate competing authoring instructions elsewhere.

The owner assigns ChatGPT to author content. The manager scaffolds, validates, coordinates artwork and builds publications; do not author lessons unless explicitly assigned. Work in this checkout; no original language-ebooks checkout or external shared runtime is required. Respect the user's book or batch scope. Existing plans and templates are not completed manuscripts.

JSON is the source of truth. Use Python 3 for structural file edits and UTF-8 JSON with ensure_ascii=False, indent=2. Keep stable IDs. Lesson prose, colours, titles, copy, URLs and image prompts belong in JSON, not Python constants. Publisher is Englishing.app; titles begin Easy and Bengali titles transliterate. Never commit secrets, .env, generated/, output/ or caches. Do not modify the read-only reference project.

Keep content, editorial, image, build and publication statuses separate. Validate authored work and report real results. Production needs independent bilingual review, font coverage, artwork and visual PDF/EPUB checks; docs/BUILD-PLAYBOOK.md is manager-only. Authoring does not authorize paid images, scheduled/background jobs or publication. Explicitly requested Git commit/push is authorized; do not ask again. Preserve unrelated work and never claim Git delivery without verification.

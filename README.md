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

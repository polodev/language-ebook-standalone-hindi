# Easy Hindi Advanced — authoring instructions

This is the **single authoritative instruction file for this book**. `book.json` holds its ordered chapter plans and stable paths/IDs; `chapter-template.json` is an empty data-shape reference; `supplementary.json` holds presentation settings. These are data files, not additional authoring guides. Work on this book only, preserving its chapter topics and correct existing work.

Target language: **Hindi** (hi-IN). Variety: Standard Hindi, Devanagari. Audience: Bangladeshi Bangla-speaking adults who know English letter shapes but may not recognize any target-language letters or words. Pronunciation support is mandatory throughout this book, including review, builder and later chapters. Never assume that a familiar-looking Latin letter has its English sound.

## 1. Complete the assigned chapter range continuously

The full book contains **60 chapters**. When the task specifies a range, complete only that range continuously, checkpointing each finished chapter; do not begin the next range. Preserve correct existing chapters and use earlier chapters for continuity. Only an explicit whole-book task requires all 60 chapters in one assignment. Never replace lessons with outlines or placeholders. Record actual requested/completed/unfinished IDs and checks in this book’s `authoring-progress.json`. A finished batch is not a finished book.

Advanced develops the communicative goals in its chapter plans while keeping full script and pronunciation help. Its pure-language readings use moderate intermediate-level language, not dense advanced articles.

## 2. The same chapter order every time

1. **Exactly 20 essential sentences.** Native text with Bangla pronunciation immediately after every target-language word, followed by whole-sentence pronunciation and natural Bangla meaning. Keep sentences useful and natural. Retain romanization as an additional aid; it never replaces Bangla pronunciation.
2. **Vocabulary from those 20 sentences.** Select the useful vocabulary needed to understand those sentences; the count is flexible, not a forced ten-entry quota. Cover the important unfamiliar words and expressions meaningfully. At least one genuine entry is required, and all entries must be drawn from the sentence set. Each entry includes meaning, pronunciation, its source sentence ID and the exact form occurring there. Explain useful grammar/register briefly in Bangla. Do not import English grammar categories that do not fit this language.
3. **A Bangla + Hindi mixed story or article.** Use natural Bangla narration with target-language words/phrases from the lesson. Use actual Markdown bold for each target word and put its Bangla pronunciation immediately after it: `**Hello** (হ্যালো)`. Repeat this for every occurrence of every target-language word, not only the first occurrence. Use structured segments so the renderer can reliably distinguish Bangla narration, target text and pronunciation. Both kinds must actually occur; an entirely Bangla passage is not the mixed reading.
4. **A tiny pure-Hindi story or article: 4–8 authored lines.** Each line is one short sentence, not a long paragraph that happens to wrap. Source text uses the target language; render word-by-word Bangla pronunciation after each word. Then show the **complete article/story pronunciation in Bangla**, and then its **complete Bangla meaning**, in that order. The mixed and pure readings share the topic but use different situations or viewpoints. Use moderate intermediate-level sentences, at most 12 word/learning units per line, with a clear small situation and only modest grammatical linking. Do not turn this tiny reading into a dense C1/C2 essay.
5. **Letters and optional numbers.** Pick exactly five appropriate letters/script units, varying or randomly selecting within the chapter’s script-learning stage. They can be new items or useful review; do not invent new letters after the alphabet is covered. Save the chosen items in chapter JSON so rebuilding does not randomly change them. Add **two or three number cards, or `null` for no numbers**. There is no every-third-chapter schedule and no fixed book-wide number-card total. Each letter/sign and each spoken number has immediate Bangla pronunciation. Number cards also show digits, the complete spoken number and Bangla meaning.
6. **Practice tasks.** Six short speaking/recall/application tasks in Bangla with usable model responses. Every target-language word in a model or extra example also has immediate Bangla pronunciation. Include visible answers for a static book.

Every chapter also supplies two matching reading-image prompts. Builder practice is optional extra material after the required sections; it never replaces the 20 sentences, readings, pronunciation, script practice or tasks.

## 3. Pronunciation after every target word

This rule applies to titles, all 20 sentences, vocabulary, mixed-reading target spans, every line of the pure reading, number words, practice models, synonyms, collocations and optional builder lines. Put the pronunciation directly after the associated word, not only at the end of a sentence or in a distant glossary. A whole-line pronunciation alone is insufficient. The full article pronunciation remains required in addition to the inline cues.

Represent word-level support with `word_pronunciations`: an ordered array of `{target, bangla_pronunciation, separator_after}`. Each `target` is one correctly segmented native word with its attached punctuation; no embedded whitespace. `separator_after` is the original whitespace after that word, or `""` for no separator. Concatenating every `target + separator_after` must exactly reproduce the associated native string. For unspaced scripts, segment actual lexical/learning units without adding spaces to native spelling; native-language review must verify those boundaries. Code-point count is not word count.

The renderer displays each native word followed immediately by its parenthesized Bangla pronunciation and preserves the source word order. In a mixed reading it bolds native words and keeps pronunciation visually distinct. Native-only source text stays separate from pronunciation metadata. Keep native `target` fields plain. Store the mixed article’s actual bold Markdown in its `text_md` field as the exact mirror described below; do not insert Markdown into native fields themselves. No raw HTML is allowed in JSON.

Keep Bangla explanations and instructions in Bangla; put target-language examples in the structured annotated fields. Do not hide unannotated native examples inside a Bangla prose field. Pronunciation is a practical approximation: explain important sound distinctions simply where Bangla cannot represent them accurately. Never taper or remove support because the book/chapter is labelled Intermediate or Advanced.

## 4. Exact JSON contract

Save one complete object in each path from `book.json`, normally `chapters/chNNN.json`. Empty templates are not completed chapters. The `_md` suffix means Markdown; other strings are literal. Preserve UTF-8 with `ensure_ascii=False, indent=2` for programmatic JSON edits.

- Chapter identity: `chapter_id`, `status` (`drafted` or genuinely `reviewed`), `title_target`, `title_bangla_pronunciation`, `title_word_pronunciations`, `title_bengali`, `goal_bengali_md`.
- `sentences`: exactly 20 objects `{id, target, romanization, bangla_pronunciation, word_pronunciations, meaning_bengali_md}`. IDs and native sentences are unique within the chapter. The word array supplies segmentation; no separate `learning_units` copy is needed.
- `vocabulary`: objects `{id, target, type, romanization, bangla_pronunciation, word_pronunciations, meaning_bengali_md, source_sentence_id, source_form}`. `source_form` is an exact occurrence in its source sentence, allowing a taught lemma to have a natural inflection there. It is internal metadata, not an unannotated display example. Optional `collocations` and `synonyms` are arrays of annotated objects `{target, bangla_pronunciation, word_pronunciations}`, never bare native strings.
- `bridge_reading`: `{mode, title_bengali, scene_summary, segments, text_md}`. `mode` is `story` or `article`. Each segment is either `{kind: "bangla", text}` or `{kind: "target", target, bangla_pronunciation, word_pronunciations}`. Include both kinds. The renderer highlights every target-kind word. The segments are the canonical text source. `text_md` is a required, exactly validated Markdown mirror: plain Bangla narration, and every native word as `**word** (Bangla pronunciation)`. Generate it with `mixed_reading_markdown(segments)` from `scripts/manage.py`; the validator recomputes it and rejects missing bold, missing/wrong pronunciation or any difference from the segments. Do not independently rewrite this mirror. Literal Markdown characters in source text must be escaped by that helper.
- `target_reading`: `{mode, title_bengali, scene_summary, lines, bangla_pronunciation, meaning_bengali_md}`. `lines` contains exactly 4–8 objects `{target, bangla_pronunciation, word_pronunciations}`. Its top-level `bangla_pronunciation` contains the complete reading’s pronunciation, and `meaning_bengali_md` the full meaning. Do not add a separate duplicate `text`, `text_md` or root word array.
- `script_practice`: exactly five objects `{item_id, mode, target, bangla_pronunciation, explanation_bengali_md, practice_bengali_md}`. `mode` is `new`, `review` or `application`. Reuse the stable item ID when reviewing it; five distinct items inside one chapter. A script card shows a letter/sign or short script combination, not an unannotated sentence.
- `number_practice`: `null`, or an array of exactly two or three objects `{display, target, bangla_pronunciation, word_pronunciations, meaning_bengali_md, system}`. `display` holds the digits and `target` the full spoken number. Do not use an empty array, a single card or digits as a pronunciation shortcut.
- `speaking_practice`: six objects `{prompt_bengali_md, model_target, model_bangla_pronunciation, model_word_pronunciations, model_meaning_bengali_md}`.
- `image_prompts`: exactly two objects in bridge/pure order, `{key, reading, subject, style}`. `reading` is `bridge_reading` or `target_reading`; keys are `chNNN_bridge_reading_01` and `chNNN_target_reading_01`.
- Optional `additional_practice`: objects with `explanation_bengali_md` plus each of `base_target`, `base_bangla_pronunciation`, `base_word_pronunciations`, `expanded_target`, `expanded_bangla_pronunciation`, `expanded_word_pronunciations`, `polished_target`, `polished_bangla_pronunciation`, `polished_word_pronunciations`. No native-only builder exception.

For this book there is no fixed vocabulary total. Choose entries for learning value and their real use in the 20 sentences, and report the actual inventory. Preserve legitimate inflection differences using the exact `source_form`; a substring match alone does not prove a semantically correct relationship.

## 5. Language and difficulty

Begin with independent vowels and high-utility consonants; then dependent vowel signs, combinations, nasal signs and common conjuncts. Compare with familiar Bangla only when accurate. Do not equate Devanagari shape recognition with Bangla literacy. Teach inherent-vowel behaviour and schwa deletion in encountered words.

Numbers: Show international digits and introduce Devanagari digits gradually, with Hindi number words.

Follow each chapter’s script focus, selecting useful new/review items rather than exhausting the alphabet in one chapter. All selected items are fixed authoring data; do not add runtime randomness. Teach recognition and useful speech together. Readers may still need help recognizing print in any of the four books.

Foundation opening sentences normally have 2–4 words/short language-aware units, with natural one-word greetings allowed. Respect `sentence_max_units` in the chapter plan as difficulty grows. Mixed-reading utterances should reuse learned words at the chapter’s difficulty. A pure-reading line must fit this book’s `pure_reading_max_units`, and any smaller Foundation chapter ceiling. Shortness is not permission to use unnatural fragments; grammar, register and actual speaking usefulness need editorial review.

Use original, plausible examples for Bangladeshi adults, including destination-language settings when relevant. Use natural Bangla. Invented scenarios remain fictional; do not fabricate factual evidence, citations or professional advice. CEFR-style labels are editorial targets, not certificates or guaranteed outcomes.

## 6. Attractive images and readable layout

Write one visual prompt for each finished reading, based on its topic and exact scene/article idea. Describe setting, characters/actions or objects, framing, lighting and a clear focal point. Make the two images meaningfully different. Follow the bright, coherent style in `supplementary.json`; avoid clutter, dark generic scenes and stereotypes.

Every image subject must include **“No readable text, no labels, no signage, no watermark.”** Generated art never teaches letter shapes, digits, pronunciation or titles. The layout uses real embedded fonts for those. Chapter images are `1536x1024`; cover is `1024x1536` with the upper third calm; banner is `1536x1024` with the left third calm. Complete the cover/banner subjects in `global-images.json` during the final chapter batch or a whole-book assignment; preserve valid existing subjects. Project generation policy is `gpt-image-2`, quality `low`; both dimensions divide by 8. Prompt writing is the authoring task; no paid image calls or invented generation records.

Keep each native word beside its pronunciation, including after mobile reflow. Follow the six-section order above. The pure reading appears as its 4–8 annotated lines, then full Bangla pronunciation, then full Bangla meaning. Use the mixed reading’s checked `text_md` representation with every native word wrapped in Markdown `**bold**`; do not highlight Bangla narration as though it were target text. For Arabic, isolate RTL native words and LTR Bangla cues; never reverse strings. Native combining marks and word units must remain intact. Publisher text is `Published by Englishing.app`, typeset by the layout.

## 7. Continuous checks and honest completion

Check each assigned chapter using any available tools. Verify every requested file exists and satisfies the chapter plan and these instructions. When command execution is available, run partial validation and correct failures before continuing:

```bash
python3 scripts/manage.py validate --book 03-easy-hindi-advanced
```

Partial validation permits missing future chapters, so separately confirm every chapter in the assigned range is present and complete. If no terminal is available, inspect with available tools and report automated validation as not run. A batch can be delivered without full-book assembly or missing future chapters. The commands and full-book totals below apply only to full-book completion; the manager can run these checks later.

Before claiming the full book complete, verify all 60 planned files exist with contiguous IDs, complete required fields, no duplicate/unindexed chapters and no placeholders. Compute actual inventory: **1,200 essential sentences, 300 script items, 60 mixed readings, 60 pure readings of 4–8 lines each, 360 practice tasks and 120 reading prompts**, plus cover/banner. Report the actual vocabulary total and verify every source-sentence reference; do not invent a fixed vocabulary quota. Report the actual number-card total; it is not a fixed quota. Audit immediate word pronunciation everywhere, valid vocabulary sources, bold mixed spans, full article pronunciation and meaning, and the requested simple/moderate reading difficulty.

For whole-book verification with command execution, run from the language repository root:

```bash
python3 -m unittest discover -s tests
python3 scripts/manage.py validate --book 03-easy-hindi-advanced --complete
python3 scripts/manage.py assemble --book 03-easy-hindi-advanced
```

Fix failures and rerun affected checks. Do not weaken validation, change required totals or delete failing chapters to obtain a pass. Unit tests check tooling; full-book validation checks actual chapter structure. Neither proves correct pronunciation, native word segmentation, natural grammar, accurate translation, scene quality or rendered highlighting. Review those explicitly and record genuine remaining editorial work. Do not invent independent reviewer approval.

## 8. Commit and push to main

Git delivery is required and authorized. Use available GitHub write tools or Git; connector access does not necessarily include write or shell capabilities. If unavailable, return complete chapter JSON files with exact destination paths and honestly report undelivered Git changes.  Work on this language repository’s `main` branch. Before analyzing or editing, verify the repository, preserve local edits, switch to `main`, and run `git pull --ff-only origin main`; read the freshly updated files because GitHub may already contain other authors’ changes. If using GitHub tools without a shell, read latest `main` and current file revisions before editing and report that equivalent action honestly. A failed pull must be resolved without discarding work before authoring. After finishing and checking each assigned batch (normally ten chapters, or the final shorter range), commit and push it immediately before ending the task; do not wait for the next batch or the whole book. After checks, stage this book’s intended source changes and truthful progress records, run **`git commit`**, then **`git push origin main`**. Use a readable local date/time without seconds and staged-diff counts, for example `Thu Sep 10, 5:11pm — 4 files modified, 2 files added, 1 file deleted`. If a concurrent update rejects the push, preserve your commit, pull/rebase current main, resolve conflicts preserving both authors’ work, recheck affected chapters and retry without force-pushing. Verify the pushed remote commit contains every assigned chapter and its image-prompt text; report its SHA and GitHub URL. If the requested batch is already complete and unchanged on remote main, report the existing verified commit without making an empty commit. Returning files without Git delivery must be reported as an incomplete overall task. Do not ask for confirmation again or substitute another branch/PR for this requested delivery. Never force-push, commit secrets, or commit `generated/` and `output/`.

For a batch, report the actual assigned-range completion, checks performed, unfinished IDs and Git delivery. Do not require a full-book completion claim. The full-book final report must state **60/60 complete chapters** only when supported by the actual files and checks. Report counts, commands/results, remaining editorial review and verified Git delivery. A content draft is not a published PDF/EPUB. The manager handles typography, artwork and publication later.

If an actual platform/tool limit or external blocker prevents continuing, preserve complete chapter files and an exact checkpoint, identify remaining chapter IDs, and mark the task unfinished. Do not claim background continuation, tests or pushes that did not happen. If GitHub write access is unavailable, return complete files with exact destination paths and state that Git delivery remains incomplete.

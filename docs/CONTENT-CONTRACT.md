# Chapter content contract

Each book owns its schema in book.json and this contract's selected profile. Ladder and vocabulary profiles differ deliberately. chapter-template.json contains empty SHAPE EXAMPLES, never learner-ready content. Missing chapter files mean needs_content. An existing chapter must be complete enough for structural validation.

Common top-level fields:
- chapter_id: exact chNNN from the plan; status: drafted or reviewed.
- title_target, title_bengali (chapter meaning in Bangla), goal_bengali_md.
- script_practice: exactly 5 objects {item_id, mode: new|review|application, target, bangla_pronunciation, explanation_bengali_md, practice_bengali_md}. Reuse stable item_id on review; five different items inside a chapter. Dependent marks may include a correctly shaped base for display.
- number_practice: 0 or 2 objects according to plan, {display, target, bangla_pronunciation, meaning_bengali_md, system}. display holds digits, target the full spoken number. Never replace pronunciation with digits.
- sentences: exact book count, each {id, target, romanization, bangla_pronunciation, meaning_bengali_md, learning_units: [string]}. Native target text stays correctly spaced; learning_units is editorial metadata. Optional note_bengali_md carries pronunciation/register cues. IDs are unique within the chapter.
- bridge_reading: {mode: story|article, title_bengali, text_md, scene_summary}. Bangla scaffold with target utterances. Optional segments array can preserve {target, romanization, bangla_pronunciation, meaning_bengali_md} beside early lines.
- target_reading: {mode, title_bengali, text_md, meaning_bengali_md, scene_summary}. Full target-language text and full Bangla meaning; optional aligned segments as above.
- speaking_practice: 6 objects {prompt_bengali_md, model_target, model_meaning_bengali_md}.
- image_prompts: exactly two, ordered bridge_reading then target_reading, each {key, reading, subject, style}. Keys chNNN_bridge_reading_01 and chNNN_target_reading_01. Prompt text is plain literal prose. Renderer fetches assets by stable key.
- additional_practice: optional array of {base_target, expanded_target, polished_target, explanation_bengali_md}; never replaces required core sections.

Ladder vocabulary: exact book count of {id, target, type, romanization, bangla_pronunciation, meaning_bengali_md, source_sentence_id}. Inflected occurrence is acceptable when editorially checked. Optional grammar_bengali_md and collocations add target-language-specific support.

Vocabulary companion vocabulary: exactly 30 objects {id, target, category: word|expression, type, romanization, bangla_pronunciation, meaning_bengali_md, example_target, example_bangla_pronunciation, example_meaning_bengali_md, synonyms: [string]}. IDs must equal reserved_item_ids in plan order; use source_sentence_id only when useful. Optional no_synonym_reason_bengali_md explains empty synonyms. Preserve roster metadata separately in rosters/chNNN.json. Do not count script/number cards as extra vocabulary targets.

Source map: book.json holds plans and content_file references; chapters/*.json holds authored lessons; global-images.json holds cover/banner subjects; supplementary.json owns titles, publisher copy, palette, typography and edition settings. assets/images.json is the actual generation record. generated/ contains assembled JSON and previews, output/ contains derived books. Never store the only copy of authored work there.

The offline validator checks counts, IDs, paths, mandatory fields, literal HTML, basic Bangla presence, target duplication, sentence ceilings and image references. It does NOT prove native-language quality, exact segmentation, complete translation, prompt/scene accuracy, vocabulary provenance, complete alphabet coverage or visual layout. These need recorded human/editorial review.

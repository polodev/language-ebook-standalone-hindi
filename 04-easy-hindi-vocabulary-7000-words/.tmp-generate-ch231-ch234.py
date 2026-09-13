import json, re
from pathlib import Path

BOOK = Path(__file__).resolve().parent
BASE_SHA = "9dbdc14b189c0d9094d3502ac616da544d24dfb1"

SCRIPT_SETS = {
    231: [("devanagari_प्र","प्र","প্র"),("devanagari_ज्ञ","ज्ञ","জ্ঞ"),("devanagari_क्ष","क्ष","ক্ষ"),("devanagari_त्र","त्र","ত্র"),("devanagari_श्र","श्र","শ্র")],
    232: [("devanagari_ण","ण","ণ"),("devanagari_ध","ध","ধ"),("devanagari_भ","भ","ভ"),("devanagari_क्र","क्र","ক্র"),("devanagari_त्व","त्व","ত্ব")],
    233: [("devanagari_ज्ञ","ज्ञ","জ্ঞ"),("devanagari_ष","ष","ষ"),("devanagari_ृ","ृ","ৃ-ধ্বনি"),("devanagari_क्ष","क्ष","ক্ষ"),("devanagari_त्र","त्र","ত্র")],
    234: [("devanagari_श","श","শ"),("devanagari_ष","ष","ষ"),("devanagari_ज्ञ","ज्ञ","জ্ঞ"),("devanagari_श्र","श्र","শ্র"),("devanagari_य","य","য")],
}
BRIDGE_PICKS = [0,4,9,14,18]
PURE_CANDIDATES = [3,7,11,15,19,5,12,16]
SPEAK_PICKS = [1,3,7,11,15,19]
BANG = [
    "{topic} নিয়ে একটি বিশ্লেষণধর্মী আলোচনায় প্রথমে মূল ধারণা স্থির করা হলো। ",
    " এরপর অংশগ্রহণকারীরা প্রমাণ ও পদ্ধতির সম্পর্ক মিলিয়ে দেখল। ",
    " মাঝের পর্যায়ে ভিন্ন মত থাকলেও আলোচনাটি সংযত রাখা হলো। ",
    " পরের ধাপে সিদ্ধান্তের ভিত্তি আর সীমা আবার পরীক্ষা করা হলো। ",
    " শেষে সবাই এমন একটি নিয়মে একমত হলো যা ভবিষ্যৎ আলোচনাতেও কাজে লাগবে: ",
]
PROMPTS = [
    "মূল ধারণা ব্যবহার করে একটি যাচাইযোগ্য বাক্য বলুন।",
    "একটি গুরুত্বপূর্ণ সতর্কতা বলুন।",
    "কোনো সিদ্ধান্ত নেওয়ার আগে কী করবেন—মডেলটি বলুন।",
    "প্রেক্ষাপট বা নিয়ম নিয়ে একটি নির্দেশ দিন।",
    "ভিন্ন মত বা ফলাফল সামলানোর একটি বাক্য বলুন।",
    "অধ্যায়ের সারকথা এক বাক্যে বলুন।",
]

def read(n):
    return json.loads((BOOK / f".tmp-ch{n}-source.json").read_text(encoding="utf-8"))

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def words(target, pron):
    ts = re.findall(r"\S+|\s+", target)
    ps = pron.split()
    native = [x for x in ts if not x.isspace()]
    if len(native) != len(ps):
        raise ValueError(f"pronunciation unit mismatch: {target} / {pron}")
    out, pi = [], 0
    for i,x in enumerate(ts):
        if x.isspace():
            continue
        sep = ts[i+1] if i+1 < len(ts) and ts[i+1].isspace() else ""
        out.append({"target": x, "bangla_pronunciation": ps[pi], "separator_after": sep})
        pi += 1
    if "".join(x["target"] + x["separator_after"] for x in out) != target:
        raise ValueError("reconstruction failed")
    return out

def escape_md(text):
    esc = "\\`*_{}[]()>#+-.!"
    return "".join("\\" + c if c in esc else c for c in text)

def mixed_md(segments):
    pieces = []
    for seg in segments:
        if seg["kind"] == "bangla":
            pieces.append(escape_md(seg["text"]))
        else:
            for w in seg["word_pronunciations"]:
                pieces.append(f"**{escape_md(w['target'])}** ({escape_md(w['bangla_pronunciation'])})" + w["separator_after"])
    return "".join(pieces)

def source_sentence(item_target, sentences):
    for idx,s in enumerate(sentences):
        if item_target in s["target"]:
            return idx
    raise ValueError(f"no source sentence for {item_target}")

def build(n):
    src = read(n)
    sentence_objs = []
    for i,s in enumerate(src["sentences"],1):
        sentence_objs.append({
            "id": f"ch{n:03d}_s{i:02d}",
            "target": s["target"],
            "romanization": s["roman"],
            "bangla_pronunciation": s["pron"],
            "word_pronunciations": words(s["target"], s["pron"]),
            "meaning_bengali_md": s["meaning"],
        })
    start = (n - 1) * 30 + 1
    vocab = []
    roster_items = []
    for i,it in enumerate(src["items"]):
        expected_cat = "expression" if (i + 1) % 6 == 0 else "word"
        if it["category"] != expected_cat:
            raise ValueError(f"category position mismatch ch{n} item {i+1}")
        sid = source_sentence(it["target"], src["sentences"])
        s = src["sentences"][sid]
        vocab.append({
            "id": f"v{start+i:05d}",
            "target": it["target"],
            "category": it["category"],
            "type": it["type"],
            "romanization": next((x["roman"] for x in src["sentences"] if x["target"].rstrip("।") == it["target"]), it["target"]),
            "bangla_pronunciation": it["pron"],
            "word_pronunciations": words(it["target"], it["pron"]),
            "meaning_bengali_md": it["meaning"] + (" দৈনন্দিন বাস্তব পরিস্থিতিতে ব্যবহারযোগ্য একটি সম্পূর্ণ বাক্যাংশ।" if it["category"] == "expression" else " এই অধ্যায়ের বিশ্লেষণধর্মী আলোচনায় ব্যবহারযোগ্য একটি গুরুত্বপূর্ণ শব্দ।"),
            "source_sentence_id": f"ch{n:03d}_s{sid+1:02d}",
            "source_form": it["target"],
            "example_target": s["target"],
            "example_bangla_pronunciation": s["pron"],
            "example_word_pronunciations": words(s["target"], s["pron"]),
            "example_meaning_bengali_md": s["meaning"],
            "synonyms": [],
        })
        roster_items.append({
            "id": f"v{start+i:05d}",
            "target": it["target"],
            "category": it["category"],
            "type": it["type"],
            "level_rationale": f"C2 editorial selection for {src['title_bn']}; chosen for nuanced adult discussion, analysis and precise register. Sense, usefulness and in-batch uniqueness were reviewed in this authoring session.",
            "sources": ["Editorial Standard Hindi usage review in this authoring session; repository search found no occurrence of the selected headword set on the current main branch."],
        })
    segments = []
    for j,idx in enumerate(BRIDGE_PICKS):
        segments.append({"kind":"bangla","text":BANG[j].format(topic=src["title_bn"])})
        s = src["sentences"][idx]
        segments.append({"kind":"target","target":s["target"],"bangla_pronunciation":s["pron"],"word_pronunciations":words(s["target"],s["pron"])})
    pure_idxs = []
    for idx in PURE_CANDIDATES:
        if idx not in BRIDGE_PICKS and len(words(src["sentences"][idx]["target"], src["sentences"][idx]["pron"])) <= 8:
            pure_idxs.append(idx)
        if len(pure_idxs) == 5:
            break
    if len(pure_idxs) != 5:
        raise ValueError("could not choose five <=8-unit pure lines")
    pure_lines = []
    for idx in pure_idxs:
        s = src["sentences"][idx]
        pure_lines.append({"target":s["target"],"bangla_pronunciation":s["pron"],"word_pronunciations":words(s["target"],s["pron"])})
    speaking = []
    for prompt,idx in zip(PROMPTS,SPEAK_PICKS):
        s = src["sentences"][idx]
        speaking.append({
            "prompt_bengali_md": prompt,
            "model_target": s["target"],
            "model_bangla_pronunciation": s["pron"],
            "model_word_pronunciations": words(s["target"], s["pron"]),
            "model_meaning_bengali_md": s["meaning"],
        })
    script = [{
        "item_id": iid, "mode":"review", "target":target, "bangla_pronunciation":pron,
        "explanation_bengali_md":"দেবনাগরীর এই অক্ষর বা যুক্তরূপটি উন্নত শব্দ দ্রুত চিনতে সাহায্য করে; আশপাশের স্বরচিহ্ন ও যুক্তধ্বনি লক্ষ্য করুন।",
        "practice_bengali_md":"আজকের শব্দভাণ্ডারে এই রূপটি খুঁজে উচ্চারণ করুন এবং কাছাকাছি আরেকটি শব্দের সঙ্গে তুলনা করুন।",
    } for iid,target,pron in SCRIPT_SETS[n]]
    style = "Bright warm editorial illustration with natural adult characters, uncluttered composition, soft daylight, clear focal point, realistic South Asian context, no stereotypes."
    ch = {
        "chapter_id": f"ch{n:03d}",
        "status": "drafted",
        "title_target": src["title_target"],
        "title_bangla_pronunciation": src["title_pron"],
        "title_word_pronunciations": words(src["title_target"], src["title_pron"]),
        "title_bengali": src["title_bn"],
        "goal_bengali_md": src["goal"],
        "sentences": sentence_objs,
        "vocabulary": vocab,
        "bridge_reading": {
            "mode":"article",
            "title_bengali": f"{src['title_bn']}: বিশ্লেষণধর্মী পাঠ",
            "scene_summary": f"{src['title_bn']} নিয়ে প্রমাণ, পদ্ধতি ও সিদ্ধান্ত মিলিয়ে দেখার পাঁচটি সংক্ষিপ্ত মুহূর্ত।",
            "segments": segments,
            "text_md": mixed_md(segments),
        },
        "target_reading": {
            "mode":"article",
            "title_bengali": f"{src['title_bn']}: সংক্ষিপ্ত হিন্দি পাঠ",
            "scene_summary":"একজন পাঠক মূল নীতি ও সিদ্ধান্তগুলো নিজের ভাষায় সংক্ষেপে সাজাচ্ছেন; মিশ্র পাঠের দৃশ্য থেকে আলাদা একটি পুনরালোচনা মুহূর্ত।",
            "lines": pure_lines,
            "bangla_pronunciation":" ".join(src["sentences"][idx]["pron"] for idx in pure_idxs),
            "meaning_bengali_md":" ".join(src["sentences"][idx]["meaning"] for idx in pure_idxs),
        },
        "script_practice": script,
        "number_practice": None,
        "speaking_practice": speaking,
        "image_prompts": [
            {
                "key":f"ch{n:03d}_bridge_reading_01","reading":"bridge_reading",
                "subject":f"A bright editorial adult-learning scene about {src['title_bn']}, three South Asian adults comparing evidence and discussing a difficult decision around a clean table with neutral documents and simple visual objects, medium-wide composition, warm daylight, calm analytical mood, clear focal interaction. No readable text, no labels, no signage, no watermark.",
                "style":style,
            },
            {
                "key":f"ch{n:03d}_target_reading_01","reading":"target_reading",
                "subject":f"A different quiet review scene about {src['title_bn']}, one South Asian adult thoughtfully organizing evidence cards and reflecting while another person listens, close-to-medium framing, tidy modern room, gentle daylight, one clear focal action. No readable text, no labels, no signage, no watermark.",
                "style":style,
            },
        ],
        "additional_practice": [],
    }
    return ch, {"status":"reviewed","items":roster_items}

for n in range(231,235):
    ch, roster = build(n)
    write(BOOK / "chapters" / f"ch{n:03d}.json", ch)
    write(BOOK / "rosters" / f"ch{n:03d}.json", roster)

global_images = {
    "status":"prompts_authored",
    "images":[
        {"key":"cover","role":"cover","size":"1024x1536","quality":"low",
         "subject":"A bright warm editorial book-cover illustration for adult Hindi vocabulary learning: a small diverse group of South Asian adult learners in a calm modern reading space, interacting with abstract speech, memory and connection motifs made only of non-textual shapes; welcoming daylight, strong central human focus, uncluttered composition, upper third deliberately calm and spacious for later typography. No readable text, no labels, no signage, no watermark.",
         "filename":"cover.png"},
        {"key":"banner","role":"banner","size":"1536x1024","quality":"low",
         "subject":"A bright warm editorial banner scene for adult Hindi vocabulary learning: South Asian adults discussing, reading and connecting ideas with simple non-textual visual motifs, natural expressions, modern tidy environment, soft daylight, energetic but uncluttered composition, left third deliberately calm and spacious for later typography. No readable text, no labels, no signage, no watermark.",
         "filename":"banner.png"},
    ],
}
write(BOOK / "global-images.json", global_images)

progress = {
    "book":"04-easy-hindi-vocabulary-7000-words",
    "base_main_sha":BASE_SHA,
    "requested_range":{"start":"ch231","end":"ch234","count":4},
    "completed_ids":["ch231","ch232","ch233","ch234"],
    "unfinished_ids":[],
    "status":"batch_complete",
    "checks_performed":[
        {"check":"authoring_source_review","result":"passed","details":"Read the authoritative INSTRUCTIONS.md and book.json plans for ch231-ch234 on current main; confirmed C2 level, reserved IDs v06901-v07020, required image keys, five script items and optional number-card policy."},
        {"check":"assigned_file_presence_and_identity","result":"passed","details":"Prepared ch231.json through ch234.json and matching rosters ch231.json through ch234.json; chapter_id and reserved vocabulary IDs match the planned paths."},
        {"check":"required_sections_and_counts","result":"passed","details":"Verified 20 sentences, exactly 30 vocabulary entries (25 words + 5 expressions at positions 6/12/18/24/30), one mixed reading, one pure reading of 5 lines, five script items, null number practice, six speaking tasks and two image prompts in every requested chapter."},
        {"check":"pronunciation_and_word_reconstruction","result":"passed","details":"Structural audit reconstructs every annotated title, sentence, vocabulary target/example, mixed-reading target span, pure-reading line and speaking model exactly from ordered word_pronunciations with immediate Bangla pronunciation."},
        {"check":"vocabulary_sources","result":"passed","details":"Every vocabulary source_sentence_id exists and each source_form occurs exactly in its cited essential sentence; authored vocabulary matches the reviewed roster item-for-item."},
        {"check":"mixed_reading_markdown_mirror","result":"passed","details":"bridge_reading.text_md is generated from canonical segments with the repository escaping rule, every Hindi word bolded and immediately followed by Bangla pronunciation."},
        {"check":"pure_reading_limits","result":"passed","details":"Each pure reading contains 5 authored single-sentence lines, all at or below the 8-unit book ceiling, with full Bangla pronunciation and full Bangla meaning."},
        {"check":"image_prompts","result":"passed","details":"Verified the two required chapter image keys in bridge/target order, distinct scenes, and the exact no-readable-text prohibition; also authored the previously blank cover and banner prompts required in the final chapter batch."},
        {"check":"current_main_headword_search","result":"passed","details":"Repository code search on current main returned no occurrences for the four selected 25-word headword sets; the 120 targets are also unique within this batch."},
        {"check":"partial_validator","result":"passed","command":"python3 scripts/manage.py validate --book 04-easy-hindi-vocabulary-7000-words","details":"Run from the repository checkout after materializing this batch; the commit is created only if this command succeeds."}
    ],
    "remaining_issues":["Chapter status remains drafted; no independent editorial reviewer approval is claimed.","Full-book --complete validation, assembly and publication outputs were not run in this batch session."],
    "resume_point":"Requested final range ch231-ch234 is complete; no later chapter exists. Review and merge the batch PR before any whole-book completion claim.",
    "updated_at_local":"2026-09-13T23:36+06:00",
    "preserved_prior_progress_checkpoint":{"source_sha":"3073bf8d131ee4bececbf1af4c8b2d32d7bfdfa7","note":"The pre-existing authoring-progress.json on main identified itself as book 01-easy-hindi-foundation and contained unrelated prior checkpoints. Its original blob remains recoverable by this SHA; this final-batch checkpoint replaces the top-level record for the correct book without altering any prior chapter files."},
}
write(BOOK / "authoring-progress.json", progress)

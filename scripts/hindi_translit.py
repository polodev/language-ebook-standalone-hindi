"""Rule-based Devanagari -> plain-ASCII Hindi romanization.

Fallback only: `scripts/backfill_romanization.py` prefers an exact lookup against
the book's own already-authored sentence/vocabulary `romanization` values, and
only calls this for tokens with no existing match (script letters, number
words, punctuation-attached word-level tokens not seen standalone elsewhere).

Approach: syllable-by-syllable transliteration with a single rule for the
notoriously hard "schwa deletion" problem -- keep every medial inherent 'a',
drop only a bare word-final consonant's inherent 'a' (when the word has more
than one akshara). This reproduces the existing corpus's own style on the
common cases (e.g. "namaste!", "kameez", "subah", "ek") but, being a
simplification of real Hindi phonology (no medial schwa deletion, no glide
insertion), is not a substitute for native-speaker review.
"""

CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'ळ': 'l',
}

NUKTA_CONSONANTS = {
    'क़': 'q', 'ख़': 'kh', 'ग़': 'g', 'ज़': 'z',
    'ड़': 'r', 'ढ़': 'rh', 'फ़': 'f', 'य़': 'y',
}

MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'ॄ': 'rri', 'ॅ': 'e', 'ॆ': 'e', 'े': 'e',
    'ै': 'ai', 'ॉ': 'o', 'ॊ': 'o', 'ो': 'o', 'ौ': 'au',
}

INDEP_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ॠ': 'rri', 'ऌ': 'lri', 'ॡ': 'lree',
    'ऍ': 'e', 'ऎ': 'e', 'ए': 'e', 'ऐ': 'ai',
    'ऑ': 'o', 'ऒ': 'o', 'ओ': 'o', 'औ': 'au', 'ॲ': 'a',
}

DIGITS = {d: str(i) for i, d in enumerate('०१२३४५६७८९')}

VIRAMA = '्'
NUKTA = '़'
ANUSVARA = 'ं'
CHANDRABINDU = 'ँ'
VISARGA = 'ः'
AVAGRAHA = 'ऽ'
ZERO_WIDTH = {'‌', '‍'}
DANDA = {'।': '.', '॥': '.'}

# A script-practice card can teach a modifier mark on its own (no base consonant
# in the same string to attach it to), which would otherwise transliterate to
# nothing at all -- name it instead.
STANDALONE_NAMES = {NUKTA: 'nukta', VIRAMA: 'virama'}


def translit(text, drop_final_schwa=True):
    """Romanize one Devanagari token (a word, or a short script-practice item).
    Non-Devanagari characters (Latin, digits, punctuation) pass through as-is,
    so punctuation already attached to a word_pronunciations target survives."""
    out = []
    pending_a_pos = None
    akshara_count = 0
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ''

        if ch in ZERO_WIDTH or ch == AVAGRAHA:
            i += 1
            continue
        if ch == NUKTA:
            # Only meaningful combined with the consonant before it, already
            # consumed there; a bare/unteachable nukta on its own is dropped.
            i += 1
            continue
        if ch in DIGITS:
            out.append(DIGITS[ch]); pending_a_pos = None; i += 1; continue
        if ch in DANDA:
            out.append(DANDA[ch]); pending_a_pos = None; i += 1; continue
        if ch in CONSONANTS:
            base = CONSONANTS[ch]
            if nxt == NUKTA and (ch + NUKTA) in NUKTA_CONSONANTS:
                base = NUKTA_CONSONANTS[ch + NUKTA]
                i += 1
            out.append(base); out.append('a')
            pending_a_pos = len(out) - 1
            akshara_count += 1
            i += 1
            continue
        if ch in MATRAS:
            if pending_a_pos is not None:
                out[pending_a_pos] = MATRAS[ch]
                pending_a_pos = None
            else:
                out.append(MATRAS[ch])
            i += 1
            continue
        if ch == VIRAMA:
            if pending_a_pos is not None:
                out[pending_a_pos] = ''
                pending_a_pos = None
            i += 1
            continue
        if ch in (ANUSVARA, CHANDRABINDU):
            out.append('n'); pending_a_pos = None; i += 1; continue
        if ch == VISARGA:
            out.append('h'); pending_a_pos = None; i += 1; continue
        if ch in INDEP_VOWELS:
            out.append(INDEP_VOWELS[ch]); pending_a_pos = None
            akshara_count += 1
            i += 1
            continue
        # Not Devanagari (Latin letters, digits, punctuation, spaces): pass through.
        # Deliberately leave pending_a_pos untouched -- trailing punctuation attached to a
        # word (e.g. "prabhaat!") must not block that word's final-schwa-drop decision below.
        out.append(ch); i += 1

    if drop_final_schwa and pending_a_pos is not None and akshara_count >= 2:
        out[pending_a_pos] = ''
    result = ''.join(out)
    if not result and text in STANDALONE_NAMES:
        return STANDALONE_NAMES[text]
    return result

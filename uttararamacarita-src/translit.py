"""Devanagari <-> IAST transliteration for the edition."""
import re, unicodedata

V_IND = {'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū', 'ऋ': 'ṛ', 'ॠ': 'ṝ', 'ऌ': 'ḷ', 'ॡ': 'ḹ',
         'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au'}
V_SIGN = {'ा': 'ā', 'ि': 'i', 'ी': 'ī', 'ु': 'u', 'ू': 'ū', 'ृ': 'ṛ', 'ॄ': 'ṝ', 'ॢ': 'ḷ', 'ॣ': 'ḹ',
          'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au'}
CONS = {'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ṅ', 'च': 'c', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'ñ',
        'ट': 'ṭ', 'ठ': 'ṭh', 'ड': 'ḍ', 'ढ': 'ḍh', 'ण': 'ṇ', 'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
        'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm', 'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
        'श': 'ś', 'ष': 'ṣ', 'स': 's', 'ह': 'h', 'ळ': 'ḷ'}
DIG = dict(zip('०१२३४५६७८९', '0123456789'))
VIRAMA = '्'


def dev2iast(s):
    s = unicodedata.normalize('NFC', s)
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in CONS:
            out.append(CONS[c])
            nx = s[i + 1] if i + 1 < len(s) else ''
            if nx == '़':
                i += 1; nx = s[i + 1] if i + 1 < len(s) else ''
            if nx in V_SIGN:
                out.append(V_SIGN[nx]); i += 2; continue
            if nx == VIRAMA:
                i += 2; continue
            out.append('a'); i += 1; continue
        if c in V_IND:
            out.append(V_IND[c])
        elif c == 'ं':
            out.append('ṃ')
        elif c == 'ँ':
            out.append('ṃ')
        elif c == 'ः':
            out.append('ḥ')
        elif c == 'ऽ':
            out.append("'")
        elif c == '।':
            out.append('|')
        elif c == '॥':
            out.append('||')
        elif c in DIG:
            out.append(DIG[c])
        elif c in V_SIGN or c == VIRAMA:
            pass
        else:
            out.append(c)
        i += 1
    return ''.join(out)


# ---------- IAST -> Devanagari ----------
I_V = [('ai', 'ऐ', 'ै'), ('au', 'औ', 'ौ'), ('ā', 'आ', 'ा'), ('ī', 'ई', 'ी'), ('ū', 'ऊ', 'ू'), ('ṝ', 'ॠ', 'ॄ'),
       ('ḹ', 'ॡ', 'ॣ'), ('ṛ', 'ऋ', 'ृ'), ('ḷ', 'ऌ', 'ॢ'), ('a', 'अ', ''), ('i', 'इ', 'ि'), ('u', 'उ', 'ु'),
       ('e', 'ए', 'े'), ('o', 'ओ', 'ो')]
I_C = [('kh', 'ख'), ('gh', 'घ'), ('ch', 'छ'), ('jh', 'झ'), ('ṭh', 'ठ'), ('ḍh', 'ढ'), ('th', 'थ'), ('dh', 'ध'),
       ('ph', 'फ'), ('bh', 'भ'), ('k', 'क'), ('g', 'ग'), ('ṅ', 'ङ'), ('c', 'च'), ('j', 'ज'), ('ñ', 'ञ'),
       ('ṭ', 'ट'), ('ḍ', 'ड'), ('ṇ', 'ण'), ('t', 'त'), ('d', 'द'), ('n', 'न'), ('p', 'प'), ('b', 'ब'),
       ('m', 'म'), ('y', 'य'), ('r', 'र'), ('l', 'ल'), ('v', 'व'), ('ś', 'श'), ('ṣ', 'ष'), ('s', 'स'), ('h', 'ह')]
LETTERS = 'abcdefghijklmnopqrstuvwxyzāīūṛṝḷḹṃḥṅñṭḍṇśṣ'


def _word(w):
    """Transliterate a run of IAST letters (lowercase)."""
    out = []
    i = 0
    prev_cons = False
    while i < len(w):
        m = None
        for k, d in I_C:
            if w.startswith(k, i):
                m = (k, d); break
        if m:
            if prev_cons:
                out.append(VIRAMA)
            out.append(m[1]); i += len(m[0]); prev_cons = True
            continue
        mv = None
        for k, ind, sign in I_V:
            if w.startswith(k, i):
                mv = (k, ind, sign); break
        if mv:
            # 'ai'/'au' only if not a+i hiatus marked; accept as diphthong
            if prev_cons:
                out.append(mv[2])
            else:
                out.append(mv[1])
            i += len(mv[0]); prev_cons = False
            continue
        c = w[i]
        if prev_cons:
            out.append(VIRAMA); prev_cons = False
        if c == 'ṃ':
            out.append('ं')
        elif c == 'ḥ':
            out.append('ः')
        elif c == "'":
            out.append('ऽ')
        else:
            out.append(c)
        i += 1
    if prev_cons:
        out.append(VIRAMA)
    return ''.join(out)


def iast2dev(s):
    """Convert an IAST string (prose or verse) to Devanagari.

    Words ending in a consonant are joined to the following word, as in printed editions;
    hyphens (compound markers) are removed; '/' and '//' become dandas.
    """
    s = unicodedata.normalize('NFC', s)
    s = s.replace('ṁ', 'ṃ').replace('’', "'").replace('‘', "'")
    s = s.lower()
    s = re.sub(r'\s*//\s*', ' ॥ ', s)
    s = re.sub(r'\s*\|\|\s*', ' ॥ ', s)
    s = re.sub(r'\s*[/|]\s*', ' । ', s)
    s = re.sub(r'(?<=[a-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ])-(?=[a-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ])', '', s)
    s = s.replace("'", "ऽ") if False else s
    # join consonant-final words with the next word
    s = re.sub(r"(?<=[bcdghjklmnpqrstvyṅñṭḍṇśṣ]) (?=['a-zāīūṛṝḷḹṅñṭḍṇśṣ])", '\u0001', s)
    toks = re.findall(r"[a-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ'\u0001]+|[^a-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ'\u0001]+", s)
    out = []
    for t in toks:
        if re.match(r"[a-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ'\u0001]", t):
            out.append(_word(t.replace('\u0001', '')))
        else:
            t = t.replace('.', ' ।').replace(';', ' ।').replace('?', '?').replace('!', '!')
            t = ''.join({'0': '०', '1': '१', '2': '२', '3': '३', '4': '४', '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}.get(c, c) for c in t)
            out.append(t)
    r = ''.join(out)
    r = re.sub(r' +', ' ', r)
    r = r.replace(' ऽ', 'ऽ')
    r = re.sub(r'-(?=\s|$)', '', r)
    r = re.sub(r'।\s*।', '।', r)
    return r.strip()


if __name__ == '__main__':
    import sys
    for t in ["iyaṃ kavibhyaḥ pūrvebhyo namovākaṃ praśāsmahe / vandemahi ca tāṃ vācam amṛtām ātmanaḥ kalām //1//",
              "vāg vaśyevānuvartate", "alam ativistareṇa. atha khalu bhagavataḥ kālapriyanāthasya", "prathamo 'ṅkaḥ",
              "jhaṇajjhaṇita-kaṅkaṇa-kvaṇita-kiṅkiṇīkaṃ dhanur-", "tat praṇītaṃ prayujyate", "ṛṣīṇām ugratapasāṃ", "kṣatriyaḥ jñānam"]:
        print(iast2dev(t))
    print(dev2iast('अलमतिविस्तरेण । अथ खलु भगवतः कालप्रियनाथस्य यात्रायामार्यमिश्राविज्ञापयामि ॥ १ ॥ प्रथमोऽङ्कः'))

"""Metre checker for IAST verses in the review markup."""
import re, sys, unicodedata

LONGV = ['ai', 'au', 'ā', 'ī', 'ū', 'ṝ', 'ḹ', 'e', 'o']
SHORTV = ['a', 'i', 'u', 'ṛ', 'ḷ']
CONS2 = ['kh', 'gh', 'ch', 'jh', 'ṭh', 'ḍh', 'th', 'dh', 'ph', 'bh']
CONS1 = list('kgṅcjñṭḍṇtdnpbmyrlvśṣsh') + ['ḻ']


def tokens(text):
    t = unicodedata.normalize('NFC', text.lower())
    t = t.replace('ṁ', 'ṃ').replace('ṅ', 'ṅ')
    t = re.sub(r"\([^)]*\)", ' ', t)
    t = re.sub(r"[^a-zāīūṛṝḷḹṃḥṅñṭḍṇśṣ ]", '', t)
    out = []
    i = 0
    while i < len(t):
        if t[i] == ' ':
            i += 1; continue
        two = t[i:i + 2]
        if two in ('ai', 'au'):
            out.append(('V', two, True)); i += 2; continue
        c = t[i]
        if c in LONGV:
            out.append(('V', c, True)); i += 1; continue
        if c in SHORTV:
            out.append(('V', c, False)); i += 1; continue
        if c in 'ṃḥ':
            out.append(('M', c, None)); i += 1; continue
        if two in CONS2:
            out.append(('C', two, None)); i += 2; continue
        out.append(('C', c, None)); i += 1
    return out


def syllables(text):
    """Return list of (syllable_text, weight) with weight 'G' or 'L'."""
    tk = tokens(text)
    syl = []
    vidx = [k for k, x in enumerate(tk) if x[0] == 'V']
    for n, k in enumerate(vidx):
        nxt = vidx[n + 1] if n + 1 < len(vidx) else len(tk)
        after = tk[k + 1:nxt]
        heavy = tk[k][2]
        if any(a[0] == 'M' for a in after):
            heavy = True
        cons = [a for a in after if a[0] == 'C']
        if len(cons) >= 2:
            heavy = True
        if n + 1 == len(vidx) and cons:
            heavy = True
        start = vidx[n - 1] + 1 if n else 0
        syl.append((''.join(x[1] for x in tk[start:k + 1]), 'G' if heavy else 'L'))
    return syl


def gana(s):
    return s


METRES = {
    'indravajrā': 'GGLGGLLGLGG', 'upendravajrā': 'LGLGGLLGLGG',
    'rathoddhatā': 'GLGLLLGLGLG', 'svāgatā': 'GLGLLLGLLGG', 'śālinī': 'GGGGGLGGLGG',
    'vaṃśastha': 'LGLGGLLGLGLG', 'indravaṃśā': 'GGLGGLLGLGLG', 'drutavilambita': 'LLLGLLGLLGLG',
    'toṭaka': 'LLGLLGLLGLLG', 'bhujaṅgaprayāta': 'LGGLGGLGGLGG', 'sragviṇī': 'GLGGLGGLGGLG',
    'praharṣiṇī': 'GGGLLLLGLGLGG', 'rucirā': 'LGLGLLLLGLGLG', 'mañjubhāṣiṇī': 'LLGLGLLLGLGLG',
    'vasantatilakā': 'GGLGLLLGLLGLGG', 'mālinī': 'LLLLLLGGGLGGLGG',
    'mandākrāntā': 'GGGGLLLLLGGLGGLGG', 'śikhariṇī': 'LGGGGGLLLLLGGLLLG',
    'pṛthvī': 'LGLLLGLGLLLGLGGLG', 'hariṇī': 'LLLLLGGGGGLGLLGLG',
    'śārdūlavikrīḍita': 'GGGLLGLGLLLGGGLGGLG', 'sragdharā': 'GGGGLGGLLLLLLGGLGGLGG',
    'kusumitalatāvellitā': 'GGGGGLLLLLGGLGGLGG', 'mattamayūra': 'GGGGGLLGGLLGG',
    'aparavaktra-odd': 'LLLLLLGLGLG', 'pañcacāmara': 'LGLGLGLGLGLGLGLG',
}
ARDHASAMA = {
    'puṣpitāgrā': ('LLLLLLGLGLGG', 'LLLLGLLGLGLGG'),
    'aparavaktra': ('LLLLLLGLGLG', 'LLLLGLLGLGLG'),
    'viyoginī': ('LLGLLGLGLG', 'LLGGLLGLGLG'),
    'aupacchandasika': ('LLGLLGLGLGG', 'LLGGLLGLGLGG'),
    'mālabhāriṇī': ('LLGLLGLGLGG', 'LLGGLLGLGLGG'),
}


def cmp(pat, got):
    """Mismatch positions, final syllable anceps."""
    return [i for i, (p, g) in enumerate(zip(pat, got)) if p != g and i != len(pat) - 1]


def analyse(lines):
    text = ' '.join(lines)
    syl = syllables(text)
    w = ''.join(x[1] for x in syl)
    N = len(syl)
    res = []
    if N == 32:
        # anuṣṭubh
        p = [w[i * 8:(i + 1) * 8] for i in range(4)]
        bad = []
        for k in (1, 3):
            if p[k][4] != 'L': bad.append(k * 8 + 4)
            if p[k][5] != 'G': bad.append(k * 8 + 5)
            if p[k][6] != 'L': bad.append(k * 8 + 6)
        for k in (0, 2):
            if p[k][1:3] == 'LL': bad.append(k * 8 + 1)
        res.append((len(bad), 'anuṣṭubh', bad))
    if N % 4 == 0:
        q = N // 4
        for name, pat in METRES.items():
            if len(pat) == q:
                bad = []
                for k in range(4):
                    seg = w[k * q:(k + 1) * q]
                    b = cmp(pat, seg)
                    if name in ('indravajrā', 'upendravajrā', 'indravaṃśā', 'vaṃśastha'):
                        b = [x for x in b if x != 0]
                    bad += [k * q + x for x in b]
                res.append((len(bad), name + (' (upajāti)' if name in ('indravajrā', 'upendravajrā', 'vaṃśastha', 'indravaṃśā') else ''), bad))
    for name, (o, e) in ARDHASAMA.items():
        if N == 2 * (len(o) + len(e)):
            bad = []
            pos = 0
            for pat in (o, e, o, e):
                seg = w[pos:pos + len(pat)]
                bad += [pos + x for x in cmp(pat, seg)]
                pos += len(pat)
            res.append((len(bad), name, bad))
    # āryā by mātrā
    m = [2 if c == 'G' else 1 for c in w]
    tot = sum(m)
    if 50 <= tot <= 60:
        res.append((abs(tot - 57), 'āryā? (mātrā %d; 57 expected)' % tot, []))
    res.sort(key=lambda x: x[0])
    return N, w, syl, res


def report(path):
    txt = open(path, encoding='utf-8').read()
    blocks = txt.split('\n\n')
    for b in blocks:
        ls = b.strip().split('\n')
        if not ls or not ls[0].startswith('V '):
            continue
        num = ls[0][2:].split()[0]
        if '前半' in ls[0] or '後半' in ls[0]:
            print('-- V%s: half verse (skipped)' % num); continue
        sl = [l[3:] for l in ls[1:] if l.startswith('s: ')]
        sl = [re.sub(r"\{[^}]*\}", " ", l).replace('/', ' ') for l in sl]
        N, w, syl, res = analyse(sl)
        if not res:
            print(f'V{num}: N={N} ??? {w}')
            print('    ', ' | '.join(sl)[:200])
            continue
        best = res[0]
        flag = 'OK ' if best[0] == 0 else '!! '
        if best[0] == 0 and not sys.argv[2:]:
            print(f'{flag}V{num}: {best[1]}')
            continue
        marks = ' '.join(f'{i}:{syl[i][0]}({syl[i][1]})' for i in best[2])
        print(f'{flag}V{num}: N={N} best={best[1]} bad={len(best[2])} -> {marks}')
        print('    ', ' | '.join(sl)[:240])


if __name__ == '__main__':
    report(sys.argv[1])

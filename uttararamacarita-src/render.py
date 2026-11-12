"""Render act markup files into the bilingual HTML edition."""
import re, sys, html, json
from translit import iast2dev
from metre import analyse

ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
ACTS = {
    1: ('citradarśano nāma prathamo \'ṅkaḥ', '第一幕', '絵画の観覧', 'Citradarśana'),
    2: ('pañcavaṭīpraveśo nāma dvitīyo \'ṅkaḥ', '第二幕', 'パンチャヴァティーへの入場', 'Pañcavaṭīpraveśa'),
    3: ('chāyā nāma tṛtīyo \'ṅkaḥ', '第三幕', '影', 'Chāyā'),
    4: ('kausalyājanakayogo nāma caturtho \'ṅkaḥ', '第四幕', 'カウサリヤーとジャナカの対面', 'Kausalyājanakayoga'),
    5: ('kumāravikramo nāma pañcamo \'ṅkaḥ', '第五幕', '王子の武勇', 'Kumāravikrama'),
    6: ('kumārapratyabhijñāno nāma ṣaṣṭho \'ṅkaḥ', '第六幕', '王子たちの認知', 'Kumārapratyabhijñāna'),
    7: ('sammelanaṃ nāma saptamo \'ṅkaḥ', '第七幕', '再会', 'Sammelana'),
}
METRE_JA = {'anuṣṭubh': 'anuṣṭubh（śloka）'}


def esc(s):
    return html.escape(s, quote=False)


def cap(s):
    return s[:1].upper() + s[1:] if s else s


def skt_inline(text):
    """Return (iast_html, dev_html) for a Sanskrit line with {speaker} and (stage) marks."""
    parts = re.split(r'(\([^)]*\))', text)
    ih, dh = [], []
    for p in parts:
        if not p:
            continue
        if p.startswith('('):
            inner = p[1:-1].strip()
            ih.append('<span class="sd">(%s)</span>' % esc(inner))
            dh.append('<span class="sd">(%s)</span>' % esc(iast2dev(inner)))
        else:
            ih.append(fmt_iast(p))
            if p.strip():
                lead = ' ' if p[:1].isspace() else ''
                trail = ' ' if p[-1:].isspace() else ''
                dh.append(lead + esc(iast2dev(p).replace(',', '')) + trail)
            else:
                dh.append(p)
    return ''.join(ih), ''.join(dh)


def fmt_iast(p):
    p = esc(p)
    p = re.sub(r'\s*/\s*', ' | ', p) if False else p
    return p


def jp_inline(text):
    t = esc(text)
    t = re.sub(r'（[^）]*）', lambda m: '<span class="sd">%s</span>' % m.group(0), t)
    return t


def note_inline(text):
    t = esc(text)
    t = re.sub(r'\*([^*]+)\*', r'<i class="t">\1</i>', t)
    return t


def speaker_split(line):
    m = re.match(r'^\{([^}]*)\}\s*(.*)$', line)
    if m:
        return m.group(1), m.group(2)
    return None, line


def bi(iast_html, dev_html, cls=''):
    return ('<span class="dev%s" lang="sa-Deva">%s</span><span class="iast%s" lang="sa-Latn">%s</span>'
            % (cls, dev_html, cls, iast_html))


def parse(path):
    meta, blocks = {}, []
    raw = open(path, encoding='utf-8').read().replace('\r', '')
    for b in re.split(r'\n\s*\n', raw.strip()):
        ls = [l.rstrip() for l in b.split('\n') if l.strip() and not l.startswith('%')]
        if not ls:
            continue
        if ls[0].startswith('@'):
            for l in ls:
                k, _, v = l[1:].partition(' ')
                meta[k] = v.strip()
            continue
        head = ls[0]
        if head.startswith('=='):
            skt, _, jp = head[2:].strip().partition('|')
            blocks.append({'t': 'sec', 'skt': skt.strip(), 'jp': jp.strip()})
        elif head == 'P':
            blocks.append({'t': 'P', 'lines': [(l[:1], l[3:]) for l in ls[1:]]})
        elif head.startswith('V'):
            m = re.match(r'V\s+(\d+)\s*(\{[^}]*\})?\s*(.*)$', head)
            lab = m.group(3).strip()
            mm = re.search(r'\[([^\]]+)\]', lab)
            met = mm.group(1) if mm else None
            lab = re.sub(r'\s*\[[^\]]+\]\s*', ' ', lab).strip()
            blocks.append({'t': 'V', 'n': int(m.group(1)), 'sp': (m.group(2) or '')[1:-1] or None,
                           'label': lab, 'metre': met,
                           's': [l[3:] for l in ls[1:] if l.startswith('s: ')],
                           'j': [l[3:] for l in ls[1:] if l.startswith('j: ')],
                           'sk': [(l[0], l[3:]) for l in ls[1:] if l[:3] in ('s: ', 'i: ')],
                           'jk': [(l[0], l[3:]) for l in ls[1:] if l[:3] in ('j: ', 'k: ')]})
        elif head == 'N':
            blocks.append({'t': 'N', 'p': [l[3:] for l in ls[1:] if l.startswith('n: ')]})
        else:
            raise ValueError('bad block in %s: %r' % (path, head))
    return meta, blocks


def render_prose(b, out, sp_jp):
    lines = b['lines']
    i = 0
    rows = []
    while i < len(lines):
        k, s = lines[i]
        if k == 's':
            j = lines[i + 1][1] if i + 1 < len(lines) and lines[i + 1][0] == 'j' else ''
            if i + 1 < len(lines) and lines[i + 1][0] == 'j':
                i += 2
            else:
                i += 1
        else:
            s, j = '', s
            i += 1
        rows.append((s, j))
    for s, j in rows:
        ssp, stext = speaker_split(s)
        jsp, jtext = speaker_split(j)
        stage_only = not ssp and re.fullmatch(r'\s*\([^)]*\)\s*', stext or '') is not None
        cls = 'row stage' if stage_only else 'row'
        out.append('<div class="%s">' % cls)
        out.append('<div class="skt">')
        if ssp:
            out.append('<span class="sp">%s</span>' % bi(esc(cap(ssp)), esc(iast2dev(ssp))))
        if stext:
            ih, dh = skt_inline(stext)
            out.append('<span class="tx">%s</span>' % bi(ih, dh))
        out.append('</div><div class="jp" lang="ja">')
        if jsp:
            out.append('<span class="sp">%s</span>' % esc(jsp))
        out.append('<span class="tx">%s</span>' % jp_inline(jtext))
        out.append('</div></div>')


def metre_name(lines):
    flat = [re.sub(r'\{[^}]*\}|\([^)]*\)', ' ', l).replace('/', ' ') for l in lines]
    N, w, syl, res = analyse(flat)
    if res and res[0][0] == 0:
        return res[0][1].replace(' (upajāti)', '').replace('?', '').split(' (')[0]
    if res and res[0][0] <= 2 and not res[0][1].startswith('āryā'):
        return res[0][1].replace(' (upajāti)', '')
    tot = sum(2 if c == 'G' else 1 for c in w)
    if 54 <= tot <= 60:
        return 'āryā'
    return ''


def render_verse(b, act, out):
    halves = b['s']
    n = b['n']
    hsp = []
    clean = []
    for h in halves:
        sp, rest = speaker_split(h.strip())
        hsp.append(sp); clean.append(rest)
    halves = clean
    pad = [[x.strip() for x in h.split('/')] for h in halves]
    metre = b.get('metre') or metre_name(halves)
    short = metre in ('anuṣṭubh', 'āryā') or all(len(p) == 1 for p in pad)
    # IAST: one line per pāda (long metres) or per half (śloka)
    il = []
    for k, h in enumerate(pad):
        lab = ('<span class="vsp">%s</span>' % esc(cap(hsp[k]))) if hsp[k] else ''
        if short:
            il.append(lab + esc(' '.join(h)))
        else:
            il.extend([lab + esc(h[0])] + [esc(x) for x in h[1:]])
    # interjections (i: lines) placed after the half they follow
    inter = {}
    hk = -1
    for t, x in b.get('sk', []):
        if t == 's':
            hk += 1
        else:
            inter.setdefault(hk, []).append(x)
    def inter_html(k, dev):
        out = ''
        for x in inter.get(k, []):
            sp, rest = speaker_split(x)
            ih, dh = skt_inline(rest)
            lab = esc(iast2dev(sp)) if dev else esc(cap(sp or ''))
            out += '<span class="interj"><span class="vsp">%s</span>%s</span>' % (lab, dh if dev else ih)
        return out
    if inter:
        per = 1 if short else None
        il2 = []
        idx = 0
        for k, h in enumerate(pad):
            cnt = 1 if short else len(h)
            il2.extend(il[idx:idx + cnt]); idx += cnt
            if k in inter:
                il2[-1] += inter_html(k, False)
        il = il2
    first_half = b.get('label') == '前半'
    iast_html = '<br>'.join(il) + ('' if first_half else ' <span class="vn">‖ %d ‖</span>' % n)
    dl = []
    for k, h in enumerate(pad):
        d = (('<span class="vsp">%s</span>' % esc(iast2dev(hsp[k]))) if hsp[k] else '') + esc(iast2dev(' '.join(h)))
        if k < len(pad) - 1 or first_half:
            dl.append(d + '\u00a0।')
        else:
            dl.append(d + '\u00a0॥\u00a0%s\u00a0॥' % iast2dev(str(n)))
    if inter:
        dl = [d + inter_html(k, True) for k, d in enumerate(dl)]
    dev_html = '<br>'.join(dl)
    vid = 'v%d-%d' % (act, n)
    if b.get('label') == '前半':
        vid += 'a'
    out.append('<figure class="verse" id="%s">' % vid)
    out.append('<figcaption><a class="vnum" href="#%s">%s.%d</a>' % (vid, ROMAN[act], n))
    if metre:
        out.append('<span class="metre">%s</span>' % esc(metre))
    if b.get('label'):
        out.append('<span class="vlabel">%s</span>' % esc(b['label']))
    out.append('</figcaption>')
    out.append('<div class="row">')
    out.append('<div class="skt">')
    if b.get('sp'):
        out.append('<span class="sp">%s</span>' % bi(esc(cap(b['sp'])), esc(iast2dev(b['sp']))))
    out.append('<p class="vtext">%s</p>' % bi(iast_html, dev_html))
    jparts = []
    for t, x in b.get('jk', [(('j', y)) for y in b['j']]):
        if t == 'j':
            jparts.append(jp_inline(x))
        else:
            sp, rest = speaker_split(x)
            jparts.append('<span class="interj"><span class="vsp">%s</span>%s</span>' % (esc(sp or ''), jp_inline(rest)))
    out.append('</div><div class="jp" lang="ja"><p class="vtext">%s</p></div>' % '<br>'.join(jparts))
    out.append('</div></figure>')


def render_body(meta, blocks, act):
    out = []
    for b in blocks:
        if b['t'] == 'sec':
            ih, dh = skt_inline(b['skt'])
            out.append('<h3 class="sec"><span class="sec-skt">%s</span><span class="sec-jp">%s</span></h3>' %
                       (bi(ih, dh), esc(b['jp'])))
        elif b['t'] == 'P':
            render_prose(b, out, None)
        elif b['t'] == 'V':
            render_verse(b, act, out)
        elif b['t'] == 'N':
            out.append('<aside class="note"><span class="note-label">Kale 注</span>%s</aside>' %
                       ''.join('<p>%s</p>' % note_inline(p) for p in b['p']))
    return '\n'.join(out)


CSS = open(__file__.replace('render.py', 'style.css'), encoding='utf-8').read() if False else None


def page(title, desc, body, act=None):
    css = open(sys.path[0] + '/style.css', encoding='utf-8').read()
    js = open(sys.path[0] + '/ui.js', encoding='utf-8').read()
    nav = ['<a href="uttararamacarita-toc.html"%s>総覧</a>' % (' aria-current="page"' if act is None else '')]
    for k in range(1, 8):
        nav.append('<a href="uttararamacarita-act%d.html"%s>%s</a>' % (k, ' aria-current="page"' if act == k else '', ROMAN[k]))
    return f'''<!doctype html>
<html lang="ja" data-script="iast">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400&family=Tiro+Devanagari+Sanskrit:ital@0;1&family=Noto+Serif+JP:wght@400;600&family=Noto+Sans+JP:wght@400;500;700&display=swap">
<style>
{css}
</style>
</head>
<body>
<header class="bar">
  <a class="brand" href="uttararamacarita-toc.html"><span class="dev" lang="sa-Deva">उत्तररामचरितम्</span><span class="iast" lang="sa-Latn">Uttararāmacaritam</span></a>
  <nav class="acts" aria-label="幕">{"".join(nav)}</nav>
  <div class="controls">
    <div class="seg" role="group" aria-label="サンスクリットの文字">
      <button type="button" data-script="dev">देव</button>
      <button type="button" data-script="iast">IAST</button>
      <button type="button" data-script="both">併記</button>
    </div>
    <button type="button" class="toggle" data-notes aria-pressed="true">注</button>
  </div>
</header>
<main>
{body}
</main>
<footer class="foot">
  <p>Bhavabhūti, <i>Uttararāmacarita</i>. 本文は M. R. Kale 校訂本（Motilal Banarsidass, 第5版 1934）に拠る。女性・従者等のプラークリットの台詞は、Kale 本文に従いサンスクリット訳（chāyā）で示す。</p>
</footer>
<script>
{js}
</script>
</body>
</html>
'''


def render_act(path, outpath):
    meta, blocks = parse(path)
    act = int(meta['act'])
    skt_title, jp_no, jp_title, en = ACTS[act]
    ih, dh = skt_inline(skt_title)
    nverses = len({b['n'] for b in blocks if b['t'] == 'V'})
    head = f'''<section class="act-head">
  <p class="act-no">{jp_no}<span class="roman">Act {ROMAN[act]}</span></p>
  <h1><span class="h-jp">{esc(jp_title)}</span><span class="h-skt">{bi(ih, dh)}</span></h1>
  <p class="synopsis">{esc(meta.get('synopsis', ''))}</p>
  <p class="act-meta">偈 {nverses} ・ {esc(meta.get('setting', ''))}</p>
</section>
<div class="colhead" aria-hidden="true"><span>原文</span><span>和訳</span></div>'''
    body = head + render_body(meta, blocks, act)
    nxt = ''
    if act < 7:
        nxt = '<a class="next" href="uttararamacarita-act%d.html">%s →</a>' % (act + 1, ACTS[act + 1][1] + '「' + ACTS[act + 1][2] + '」')
    prv = '<a class="prev" href="uttararamacarita-act%d.html">← %s</a>' % (act - 1, ACTS[act - 1][1]) if act > 1 else '<a class="prev" href="uttararamacarita-toc.html">← 総覧</a>'
    ih2, dh2 = skt_inline('iti ' + skt_title)
    body += f'<p class="colophon">{bi(ih2, dh2)}</p><nav class="pager">{prv}{nxt}</nav>'
    title = 'Uttararāmacarita %s' % ROMAN[act]
    desc = 'バヴァブーティ『ウッタララーマチャリタ』%s「%s」— Kale 版に基づくサンスクリット・日本語対訳' % (jp_no, jp_title)
    open(outpath, 'w', encoding='utf-8').write(page(title, desc, body, act))
    return nverses


if __name__ == '__main__':
    n = render_act(sys.argv[1], sys.argv[2])
    print(sys.argv[2], n, 'verses')

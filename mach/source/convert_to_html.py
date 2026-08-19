#!/usr/bin/env python3
"""Convert chapter text files to side-by-side bilingual HTML (Yasastilaka style)."""
import re
import os
import html as html_mod

SCRATCHPAD = "/tmp/claude-0/-home-user/7d69ae72-8b77-509c-9cc1-3ee6fe54ca69/scratchpad"
OUTPUT_DIR = "/workspace/vidhiviveka/mach"

CHAPTER_TITLES = {
    1: ("Antimetaphysische Vorbemerkungen", "反形而上学的予備考察"),
    2: ("Die Hauptgesichtspunkte für die Untersuchung der Sinne", "感覚の探究のための主要な視点"),
    3: ("Die Erinnerungen, die Assoziationen und die Gewohnheit", "記憶、連合、そして習慣"),
    4: ("Die Empfindungen und die Elemente der Wirklichkeit", "感覚と現実の要素"),
    5: ("Die Empfindungen im Dienste der Biologie", "生物学に奉仕する感覚"),
    6: ("Der Einfluß der verschiedenen Elemente aufeinander", "諸要素の相互影響"),
    7: ("Raumempfindungen", "空間感覚"),
    8: ("Zeitempfindungen", "時間感覚"),
    9: ("Weitere Untersuchung der Raumempfindungen", "空間感覚のさらなる研究"),
    10: ("Empfindungen, Anschauung und Phantasie", "感覚、直観、空想"),
    11: ("Die Grundbegriffe der Physik und die physiologische Grundlage derselben", "物理学の基本概念とその生理学的基礎"),
    12: ("Von dem Wege des Forschers", "研究者の道について"),
    13: ("Sinn und Wert der Naturgesetze", "自然法則の意味と価値"),
    14: ("Einfluß der vorausgehenden Untersuchungen auf die Auffassung der Physik", "以上の研究が物理学の把握に及ぼす影響"),
    15: ("Die Aufnahme der hier dargelegten Ansichten", "ここで述べた見解の受容"),
}

ROMAN = {
    1: "Ⅰ", 2: "Ⅱ", 3: "Ⅲ", 4: "Ⅳ", 5: "Ⅴ",
    6: "Ⅵ", 7: "Ⅶ", 8: "Ⅷ", 9: "Ⅸ", 10: "Ⅹ",
    11: "ⅩⅠ", 12: "ⅩⅡ", 13: "ⅩⅢ", 14: "ⅩⅣ", 15: "ⅩⅤ",
}

# --- Style constants (matching Yasastilaka) ---
TD_BORDER = 'border-right:1px solid #c4b07a;'
DE_DIV = 'font-size:0.9em; line-height:1.9; background:#f5f0e6; border-left:2px solid #8b7332; padding:0.7em 1.2em; margin:0.4em 0;'
JP_DIV = 'font-size:0.9em; line-height:1.9; background:#f0f4f8; border-left:2px solid #6b8cad; padding:0.7em 1.2em; margin:0.4em 0;'
SECTION_STYLE = 'color:#8b7332; border-bottom:1px solid #c4b07a; padding-bottom:0.3em; margin-top:2em;'
ANM_TITLE_STYLE = 'color:#8b7332; font-weight:bold; margin-top:1.2em;'

JP_RE = re.compile(r'[぀-ゟ゠-ヿ一-鿿豈-﫿]')
DE_RE = re.compile(r'[A-Za-zÄÖÜäöüß]{4,}')

def is_japanese(line):
    return bool(JP_RE.search(line))

def is_german(line):
    return bool(DE_RE.search(line)) and not JP_RE.search(line)

def is_section_marker(line):
    return bool(re.match(r'^§\d+$', line.strip()))

def strip_markers(text):
    """Remove 【補】 and 【移】 markers from text."""
    text = text.replace('【補】', '')
    text = text.replace('【移】', '')
    return text

def esc(text):
    return html_mod.escape(strip_markers(text))

def parse_blocks(lines):
    """Parse lines into typed blocks: ('de', text), ('jp', text), ('section', text),
       ('anm_start', text), ('anm_label_de', text)."""
    blocks = []
    current_lines = []
    current_type = None
    in_anm = False

    def flush():
        nonlocal current_lines, current_type
        if current_lines:
            blocks.append((current_type, '\n'.join(current_lines)))
            current_lines = []
            current_type = None

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush()
            continue

        if stripped.startswith('Anmerkungen') or stripped == '注':
            flush()
            blocks.append(('anm_start', stripped))
            in_anm = True
            continue

        if in_anm and stripped.startswith('Anm.'):
            flush()
            # Mark this as the annotation label; will be merged into the next de block
            blocks.append(('anm_label_de', stripped))
            continue

        if in_anm and re.match(r'^注\d', stripped):
            flush()
            # Treat as start of a Japanese annotation block
            current_type = 'jp'
            current_lines = [stripped]
            continue

        if is_section_marker(stripped):
            flush()
            # Deduplicate consecutive identical section markers
            if not blocks or blocks[-1] != ('section', stripped):
                blocks.append(('section', stripped))
            continue

        # Detect 【移】 lines — moved text (jp only, no German counterpart here)
        if stripped.startswith('【移】'):
            flush()
            current_type = 'jp_moved'
            current_lines = [stripped]
            continue

        if is_japanese(stripped):
            line_type = 'jp'
        elif is_german(stripped):
            line_type = 'de'
        else:
            line_type = current_type or 'de'

        if line_type != current_type and current_lines:
            flush()

        current_type = line_type
        current_lines.append(stripped)

    flush()
    return blocks

def _collect_jp_for_de_full(blocks, de_idx):
    """Collect jp/jp_moved blocks following a de block at de_idx.

    Rules:
      - Scan ahead past all consecutive jp/jp_moved blocks.
      - If jp and jp_moved are INTERLEAVED (a jp appears after a jp_moved),
        they all translate the same German paragraph — pair everything.
      - If jp_moved blocks only appear as a trailing group after all jp
        blocks, they're content from elsewhere — emit as jp_only.
      - If ONLY jp_moved blocks exist (no jp), they ARE the translation.

    Returns (jp_texts_for_pair, moved_only_texts, next_index).
    """
    boundary = {'de', 'section', 'anm_start', 'anm_label_de'}
    j = de_idx + 1
    following = []
    while j < len(blocks) and blocks[j][0] not in boundary:
        following.append(blocks[j])
        j += 1

    has_regular = any(bt == 'jp' for bt, _ in following)
    has_moved = any(bt == 'jp_moved' for bt, _ in following)

    if has_regular and has_moved:
        # Check if interleaved: does any jp appear AFTER a jp_moved?
        seen_moved = False
        interleaved = False
        for bt, _ in following:
            if bt == 'jp_moved':
                seen_moved = True
            elif bt == 'jp' and seen_moved:
                interleaved = True
                break

        if interleaved:
            # All blocks are part of the same translation — pair everything
            all_texts = [text for bt, text in following if bt in ('jp', 'jp_moved')]
            return all_texts, [], j
        else:
            # jp_moved is a trailing group — from elsewhere
            jp_texts = [text for bt, text in following if bt == 'jp']
            moved_only = [text for bt, text in following if bt == 'jp_moved']
            return jp_texts, moved_only, j
    elif has_regular:
        jp_texts = [text for bt, text in following if bt == 'jp']
        return jp_texts, [], j
    elif has_moved:
        # All jp_moved — treat as translations
        all_texts = [text for bt, text in following if bt == 'jp_moved']
        return all_texts, [], j
    else:
        return [], [], j

def pair_blocks(blocks):
    """Group blocks into renderable items:
       - ('pair', de_text, jp_text)  — side-by-side row
       - ('de_only', de_text)        — German only
       - ('jp_only', jp_text)        — Japanese only
       - ('section', text)
       - ('anm_start', text)
    """
    items = []
    i = 0
    while i < len(blocks):
        btype, content = blocks[i]

        if btype == 'anm_label_de':
            # Merge annotation label with the following de block, then pair with jp
            label = content
            j = i + 1
            # Collect the German body that follows
            de_body = ''
            if j < len(blocks) and blocks[j][0] == 'de':
                de_body = blocks[j][1]
                j += 1
            merged_de = label + '\n\n' + de_body if de_body else label
            # Reuse the same collection logic — pretend j-1 is de_idx
            # so _collect_jp_for_de_full scans from j onward
            boundary = {'de', 'section', 'anm_start', 'anm_label_de'}
            following = []
            k = j
            while k < len(blocks) and blocks[k][0] not in boundary:
                following.append(blocks[k])
                k += 1
            has_regular = any(bt == 'jp' for bt, _ in following)
            has_moved = any(bt == 'jp_moved' for bt, _ in following)
            if has_regular and has_moved:
                seen_m = False
                interl = False
                for bt2, _ in following:
                    if bt2 == 'jp_moved':
                        seen_m = True
                    elif bt2 == 'jp' and seen_m:
                        interl = True
                        break
                if interl:
                    jp_texts = [t for bt2, t in following if bt2 in ('jp', 'jp_moved')]
                    moved_only = []
                else:
                    jp_texts = [t for bt2, t in following if bt2 == 'jp']
                    moved_only = [t for bt2, t in following if bt2 == 'jp_moved']
            elif has_regular:
                jp_texts = [t for bt2, t in following if bt2 == 'jp']
                moved_only = []
            elif has_moved:
                jp_texts = [t for bt2, t in following if bt2 == 'jp_moved']
                moved_only = []
            else:
                jp_texts = []
                moved_only = []
            if jp_texts:
                items.append(('pair', merged_de, '\n\n'.join(jp_texts)))
            else:
                items.append(('de_only', merged_de))
            for mt in moved_only:
                items.append(('jp_only', mt))
            i = k
            continue

        if btype == 'de':
            # Merge consecutive de blocks (paragraphs split by page breaks)
            de_text = content
            merge_end = i + 1
            while merge_end < len(blocks) and blocks[merge_end][0] == 'de':
                de_text += '\n\n' + blocks[merge_end][1]
                merge_end += 1
            # Use merge_end-1 as the effective de_idx for collection
            jp_texts, moved_only, j = _collect_jp_for_de_full(blocks, merge_end - 1)
            if jp_texts:
                items.append(('pair', de_text, '\n\n'.join(jp_texts)))
            else:
                items.append(('de_only', de_text))
            for mt in moved_only:
                items.append(('jp_only', mt))
            i = j
            continue
        elif btype in ('jp', 'jp_moved'):
            items.append(('jp_only', content))
        else:
            items.append((btype, content))
        i += 1
    return items

SUPERSCRIPT_DIGITS = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4',
                      '⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9'}

def fmt(text, lang='de'):
    """Escape and format text, converting paragraph breaks to <br/><br/>."""
    t = esc(text)
    t = t.replace('\n\n', '<br/><br/>')
    t = t.replace('\n', '<br/>')
    return t

def link_footnotes(html_body):
    """Add bidirectional links between body footnote refs and Anmerkungen entries."""
    anm_split = '<div style="background:#f8f5f0'
    pos = html_body.find(anm_split)
    if pos == -1:
        return html_body  # No annotation section

    body_html = html_body[:pos]
    anm_html = html_body[pos:]

    # Step 1: Number annotations sequentially, add anchors
    anm_seq = [0]
    def _anchor_anm(m):
        anm_seq[0] += 1
        n = anm_seq[0]
        original = m.group(0)
        return (f'<a id="fn{n}" href="#fnref{n}" title="本文に戻る" '
                f'style="color:#8b7332; text-decoration:none;">{original}</a>'
                f' <a href="#fnref{n}" style="font-size:0.75em; text-decoration:none;" title="本文へ戻る">↩</a>')
    anm_html = re.sub(r'Anm\.\s*\d+\)', _anchor_anm, anm_html)
    total_anm = anm_seq[0]

    if total_anm == 0:
        return html_body

    # Step 2: Find and link body footnote refs sequentially
    ref_seq = [0]
    # Combined pattern: letter + optional space + (regular digits OR superscript digits) + )
    fnref_pat = re.compile(r'(?<=[a-zA-ZäöüÄÖÜß])(\s*)(\d{1,2}|[⁰¹²³⁴⁵⁶⁷⁸⁹]+)\)')

    def _link_ref(m):
        space = m.group(1)
        num_raw = m.group(2)
        is_super = any(c in SUPERSCRIPT_DIGITS for c in num_raw)

        # Filter out math expressions for superscript matches (e.g. d²i/dy²))
        if is_super:
            start = m.start()
            preceding = body_html[max(0, start - 4):start]
            if re.search(r'[/²³+\-=]', preceding):
                return m.group(0)  # math context, skip

        ref_seq[0] += 1
        n = ref_seq[0]
        if n > total_anm:
            return m.group(0)  # no matching annotation

        num_display = ''.join(SUPERSCRIPT_DIGITS.get(c, c) for c in num_raw)
        return (f'<sup><a id="fnref{n}" href="#fn{n}" title="注{num_display}へ" '
                f'style="color:#8b7332; text-decoration:none;">{num_display})</a></sup>')

    body_html = fnref_pat.sub(_link_ref, body_html)

    return body_html + anm_html

def make_table_row(de_text, jp_text):
    """Generate a Yasastilaka-style table row."""
    return f'''<table>
<tr><td style="{TD_BORDER}">
<div style="{DE_DIV}" lang="de">{fmt(de_text, 'de')}</div>
</td><td>
<div style="{JP_DIV}" lang="ja">{fmt(jp_text, 'ja')}</div>
</td></tr>
</table>'''

def make_de_only_row(de_text):
    return f'''<table>
<tr><td style="{TD_BORDER}">
<div style="{DE_DIV}" lang="de">{esc(de_text)}</div>
</td><td>
<div style="{JP_DIV}; opacity:0.5;" lang="ja">（未訳）</div>
</td></tr>
</table>'''

def make_jp_only_row(jp_text):
    return f'''<table>
<tr><td style="{TD_BORDER}">
</td><td>
<div style="{JP_DIV}" lang="ja">{esc(jp_text)}</div>
</td></tr>
</table>'''

def generate_chapter_html(chapter_num, lines, is_zusaetze=False):
    if is_zusaetze:
        title_de = "Zusätze"
        title_jp = "補遺（各章への追加注記）"
        ch_label = "補遺"
        filename = "zusaetze.html"
    else:
        title_de, title_jp = CHAPTER_TITLES[chapter_num]
        roman = ROMAN[chapter_num]
        ch_label = f"第{roman}章"
        filename = f"kapitel_{chapter_num:02d}.html"

    # Navigation
    if is_zusaetze:
        prev_link = '<a href="kapitel_15.html">← 第ⅩⅤ章</a>'
        next_link = '<a href="index.html">目次 →</a>'
    elif chapter_num == 1:
        prev_link = '<a href="index.html">← 目次</a>'
        next_link = '<a href="kapitel_02.html">第Ⅱ章 →</a>'
    elif chapter_num == 15:
        prev_link = '<a href="kapitel_14.html">← 第ⅩⅣ章</a>'
        next_link = '<a href="zusaetze.html">補遺 →</a>'
    else:
        pn, nn = chapter_num - 1, chapter_num + 1
        prev_link = f'<a href="kapitel_{pn:02d}.html">← 第{ROMAN[pn]}章</a>'
        next_link = f'<a href="kapitel_{nn:02d}.html">第{ROMAN[nn]}章 →</a>'

    blocks = parse_blocks(lines)
    items = pair_blocks(blocks)

    parts = []
    in_anm = False
    section_count = 0

    for item in items:
        if item[0] == 'section':
            section_count += 1
            parts.append(f'<h3 id="s{section_count:02d}" style="{SECTION_STYLE}">{esc(item[1])}</h3>')
        elif item[0] == 'pair':
            parts.append(make_table_row(item[1], item[2]))
        elif item[0] == 'de_only':
            parts.append(make_de_only_row(item[1]))
        elif item[0] == 'jp_only':
            parts.append(make_jp_only_row(item[1]))
        elif item[0] == 'anm_start':
            parts.append(f'<div style="background:#f8f5f0; margin-top:2.5em; padding:1em; border-top:2px dashed #c4b07a;">')
            parts.append(f'<h3 style="{SECTION_STYLE}">{esc(item[1])}</h3>')
            in_anm = True

    if in_anm:
        parts.append('</div>')

    body = '\n'.join(parts)
    body = link_footnotes(body)

    nav_style = 'background:#f5f0e6; padding:0.6em 1em; display:flex; justify-content:space-between; flex-wrap:wrap; gap:0.3em; font-size:0.9em; margin-bottom:1em;'
    a_style = 'color:#8b7332; text-decoration:none;'

    BODY_STYLE = 'font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", "Times New Roman", serif; max-width: 70em; margin: 0 auto; padding: 1em; line-height: 1.8; color: #333;'

    html_doc = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_mod.escape(ch_label)} — {html_mod.escape(title_de)}</title>
<style>
html {{ scroll-behavior: smooth; }}
body {{ {BODY_STYLE} }}
table {{ width: 100%; table-layout: fixed; border-collapse: collapse; margin: 0.8em 0; }}
td {{ vertical-align: top; padding: 0.7em 1.2em; overflow-wrap: break-word; word-break: break-word; }}
a {{ color: #8b7332; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
[id^="fn"], [id^="fnref"] {{ scroll-margin-top: 1.5em; }}
sup a {{ font-weight: bold; }}
</style>
</head>
<body>
<p style="text-align:center; font-size:1.6em; font-weight:bold; letter-spacing:0.1em; margin-bottom:0.2em;">{html_mod.escape(ch_label)}</p>
<p style="text-align:center; font-size:1.05em; color:#8b7332; font-style:italic; margin-bottom:0.2em;">{html_mod.escape(title_de)}</p>
<p style="text-align:center; font-size:1.05em; color:#666; margin-bottom:2em;">{html_mod.escape(title_jp)}</p>

<div style="{nav_style}">
  <span>{prev_link}</span>
  <a href="index.html">目次</a>
  <span>{next_link}</span>
</div>

{body}

<div style="{nav_style} margin-top:2em;">
  <span>{prev_link}</span>
  <a href="index.html">目次</a>
  <span>{next_link}</span>
</div>
</body>
</html>
'''
    return filename, html_doc

def generate_index():
    items = []
    for i in range(1, 16):
        de_t, jp_t = CHAPTER_TITLES[i]
        r = ROMAN[i]
        items.append(f'''<li style="margin:0.8em 0; padding:0.5em; background:#f5f0e6; border-left:3px solid #8b7332;">
  <a href="kapitel_{i:02d}.html" style="color:#8b7332; text-decoration:none;">
    <strong>第{r}章</strong> {jp_t}<br/>
    <span style="font-size:0.85em; font-style:italic; color:#888;">{de_t}</span>
  </a>
</li>''')

    toc = '\n'.join(items)

    return "index.html", f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>感覚の分析 — Die Analyse der Empfindungen — 独日対訳</title>
<style>
body {{ font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", serif; max-width: 700px; margin: 2em auto; padding: 0 1em; color: #333; line-height: 1.8; }}
a {{ color: #8b7332; }}
</style>
</head>
<body>
<p style="text-align:center; font-size:1.6em; font-weight:bold; letter-spacing:0.1em; margin-bottom:0.1em;">感覚の分析</p>
<p style="text-align:center; font-size:1.3em; font-style:italic; color:#8b7332; margin-bottom:0.1em;">Die Analyse der Empfindungen</p>
<p style="text-align:center; font-size:0.95em; color:#666; margin-bottom:0.3em;">und das Verhältnis des Physischen zum Psychischen</p>
<p style="text-align:center; font-size:0.9em; color:#888; margin-bottom:2em;">Ernst Mach · エルンスト・マッハ ｜ 第9版 (1922) ｜ 独日対訳</p>

<div style="background:#f5f0e6; border:1px solid #c4b07a; padding:1em 1.5em; margin-bottom:2em;">
<p style="font-size:0.85em; font-weight:bold; color:#8b7332; letter-spacing:0.1em; border-bottom:1px solid #c4b07a; padding-bottom:0.4em; margin-bottom:0.6em;">目次 INHALTSVERZEICHNIS</p>
<ul style="list-style:none; padding:0;">
{toc}
<li style="margin:1.2em 0 0.8em; padding:0.5em; background:#f8f5f0; border-left:3px solid #c4b07a;">
  <a href="zusaetze.html" style="color:#8b7332; text-decoration:none;">
    <strong>補遺</strong> Zusätze（各章への追加注記 · 全21項目）
  </a>
</li>
</ul>
</div>

<div style="font-size:0.82em; color:#888; border-top:1px solid #c4b07a; padding-top:0.8em; line-height:1.7;">
<p>本対訳版はエルンスト・マッハ『感覚の分析——物理的なものと心理的なものの関係』（第9版、イェーナ：グスタフ・フィッシャー、1922年）の全15章および補遺の対訳である。</p>
<p style="font-style:italic; margin-top:0.3em;">Diese zweisprachige Ausgabe umfaßt alle 15 Kapitel und die Zusätze von Ernst Machs <em>Die Analyse der Empfindungen und das Verhältnis des Physischen zum Psychischen</em> (9. Aufl., Jena: Gustav Fischer, 1922).</p>
</div>
</body>
</html>
'''

# ============== Main ==============
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Index
fname, content = generate_index()
with open(os.path.join(OUTPUT_DIR, fname), 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Created: {fname}")

# Chapters
for ch in range(1, 16):
    filepath = os.path.join(SCRATCHPAD, f"kapitel_{ch}_complete.txt")
    if not os.path.exists(filepath):
        print(f"MISSING: kapitel_{ch}_complete.txt")
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    # Skip header lines (chapter title)
    start = 0
    for i, line in enumerate(raw_lines):
        s = line.strip()
        if s.startswith('§') or (i > 3 and s):
            start = i
            break
    fname, content = generate_chapter_html(ch, [l.rstrip('\n') for l in raw_lines[start:]])
    with open(os.path.join(OUTPUT_DIR, fname), 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {fname} ({len(raw_lines)} lines)")

# Zusätze
filepath = os.path.join(SCRATCHPAD, "zusaetze_complete.txt")
with open(filepath, 'r', encoding='utf-8') as f:
    raw_lines = f.readlines()
fname, content = generate_chapter_html(0, [l.rstrip('\n') for l in raw_lines[2:]], is_zusaetze=True)
with open(os.path.join(OUTPUT_DIR, fname), 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Created: {fname} ({len(raw_lines)} lines)")

print(f"\nDone! All files in: {OUTPUT_DIR}")

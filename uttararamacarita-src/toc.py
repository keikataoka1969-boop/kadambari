"""Build the overview (TOC) page from the act files."""
import re, sys, collections
sys.path.insert(0, sys.path[0])
from render import parse, page, ACTS, ROMAN, esc, bi, skt_inline, metre_name
from translit import iast2dev

PLACES = {1: 'アヨーディヤー（王宮）', 2: 'ダンダカの森・パンチャヴァティー', 3: 'パンチャヴァティー（ゴーダーヴァリー河畔）',
          4: 'ヴァールミーキの庵', 5: '庵の近くの戦場', 6: '庵の近く', 7: 'ガンガー河畔の上演場'}
EVENTS = {1: '絵画の観覧／民の噂／シーター追放の決意', 2: 'アートレーイーの語り／シャンブーカ討伐／森の追憶',
          3: '影となったシーター／ラーマの失神と蘇生／悲愴の極み', 4: 'ジャナカとカウサリヤーの対面／ラヴァの登場／祭馬',
          5: 'ラヴァとチャンドラケートゥの対決／神器', 6: 'ラーマの到着／双子の認知／『ラーマーヤナ』の朗誦',
          7: '劇中劇／シーターの帰還／潔白の宣言と再会'}
SHORT = {1: '絵画', 2: '森への入場', 3: '影', 4: '対面', 5: '武勇', 6: '認知', 7: '再会'}
SKT = {1: 'citradarśanam', 2: 'pañcavaṭīpraveśaḥ', 3: 'chāyā', 4: 'kausalyājanakayogaḥ', 5: 'kumāravikramaḥ', 6: 'kumārapratyabhijñānam', 7: 'sammelanam'}
MLABEL = {'indravajrā': 'upajāti（indravajrā 系）', 'upendravajrā': 'upajāti（indravajrā 系）'}
KEY = {1: 39, 2: 7, 3: 47, 4: 11, 5: 17, 6: 12, 7: 20}
RASA = {1: ('śṛṅgāra → karuṇa', '愛の追憶から悲愴へ'), 2: ('karuṇa / bhayānaka', '悲愴と森の恐ろしさ'),
        3: ('karuṇa', '悲愴の極み'), 4: ('karuṇa / vātsalya', '悲愴と子への愛しさ'),
        5: ('vīra', '勇'), 6: ('vīra → vātsalya / karuṇa', '勇から親子の情、悲愴へ'),
        7: ('adbhuta → karuṇa → ānanda', '驚異、悲愴、そして歓喜')}
CHARS = [
    ('rāmaḥ', 'ラーマ', 'アヨーディヤーの王。民の声に従いシーターを捨てる', 'I II III VI VII'),
    ('sītā', 'シーター', 'ラーマの妃、大地の娘。第三幕では見えない「影」として現れる', 'I III VII'),
    ('lakṣmaṇaḥ', 'ラクシュマナ', 'ラーマの弟。シーターを森に置き去りにする役を負う', 'I VII'),
    ('kuśaḥ', 'クシャ', 'ラーマとシーターの双子の兄', 'VI VII'),
    ('lavaḥ', 'ラヴァ', '双子の弟。祭馬を奪いチャンドラケートゥと戦う', 'IV V VI VII'),
    ('candraketuḥ', 'チャンドラケートゥ', 'ラクシュマナとウールミラーの子。祭馬の護衛隊長', 'V VI'),
    ('janakaḥ', 'ジャナカ', 'シーターの父、ヴィデーハの王仙', 'IV'),
    ('kausalyā', 'カウサリヤー', 'ラーマの母', 'IV'),
    ('arundhatī', 'アルンダティー', 'ヴァシシュタの妻。第七幕でシーターの潔白を宣言する', 'IV VII'),
    ('vālmīkiḥ', 'ヴァールミーキ', '最初の詩人。双子を養い、劇中劇の作者となる', 'VII'),
    ('vāsantī', 'ヴァーサンティー', 'ジャナスターナの森の女神、シーターの親友', 'II III'),
    ('tamasā', 'タマサー', '河の女神。見えないシーターに付き添う', 'III'),
    ('sumantraḥ', 'スマントラ', 'ダシャラタ以来の老御者', 'V'),
    ('śambūkaḥ', 'シャンブーカ', '苦行するシュードラ。ラーマに討たれ天上の姿となる', 'II'),
    ('pṛthivī / gaṅgā', '大地の女神／ガンガー', 'シーターを救い守る二柱の女神', 'VII'),
]


def collect():
    data = {}
    for a in range(1, 8):
        meta, blocks = parse('act%d.txt' % a)
        vs = [b for b in blocks if b['t'] == 'V']
        nums = sorted({b['n'] for b in vs})
        mt = collections.Counter()
        seen = set()
        for b in vs:
            if b['n'] in seen:
                continue
            seen.add(b['n'])
            halves = [re.sub(r'\{[^}]*\}', ' ', h) for h in b['s']]
            m = b.get('metre') or metre_name(halves) or '不明'
            m = MLABEL.get(m, m)
            mt[m] += 1
        key = next(b for b in vs if b['n'] == KEY[a])
        data[a] = dict(meta=meta, n=len(nums), metres=mt, key=key)
    return data


def bar_chart(data):
    W, H, pl, pb, pt = 640, 240, 36, 34, 18
    mx = 60
    bw = 46
    gap = (W - pl - 10 - 7 * bw) / 6
    out = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-labelledby="ch-t">' % (W, H),
           '<title id="ch-t">各幕の偈の数</title>']
    for v in (0, 20, 40, 60):
        y = pt + (H - pt - pb) * (1 - v / mx)
        out.append('<line class="grid" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/>' % (pl, W - 6, y, y))
        out.append('<text class="tick" x="%d" y="%.1f">%d</text>' % (pl - 6, y + 4, v))
    for a in range(1, 8):
        n = data[a]['n']
        x = pl + 6 + (a - 1) * (bw + gap)
        h = (H - pt - pb) * n / mx
        y = H - pb - h
        r = 4
        path = 'M%.1f,%.1f v%.1f a%d,%d 0 0 1 %d,-%d h%.1f a%d,%d 0 0 1 %d,%d v%.1f z' % (
            x, H - pb, -(h - r), r, r, r, r, bw - 2 * r, r, r, r, r, h - r)
        out.append('<g class="bar" tabindex="0"><title>第%s幕：%d偈</title>' % ('一二三四五六七'[a - 1], n))
        out.append('<rect class="hit" x="%.1f" y="%d" width="%.1f" height="%d"/>' % (x - gap / 2, pt, bw + gap, H - pt - pb))
        out.append('<path class="mark" d="%s"/>' % path)
        out.append('<text class="val" x="%.1f" y="%.1f">%d</text>' % (x + bw / 2, y - 6, n))
        out.append('</g>')
        out.append('<text class="xl" x="%.1f" y="%d">%s</text>' % (x + bw / 2, H - pb + 20, ROMAN[a]))
    out.append('<line class="axis" x1="%d" x2="%d" y1="%d" y2="%d"/>' % (pl, W - 6, H - pb, H - pb))
    out.append('</svg>')
    return '\n'.join(out)


def flow_svg():
    # timeline: Act I, then 12-year gap, Acts II-VII in a few days
    W, H = 720, 170
    xs = [40, 210, 300, 390, 480, 570, 660]
    o = ['<svg class="flow" viewBox="0 0 %d %d" role="img" aria-labelledby="fl-t">' % (W, H),
         '<title id="fl-t">劇の時間と場所の構成</title>',
         '<line class="tl" x1="%d" x2="%d" y1="70" y2="70"/>' % (xs[0], xs[0] + 50),
         '<line class="tl gap" x1="%d" x2="%d" y1="70" y2="70"/>' % (xs[0] + 50, xs[1] - 30),
         '<line class="tl" x1="%d" x2="%d" y1="70" y2="70"/>' % (xs[1] - 30, xs[-1]),
         '<text class="gapl" x="%d" y="58">12年の歳月</text>' % ((xs[0] + xs[1]) // 2)]
    places = ['アヨーディヤー', 'ダンダカの森', '', 'ヴァールミーキの庵', '', '', 'ガンガー河畔']
    for i, x in enumerate(xs):
        a = i + 1
        o.append('<a href="uttararamacarita-act%d.html"><g class="node"><circle cx="%d" cy="70" r="15"/>'
                 '<text class="nl" x="%d" y="75">%s</text></g></a>' % (a, x, x, ROMAN[a]))
        o.append('<text class="nt" x="%d" y="110">%s</text>' % (x, esc(SHORT[a])))
    # place brackets
    def bracket(x1, x2, label, y=140):
        o.append('<path class="br" d="M%d,%d v6 H%d v-6"/>' % (x1 - 14, y - 6, x2 + 14))
        o.append('<text class="bl" x="%d" y="%d">%s</text>' % ((x1 + x2) // 2, y + 18, label))
    bracket(xs[0], xs[0], 'アヨーディヤー')
    bracket(xs[1], xs[2], 'ダンダカの森')
    bracket(xs[3], xs[5], 'ヴァールミーキの庵とその周辺')
    bracket(xs[6], xs[6], 'ガンガー河畔')
    o.append('<text class="cap" x="%d" y="24">追放</text>' % xs[0])
    o.append('<text class="cap" x="%d" y="24">別離の悲しみ</text>' % ((xs[1] + xs[2]) // 2))
    o.append('<text class="cap" x="%d" y="24">子らの登場と認知</text>' % xs[4])
    o.append('<text class="cap" x="%d" y="24">再会</text>' % xs[6])
    o.append('</svg>')
    return '\n'.join(o)


def build():
    data = collect()
    total = sum(d['n'] for d in data.values())
    allm = collections.Counter()
    for d in data.values():
        allm.update(d['metres'])
    h = []
    ih, dh = skt_inline('uttararāmacaritam')
    h.append(f'''<section class="act-head toc-head">
  <p class="act-no">総覧<span class="roman">Contents</span></p>
  <h1><span class="h-jp">ウッタララーマチャリタ</span><span class="h-skt">{bi(ih, dh)}</span></h1>
  <p class="synopsis">バヴァブーティ（8世紀前半）作の七幕の戯曲。『ラーマーヤナ』の後日譚——ラーヴァナを討って即位したラーマが、民の噂のためにシーターを捨て、十二年後に双子の子らとともに再会するまで——を描く。ラーマの悲嘆を主調とし、「ラサ（情趣）はただひとつ、悲愴（カルナ）のみ」（第三幕第47偈）と宣言する、悲愴の劇の最高峰とされる。</p>
  <div class="stats">
    <div><b>7</b><span>幕</span></div><div><b>{total}</b><span>偈（全256のうち）</span></div><div><b>12</b><span>年（第一幕と第二幕の間）</span></div><div><b>{len(allm)}</b><span>種の韻律</span></div>
  </div>
</section>''')
    # TOC table
    h.append('<h2 class="toc-h">目次</h2><div class="tablewrap"><table class="toc"><thead><tr><th>幕</th><th>題名</th><th>場所</th><th class="num">偈</th><th>主な出来事</th></tr></thead><tbody>')
    for a in range(1, 8):
        sk = SKT[a]
        ih, dh = skt_inline(sk)
        h.append('<tr><td class="ro"><a href="uttararamacarita-act%d.html">%s</a></td><td><a href="uttararamacarita-act%d.html">%s</a><br><span class="sk">%s</span></td><td>%s</td><td class="num">%d</td><td>%s</td></tr>' % (
            a, ROMAN[a], a, esc(ACTS[a][2]), bi(ih, dh), esc(PLACES[a]), data[a]['n'], esc(EVENTS[a])))
    h.append('</tbody></table></div>')
    # structure
    h.append('<h2 class="toc-h">構成</h2><p class="lead">第一幕で追放が決まったあと、物語は十二年後に飛ぶ。第二幕から第七幕までは、ほぼ連続した数日の出来事である。円をクリックすると各幕へ移動する。</p>')
    h.append('<div class="figwrap">' + flow_svg() + '</div>')
    # chart + rasa table
    h.append('<div class="two"><figure class="fig"><figcaption>各幕の偈の数</figcaption>' + bar_chart(data) +
             '<p class="figcap">第六幕は底本 OCR の欠落により42偈中38偈を収録。</p></figure>')
    h.append('<div><h3 class="sub">各幕の主調となるラサ（情趣）</h3><div class="tablewrap"><table class="rasa"><thead><tr><th>幕</th><th>ラサ</th><th>趣</th></tr></thead><tbody>')
    for a in range(1, 8):
        h.append('<tr><td class="ro">%s</td><td class="sk">%s</td><td>%s</td></tr>' % (ROMAN[a], esc(RASA[a][0]), esc(RASA[a][1])))
    h.append('</tbody></table></div></div></div>')
    # metres table
    h.append('<h2 class="toc-h">韻律の分布</h2><p class="lead">各偈の音節の長短（guru / laghu）を韻律の型と照合した結果。対訳本文の各偈にも韻律名を付した。</p><div class="tablewrap"><table class="metres"><thead><tr><th>韻律</th>')
    for a in range(1, 8):
        h.append('<th class="num">%s</th>' % ROMAN[a])
    h.append('<th class="num">計</th></tr></thead><tbody>')
    for m, c in allm.most_common():
        h.append('<tr><td class="sk">%s</td>' % esc(m))
        for a in range(1, 8):
            v = data[a]['metres'].get(m, 0)
            h.append('<td class="num%s">%s</td>' % (' zero' if not v else '', v or '·'))
        h.append('<td class="num tot">%d</td></tr>' % c)
    h.append('</tbody></table></div>')
    # characters
    h.append('<h2 class="toc-h">主な登場人物</h2><div class="tablewrap"><table class="chars"><thead><tr><th>人物</th><th>役柄</th><th>登場する幕</th></tr></thead><tbody>')
    for sk, jp, desc, acts in CHARS:
        ih = esc(sk[:1].upper() + sk[1:])
        dh = esc(' / '.join(iast2dev(x.strip()) for x in sk.split('/')))
        h.append('<tr><td><b>%s</b><br><span class="sk">%s</span></td><td>%s</td><td class="ro">%s</td></tr>' % (
            esc(jp), bi(ih, dh), esc(desc), acts))
    h.append('</tbody></table></div>')
    # synopses
    h.append('<h2 class="toc-h">各幕の梗概と名偈</h2><div class="syn">')
    for a in range(1, 8):
        k = data[a]['key']
        lines = [re.sub(r'\{[^}]*\}\s*', '', x) for x in k['s']]
        iast = '<br>'.join(esc(' '.join(p.strip() for p in l.split('/'))) for l in lines)
        dev = '<br>'.join(esc(iast2dev(' '.join(p.strip() for p in l.split('/')))) for l in lines)
        jp = '<br>'.join(esc(x) for x in k['j'])
        h.append(f'''<article class="syn-a"><h3><a href="uttararamacarita-act{a}.html"><span class="ro">{ROMAN[a]}</span>{esc(ACTS[a][1])}「{esc(ACTS[a][2])}」</a></h3>
<p>{esc(data[a]['meta'].get('synopsis', ''))}</p>
<blockquote><p class="q-skt">{bi(iast, dev)}</p><p class="q-jp">{jp}</p><cite><a href="uttararamacarita-act{a}.html#v{a}-{KEY[a]}">{ROMAN[a]}.{KEY[a]}</a></cite></blockquote></article>''')
    h.append('</div>')
    # edition notes
    h.append('''<h2 class="toc-h">この版について</h2><div class="ednotes">
<p><b>底本。</b>M. R. Kale 校訂本（Vīrarāghava 注付き、Motilal Banarsidass）の OCR テキストを底本とし、全幕の本文を原典と照合して校訂した。偈はすべて韻律（音節の長短の型）で検証し、OCR の誤りは、注釈の語釈・異読・韻律に基づいて訂正した。主な訂正は各偈の注に記した。</p>
<p><b>プラークリット。</b>女性や従者の台詞は原作ではプラークリットで書かれているが、Kale 本の本文に従い、サンスクリット訳（chāyā）で示した。</p>
<p><b>文字の切り替え。</b>上部のボタンで、サンスクリット本文を Devanāgarī・IAST（ローマ字転写）・併記のいずれでも表示できる。選択は次に開いたときにも保たれる。「注」ボタンで注の表示・非表示を切り替えられる。</p>
<p><b>欠落。</b>底本 OCR には第六幕の一頁（第21〜24偈を含む）が欠けている。推測で本文を補うことはせず、該当箇所に欠落を明記した。第六幕第40偈にも、OCR の乱れによる本文の欠落がある。</p>
<p><b>和訳。</b>サンスクリット原文から直接訳した。</p></div>''')
    body = '\n'.join(h)
    out = page('Uttararāmacarita 総覧', 'バヴァブーティ『ウッタララーマチャリタ』全七幕の目次・構成図・韻律分布・登場人物・梗概', body, None)
    open(sys.argv[1], 'w', encoding='utf-8').write(out)
    print('ok', total)


if __name__ == '__main__':
    build()

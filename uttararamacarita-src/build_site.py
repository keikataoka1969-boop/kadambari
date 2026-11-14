"""Build the edition for the brahmasiddhi site: uttararamacarita/index.html + act1..7.html."""
import os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
tmp = os.path.join(here, 'final')
os.makedirs(tmp, exist_ok=True)
for i in range(1, 8):
    subprocess.run([sys.executable, os.path.join(here, 'render.py'), os.path.join(here, 'act%d.txt' % i),
                    os.path.join(tmp, 'uttararamacarita-act%d.html' % i)], cwd=here, check=True, capture_output=True)
subprocess.run([sys.executable, os.path.join(here, 'toc.py'), os.path.join(tmp, 'uttararamacarita-toc.html')], cwd=here, check=True, capture_output=True)
TOP = '<a class="sitetop" href="../index.html">← 対訳一覧</a>'
for src, dst in [('uttararamacarita-toc.html', 'index.html')] + [('uttararamacarita-act%d.html' % i, 'act%d.html' % i) for i in range(1, 8)]:
    h = open(os.path.join(tmp, src), encoding='utf-8').read()
    h = h.replace('href="uttararamacarita-toc.html', 'href="index.html').replace('href="uttararamacarita-act', 'href="act')
    assert 'uttararamacarita-' not in h, src
    h = h.replace('<header class="bar">\n', '<header class="bar">\n  ' + TOP + '\n', 1)
    h = h.replace('</style>', '.sitetop { font-size: 12.5px; color: var(--muted); text-decoration: none; }\n.sitetop:hover { color: var(--indigo); }\n</style>', 1)
    open(os.path.join(out, dst), 'w', encoding='utf-8').write(h)
print('built', out)

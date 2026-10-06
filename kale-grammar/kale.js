/* Kale 文法教科書 — 共通スクリプト：明暗切替・IAST 自動表示・Śivasūtra */
(function () {
  // ---- theme ----
  try { var t = localStorage.getItem('kale-theme'); if (t) document.documentElement.setAttribute('data-theme', t); } catch (e) {}
  var tb = document.getElementById('theme');
  if (tb) tb.addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme');
    var dark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    var nt = dark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nt);
    try { localStorage.setItem('kale-theme', nt); } catch (e) {}
  });

  // ---- Devanāgarī → IAST ----
  var V = { 'अ':'a','आ':'ā','इ':'i','ई':'ī','उ':'u','ऊ':'ū','ऋ':'ṛ','ॠ':'ṝ','ऌ':'ḷ','ॡ':'ḹ','ए':'e','ऐ':'ai','ओ':'o','औ':'au' };
  var M = { 'ा':'ā','ि':'i','ी':'ī','ु':'u','ू':'ū','ृ':'ṛ','ॄ':'ṝ','ॢ':'ḷ','ॣ':'ḹ','े':'e','ै':'ai','ो':'o','ौ':'au' };
  var C = { 'क':'k','ख':'kh','ग':'g','घ':'gh','ङ':'ṅ','च':'c','छ':'ch','ज':'j','झ':'jh','ञ':'ñ','ट':'ṭ','ठ':'ṭh','ड':'ḍ','ढ':'ḍh','ण':'ṇ',
            'त':'t','थ':'th','द':'d','ध':'dh','न':'n','प':'p','फ':'ph','ब':'b','भ':'bh','म':'m','य':'y','र':'r','ल':'l','ळ':'ḷ','व':'v',
            'श':'ś','ष':'ṣ','स':'s','ह':'h' };
  var O = { 'ं':'ṃ','ः':'ḥ','ँ':'m̐','ऽ':'’','।':'|','॥':'||','ᳵ':'ẖ','ᳶ':'ḫ','॰':'°',
            '०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9' };
  function toIAST(s) {
    var out = '', i, ch, nx;
    for (i = 0; i < s.length; i++) {
      ch = s[i];
      if (C[ch]) {
        out += C[ch]; nx = s[i + 1];
        if (nx === '़') { i++; nx = s[i + 1]; }
        if (nx === '्') { i++; if (s[i + 1] === '‍' || s[i + 1] === '‌') i++; }
        else if (M[nx]) { out += M[nx]; i++; }
        else out += 'a';
      } else if (V[ch]) out += V[ch];
      else if (M[ch]) out += M[ch];
      else if (O[ch] !== undefined) out += O[ch];
      else if (ch === '‍' || ch === '‌') continue;
      else out += ch;
    }
    return out;
  }
  window.kaleIAST = toIAST;
  var DEV = /[ऀ-ॿ]/;
  function addTr(el, tag) {
    if (el.querySelector(':scope > .tr') || el.hasAttribute('data-notr')) return;
    var txt = el.textContent.replace(/\s+/g, ' ').trim();
    if (!DEV.test(txt)) return;
    var sp = document.createElement(tag || 'span'); sp.className = 'tr'; sp.setAttribute('aria-hidden', 'true');
    sp.textContent = toIAST(txt); el.appendChild(sp);
  }
  // 例文（左列）
  document.querySelectorAll('.ex > .f').forEach(function (el) { addTr(el); });
  // 典拠
  document.querySelectorAll('.sutra > [lang="sa"]').forEach(function (el) {
    if (el.nextElementSibling && el.nextElementSibling.classList.contains('tr')) return;
    var lines = el.innerText.split(/\n/).map(function (l) { return l.trim(); }).filter(Boolean);
    var sp = document.createElement('span'); sp.className = 'tr';
    lines.forEach(function (l, k) { if (k) sp.appendChild(document.createElement('br')); sp.appendChild(document.createTextNode(toIAST(l))); });
    el.insertAdjacentElement('afterend', sp);
  });
  // 結果の形
  document.querySelectorAll('.forms4 .sa').forEach(function (el) {
    var sp = document.createElement('span'); sp.className = 'tr'; sp.textContent = toIAST(el.textContent.trim());
    el.insertAdjacentElement('afterend', sp);
  });

  // ---- Śivasūtra & pratyāhāra ----
  var box = document.getElementById('shiva');
  if (!box) return;
  var S = [['अ','इ','उ','ण्'],['ऋ','ऌ','क्'],['ए','ओ','ङ्'],['ऐ','औ','च्'],['ह','य','व','र','ट्'],['ल','ण्'],
           ['ञ','म','ङ','ण','न','म्'],['झ','भ','ञ्'],['घ','ढ','ध','ष्'],['ज','ब','ग','ड','द','श्'],
           ['ख','फ','छ','ठ','थ','च','ट','त','व्'],['क','प','य्'],['श','ष','स','र्'],['ह','ल्']];
  var cells = [];
  S.forEach(function (row, i) {
    var d = document.createElement('div'); d.className = 'ss';
    d.innerHTML = '<div class="n">' + (i + 1) + '</div>';
    var ls = document.createElement('div'); ls.className = 'ls';
    row.forEach(function (ch, j) {
      var sp = document.createElement('span'); sp.textContent = ch;
      var isIt = (j === row.length - 1); if (isIt) sp.className = 'it';
      ls.appendChild(sp); cells.push({ el: sp, s: i, it: isIt, ch: ch });
    });
    d.appendChild(ls); box.appendChild(d);
  });
  var P = [['अण्','अ',0,0,'अ इ उ（短母音 a・i・u）'],['इक्','इ',0,1,'इ उ ऋ ऌ'],['अच्','अ',0,3,'すべての母音'],
           ['हल्','ह',4,13,'すべての子音'],['अल्','अ',0,13,'字母全体'],['यण्','य',4,5,'半母音 य व र ल'],
           ['हश्','ह',4,9,'軟音（有声）子音'],['खर्','ख',10,12,'硬音（無声）子音'],['जश्','ज',9,9,'軟音の無気音 ज ब ग ड द'],
           ['झष्','झ',7,8,'軟音の有気音 झ भ घ ढ ध'],
           ['अक्','अ',0,1,'अ इ उ ऋ ऌ（単母音）',1],['एङ्','ए',2,2,'ए ओ',1],['ऐच्','ऐ',3,3,'ऐ औ',1],['एच्','ए',2,3,'二重母音 ए ओ ऐ औ',1],
           ['मय्','म',6,11,'鼻音 ङ ञ を除く 5 類の子音',1],['झल्','झ',7,13,'鼻音・半母音以外の子音',1],['झर्','झ',7,12,'鼻音・半母音・ह 以外の子音',1],['झय्','झ',7,11,'閉鎖音のうち鼻音以外',1]];
  var chips = document.getElementById('prchips'), out = document.getElementById('prout');
  function show(p, btn) {
    Array.prototype.forEach.call(chips.children, function (c) { c.setAttribute('aria-pressed', 'false'); });
    btn.setAttribute('aria-pressed', 'true');
    var on = false, list = [];
    cells.forEach(function (c) {
      c.el.classList.remove('on', 'on-it');
      if (!on && !c.it && c.s === p[2] && c.ch === p[1]) on = true;
      if (on && !c.it && c.s <= p[3]) { c.el.classList.add('on'); list.push(c.ch); }
      if (c.it && c.s === p[3]) { c.el.classList.add('on-it'); on = false; }
    });
    out.innerHTML = '<b>' + p[0] + '</b> <i class="iast">' + toIAST(p[0]) + '</i>　＝　' + p[4] +
      '　〔' + list.length + ' 字：<span lang="sa">' + list.join(' ') + '</span>〕';
  }
  P.forEach(function (p) {
    var bt = document.createElement('button'); bt.type = 'button'; bt.textContent = p[0];
    bt.setAttribute('aria-pressed', 'false'); if (p[5]) bt.className = 'later';
    bt.addEventListener('click', function () { show(p, bt); }); chips.appendChild(bt);
  });
})();

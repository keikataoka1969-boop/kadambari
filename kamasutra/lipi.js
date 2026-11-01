/* Kāmasūtra 対訳 — IAST ⇄ Devanāgarī 表示切替
 * サンスクリット本文（.sanskrit, .sk, .sanskrit-verse, .verse-sanskrit）、
 * 語句（.iast, .term-sk）、奥付（.colophon, .final-colophon）の IAST を
 * その場でデーヴァナーガリーに変換する。原文は保持し、いつでも IAST に戻せる。
 */
(function () {
  "use strict";

  var TARGETS = ".sanskrit, .sk, .sanskrit-verse, .verse-sanskrit, .iast, .term, .term-sk, .colophon, .final-colophon";
  var STRICT = ".colophon, .final-colophon"; // 和文混在：大文字を含む語（書名・GRETIL 等）は変換しない
  var KEY = "kamasutra-lipi";

  var VOWELS = {
    "a": ["अ", ""], "ā": ["आ", "ा"], "i": ["इ", "ि"], "ī": ["ई", "ी"],
    "u": ["उ", "ु"], "ū": ["ऊ", "ू"], "ṛ": ["ऋ", "ृ"], "ṝ": ["ॠ", "ॄ"],
    "ḷ": ["ऌ", "ॢ"], "ḹ": ["ॡ", "ॣ"], "e": ["ए", "े"], "ai": ["ऐ", "ै"],
    "o": ["ओ", "ो"], "au": ["औ", "ौ"]
  };
  var CONS = {
    "kh": "ख", "gh": "घ", "ch": "छ", "jh": "झ", "ṭh": "ठ", "ḍh": "ढ",
    "th": "थ", "dh": "ध", "ph": "फ", "bh": "भ",
    "k": "क", "g": "ग", "ṅ": "ङ", "c": "च", "j": "ज", "ñ": "ञ",
    "ṭ": "ट", "ḍ": "ड", "ṇ": "ण", "t": "त", "d": "द", "n": "न",
    "p": "प", "b": "ब", "m": "म", "y": "य", "r": "र", "l": "ल",
    "v": "व", "ś": "श", "ṣ": "ष", "s": "स", "h": "ह", "ḻ": "ळ"
  };
  var OTHER = { "ṃ": "ं", "ṁ": "ं", "ḥ": "ः", "'": "ऽ", "’": "ऽ" };
  var DIGITS = "०१२३४५६७८९";
  var VIRAMA = "्";

  function matchAt(s, i, table) {
    var two = s.substr(i, 2);
    if (table[two] !== undefined) return two;
    var one = s.charAt(i);
    if (table[one] !== undefined) return one;
    return null;
  }

  /* 1語（ハイフン連結を含む）を変換 */
  function translitWord(w) {
    w = w.normalize("NFC").toLowerCase().replace(/[-‐]/g, "");
    var out = "", i = 0, pendingCons = false;
    while (i < w.length) {
      // "aï"/"aü" などは扱わない（IAST の分音記号付き母音は稀）
      var c = matchAt(w, i, CONS);
      if (c) {
        if (pendingCons) out += VIRAMA;
        out += CONS[c];
        pendingCons = true;
        i += c.length;
        continue;
      }
      var v = matchAt(w, i, VOWELS);
      if (v) {
        out += pendingCons ? VOWELS[v][1] : VOWELS[v][0];
        pendingCons = false;
        i += v.length;
        continue;
      }
      var ch = w.charAt(i);
      if (pendingCons) { out += VIRAMA; pendingCons = false; }
      if (OTHER[ch] !== undefined) out += OTHER[ch];
      else if (ch >= "0" && ch <= "9") out += DIGITS.charAt(+ch);
      else out += ch;
      i += 1;
    }
    if (pendingCons) out += VIRAMA;
    return out;
  }

  var LETTERS = "a-zA-ZāīūṛṝḷḹṅñṭḍṇśṣṃṁḥḻĀĪŪṚṜḶṄÑṬḌṆŚṢṂḤ";
  var WORD_RE = new RegExp("[" + LETTERS + "'’][" + LETTERS + "'’\\-‐]*", "g");
  var HAS_UPPER = /[A-ZĀĪŪṚṜḶṄÑṬḌṆŚṢṂḤ]/;

  function translitText(s, strict) {
    // 句読点：‖ // → ॥、| / → ।（数字に挟まれた "." は番号なので残す）
    s = s.replace(/\s*(\/\/|\|\|)\s*/g, " ॥ ").replace(/\s*[\/|]\s*/g, " । ");
    s = s.replace(/([^\d\s])\.(?=\s|$)/g, "$1 ।");
    // 印刷本の慣例：子音終わりの語は次の語と続けて書く（puruṣas tu → पुरुषस्तु）、avagraha 前の空白を詰める
    s = s.replace(/([kgṅcjñṭḍṇtdnpbmyrlvśṣs])\s+(?=[a-zāīūṛṝḷḹṅñṭḍṇśṣ])/g, "$1");
    s = s.replace(/\s+(['’])/g, "$1");
    s = s.replace(WORD_RE, function (w) {
      if (strict && HAS_UPPER.test(w)) return w;
      return translitWord(w);
    });
    s = s.replace(/[0-9]/g, function (d) { return DIGITS.charAt(+d); });
    return s.replace(/ {2,}/g, " ");
  }

  var originals = new Map();
  var CJK = /[　-ヿ㐀-鿿＀-￯]/;

  function collectNodes() {
    var seen = new Set(), list = [];
    document.querySelectorAll(TARGETS).forEach(function (el) {
      var strict = !!el.closest(STRICT);
      var tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
      var n;
      while ((n = tw.nextNode())) {
        if (seen.has(n) || !n.nodeValue.trim()) continue;
        if (n.parentElement && n.parentElement.closest("script, style, .lipi-switch")) continue;
        seen.add(n);
        list.push([n, strict || CJK.test(n.nodeValue)]);
      }
    });
    return list;
  }

  function convertMixed(s) {
    // 和文混在ノード：CJK を含まない区間だけを変換
    return s.replace(/[^　-ヿ㐀-鿿＀-￯]+/g, function (seg) {
      return /[a-zāīūṛṅñṭḍṇśṣṃḥ]/.test(seg) ? translitText(seg, true) : seg;
    });
  }

  function apply(mode) {
    var root = document.documentElement;
    if (mode === "deva") {
      collectNodes().forEach(function (pair) {
        var n = pair[0];
        if (!originals.has(n)) originals.set(n, n.nodeValue);
        var src = originals.get(n);
        n.nodeValue = pair[1] ? convertMixed(src) : translitText(src, false);
      });
      root.classList.add("lipi-deva");
    } else {
      originals.forEach(function (v, n) { n.nodeValue = v; });
      root.classList.remove("lipi-deva");
    }
    document.querySelectorAll(".lipi-switch button").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-lipi") === mode ? "true" : "false");
    });
    try { localStorage.setItem(KEY, mode); } catch (e) {}
  }

  function injectStyle() {
    var css =
      ".lipi-switch{position:fixed;top:.75rem;right:.75rem;z-index:50;display:flex;" +
      "border:1px solid var(--border,#ddd5c8);border-radius:999px;overflow:hidden;" +
      "background:var(--bg-card,#fffdf8);box-shadow:0 1px 4px rgba(0,0,0,.08);font-size:.78rem}" +
      ".lipi-switch button{all:unset;cursor:pointer;padding:.3rem .75rem;line-height:1.4;" +
      "color:var(--text-secondary,#6b5d4d);font-family:'Noto Serif Devanagari','Noto Serif JP',serif}" +
      ".lipi-switch button+button{border-left:1px solid var(--border,#ddd5c8)}" +
      ".lipi-switch button[aria-pressed=true]{background:var(--accent,#a0522d);color:var(--bg-card,#fff)}" +
      ".lipi-switch button:focus-visible{outline:2px solid var(--accent,#a0522d);outline-offset:-2px}" +
      "html.lipi-deva :is(.sanskrit,.sk,.sanskrit-verse,.verse-sanskrit,.iast,.term,.term-sk)" +
      "{font-family:'Noto Serif Devanagari',serif;font-style:normal;letter-spacing:0}" +
      "@media print{.lipi-switch{display:none}}";
    var st = document.createElement("style");
    st.textContent = css;
    document.head.appendChild(st);
  }

  function injectSwitch() {
    var box = document.createElement("div");
    box.className = "lipi-switch";
    box.setAttribute("role", "group");
    box.setAttribute("aria-label", "サンスクリット表記の切替");
    box.innerHTML =
      '<button type="button" data-lipi="iast" title="ローマ字転写（IAST）で表示">IAST</button>' +
      '<button type="button" data-lipi="deva" title="デーヴァナーガリー文字で表示">देवनागरी</button>';
    box.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-lipi]");
      if (b) apply(b.getAttribute("data-lipi"));
    });
    document.body.appendChild(box);
  }

  function init() {
    injectStyle();
    injectSwitch();
    var mode = "iast";
    try { mode = localStorage.getItem(KEY) || "iast"; } catch (e) {}
    apply(mode);
  }

  window.KamasutraLipi = { translitText: translitText, apply: apply };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

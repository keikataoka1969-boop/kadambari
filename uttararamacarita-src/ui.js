(function () {
  var root = document.documentElement;
  function get(k, d) { try { var v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } }
  function put(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function setScript(s) {
    root.setAttribute('data-script', s);
    document.querySelectorAll('[data-script]').forEach(function (b) {
      if (b.tagName === 'BUTTON') b.setAttribute('aria-pressed', b.getAttribute('data-script') === s ? 'true' : 'false');
    });
    put('urc-script', s);
  }
  function setNotes(on) {
    root.classList.toggle('no-notes', !on);
    var b = document.querySelector('[data-notes]');
    if (b) b.setAttribute('aria-pressed', on ? 'true' : 'false');
    put('urc-notes', on ? '1' : '0');
  }
  setScript(get('urc-script', 'iast'));
  setNotes(get('urc-notes', '1') === '1');
  document.querySelectorAll('button[data-script]').forEach(function (b) {
    b.addEventListener('click', function () { setScript(b.getAttribute('data-script')); });
  });
  var nb = document.querySelector('[data-notes]');
  if (nb) nb.addEventListener('click', function () { setNotes(root.classList.contains('no-notes')); });
})();

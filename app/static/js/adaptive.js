/* ============================================================
   XYZ EVENTS
   1) Phân lớp thiết bị: tier-phone / tier-tablet / tier-desktop (AWD)
   2) Theme sáng/tối/tự động + đồng bộ Bootstrap (data-bs-theme)
   3) Menu mobile tự đóng sau khi chọn mục
   ============================================================ */
(function () {
  'use strict';
  var root = document.documentElement;
  var KEY = 'xyz-events-theme';

  /* --- 1. Adaptive tiers --- */
  var mqPhone = window.matchMedia('(max-width: 575.98px)');
  var mqTablet = window.matchMedia('(min-width: 576px) and (max-width: 991.98px)');

  function applyTier() {
    root.classList.remove('tier-phone', 'tier-tablet', 'tier-desktop');
    if (mqPhone.matches) root.classList.add('tier-phone');
    else if (mqTablet.matches) root.classList.add('tier-tablet');
    else root.classList.add('tier-desktop');
    root.dataset.tier = root.classList.contains('tier-phone') ? 'phone'
      : root.classList.contains('tier-tablet') ? 'tablet' : 'desktop';
  }

  function on(mq, fn) {
    if (mq.addEventListener) mq.addEventListener('change', fn);
    else if (mq.addListener) mq.addListener(fn); // Safari cũ
  }
  applyTier();
  on(mqPhone, applyTier);
  on(mqTablet, applyTier);

  /* --- 2. Theme sáng / tối / tự động --- */
  var sysDark = window.matchMedia('(prefers-color-scheme: dark)');
  var btn = document.getElementById('themeToggle');
  var icon = document.getElementById('themeIcon');
  var ICONS = { auto: 'bi-circle-half', dark: 'bi-moon-stars-fill', light: 'bi-sun-fill' };
  var LABELS = { auto: 'tự động', dark: 'tối', light: 'sáng' };

  function getMode() {
    try { return localStorage.getItem(KEY) || 'auto'; } catch (e) { return 'auto'; }
  }

  function applyTheme(mode) {
    var dark = mode === 'dark' || (mode === 'auto' && sysDark.matches);
    root.setAttribute('data-theme', dark ? 'dark' : 'light');
    root.setAttribute('data-bs-theme', dark ? 'dark' : 'light');
    if (icon) icon.className = 'bi ' + ICONS[mode];
    if (btn) btn.title = 'Giao diện: ' + LABELS[mode] + ' (bấm để đổi)';
  }

  function cycle() {
    var cur = getMode();
    var next = cur === 'auto' ? 'dark' : (cur === 'dark' ? 'light' : 'auto');
    try { localStorage.setItem(KEY, next); } catch (e) { /* bộ nhớ riêng tư */ }
    applyTheme(next);
  }

  if (btn) btn.addEventListener('click', cycle);
  applyTheme(getMode());
  on(sysDark, function () { if (getMode() === 'auto') applyTheme('auto'); });

  /* --- 3. Menu mobile tự đóng --- */
  document.querySelectorAll('#mainNav .nav-link').forEach(function (a) {
    a.addEventListener('click', function () {
      var nav = document.getElementById('mainNav');
      if (nav && nav.classList.contains('show') && root.classList.contains('tier-phone')) {
        var inst = window.bootstrap && bootstrap.Collapse.getInstance(nav);
        if (inst) inst.hide();
      }
    });
  });
})();

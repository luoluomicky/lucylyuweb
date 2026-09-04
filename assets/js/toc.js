/* 长文右栏目录：给当前所在小节的链接加 .is-current。无目录的页面直接退出。 */
(function () {
  var rail = document.querySelector('.article-toc');
  if (!rail) return;
  var pairs = [];
  rail.querySelectorAll('a[href^="#"]').forEach(function (a) {
    var id = a.getAttribute('href').slice(1);
    var h = document.getElementById(id);
    if (!h) { try { h = document.getElementById(decodeURIComponent(id)); } catch (e) {} }
    if (h) pairs.push([a, h]);
  });
  if (!pairs.length) return;
  var current = null, ticking = false;
  function update() {
    ticking = false;
    var hit = null;
    for (var i = 0; i < pairs.length; i++) {
      if (pairs[i][1].getBoundingClientRect().top <= 120) hit = pairs[i][0];
    }
    if (hit === current) return;
    if (current) current.classList.remove('is-current');
    if (hit) hit.classList.add('is-current');
    current = hit;
  }
  function schedule() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  update();
})();

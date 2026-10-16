// Carousel 单篇页看卡器（2026-10-16）：箭头翻一张、进度条可点、键盘左右键、首尾箭头置灰
document.querySelectorAll(".card-viewer-wrap").forEach(wrap => {
  const viewer = wrap.querySelector(".card-viewer");
  const frames = [...viewer.querySelectorAll(".card-frame")];
  const prev = wrap.querySelector(".viewer-arrow-left");
  const next = wrap.querySelector(".viewer-arrow-right");
  const n = frames.length;
  const pad = i => String(i).padStart(2, "0");

  const bar = document.createElement("div");
  bar.className = "cv-bar";
  const ticks = document.createElement("div");
  ticks.className = "cv-ticks";
  const count = document.createElement("span");
  count.className = "cv-count";
  frames.forEach((_, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("aria-label", `第 ${i + 1} 张`);
    b.addEventListener("click", () => go(i));
    ticks.appendChild(b);
  });
  bar.append(ticks, count);
  wrap.after(bar);

  const current = () => viewer.clientWidth ? Math.round(viewer.scrollLeft / viewer.clientWidth) : 0;
  const go = i => viewer.scrollTo({ left: Math.max(0, Math.min(n - 1, i)) * viewer.clientWidth });
  const paint = () => {
    const i = current();
    [...ticks.children].forEach((b, j) => b.setAttribute("aria-current", j === i));
    count.textContent = `${pad(i + 1)} / ${pad(n)}`;
    prev.disabled = i === 0;
    next.disabled = i === n - 1;
  };

  prev.addEventListener("click", () => go(current() - 1));
  next.addEventListener("click", () => go(current() + 1));
  viewer.addEventListener("scroll", () => requestAnimationFrame(paint), { passive: true });
  document.addEventListener("keydown", e => {
    if (e.target.closest?.("input, textarea, select, [contenteditable]") || e.altKey || e.metaKey) return;
    if (e.key === "ArrowLeft") go(current() - 1);
    if (e.key === "ArrowRight") go(current() + 1);
  });
  window.addEventListener("resize", paint);
  window.addEventListener("load", paint);
  paint();
});

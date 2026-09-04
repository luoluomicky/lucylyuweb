#!/usr/bin/env python3
"""长文页导航：h2 锚点 + 目录 + 文末「接着读」。

用法（仓库根目录）：python3 tools/article-nav.py
可重复运行：块写在 <!-- toc --> / <!-- nextread --> 标记之间，每次整块重生成，
新文章上站后跑一遍，相邻文章的「接着读」会自动补上下一篇。

规则：
- 作用域 = 有 .article-body 的长文页（pilates/articles、work/chuhai、ai/*）
- h2 ≥ 3 才出目录；id 取自标题文字（已有 id 保留）
- 「接着读」= 同栏目按发布日期的上一篇（更早）/ 下一篇（更新）
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sitelib import LONGFORM, scan  # noqa: E402

H2 = re.compile(r"<h2([^>]*)>(.*?)</h2>", re.S)
TOC_BLOCK = re.compile(r"\n?<!-- toc:start -->.*?<!-- toc:end -->\n?", re.S)
NEXT_BLOCK = re.compile(r"\n?<!-- nextread:start -->.*?<!-- nextread:end -->\n?", re.S)
SCRIPT_TAG = '<script src="/assets/js/toc.js" defer></script>\n'
MIN_H2 = 3


def slugify(text, used):
    text = re.sub(r"<[^>]+>", "", text)
    slug = re.sub(r"[^\w]", "", text, flags=re.UNICODE).lower()[:32] or "section"
    base, n = slug, 2
    while slug in used:
        slug, n = f"{base}-{n}", n + 1
    used.add(slug)
    return slug


def ensure_ids(main_html):
    """给 main 内每个 h2 加稳定 id，返回 (html, [(id, text)])。"""
    used = set(re.findall(r'\sid="([^"]+)"', main_html))
    entries = []

    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        idm = re.search(r'\sid="([^"]+)"', attrs)
        if idm:
            hid = idm.group(1)
        else:
            hid = slugify(text, used)
            attrs = f' id="{hid}"' + attrs
        entries.append((hid, text))
        return f"<h2{attrs}>{inner}</h2>"

    return H2.sub(repl, main_html), entries


def toc_html(entries):
    items = "".join(f'<li><a href="#{hid}">{text}</a></li>' for hid, text in entries)
    return (
        "<!-- toc:start -->\n"
        '<aside class="article-toc" aria-label="目录"><div class="toc-inner">'
        f'<span class="toc-label">目录</span><ol>{items}</ol></div></aside>\n'
        f'<details class="article-toc-m"><summary>目录</summary><ol>{items}</ol></details>\n'
        "<!-- toc:end -->\n"
    )


def nextread_html(prev_pg, next_pg):
    lines = ['<section class="article-nextread" aria-label="接着读">', '<span class="nextread-label">接着读</span>']
    if prev_pg:
        lines.append(f'<p><span>上一篇</span><a href="{prev_pg.url}">{prev_pg.h1}</a></p>')
    if next_pg:
        lines.append(f'<p><span>下一篇</span><a href="{next_pg.url}">{next_pg.h1}</a></p>')
    lines.append("</section>")
    return "<!-- nextread:start -->\n" + "\n".join(lines) + "\n<!-- nextread:end -->\n"


def process(pg, prev_pg, next_pg):
    src = pg.html
    head, rest = src.split("<main", 1)
    main_part, tail = rest.split("</main>", 1)
    main_part = "<main" + main_part

    # 先清旧块，再按当前内容重生成
    main_part = TOC_BLOCK.sub("\n", main_part)
    main_part = NEXT_BLOCK.sub("\n", main_part)
    head = head.replace(SCRIPT_TAG, "")

    main_part, entries = ensure_ids(main_part)

    if len(entries) >= MIN_H2:
        open_tag = re.search(r'<div class="article-body">[ \t]*\n?', main_part)
        main_part = main_part[: open_tag.end()] + toc_html(entries) + main_part[open_tag.end() :]
        head = head.replace("</head>", SCRIPT_TAG + "</head>")

    if prev_pg or next_pg:
        main_part = main_part.rstrip() + "\n\n" + nextread_html(prev_pg, next_pg)

    out = head + main_part + "</main>" + tail
    changed = out != src
    if changed:
        pg.path.write_text(out, encoding="utf-8")
    return changed, len(entries)


def main():
    pages = [p for p in scan(LONGFORM)]
    by_sec = {}
    for p in pages:
        by_sec.setdefault(p.section, []).append(p)
    touched = toc_count = 0
    for sec, lst in by_sec.items():
        lst.sort(key=lambda p: (p.date, p.url))  # 旧 → 新
        for i, p in enumerate(lst):
            prev_pg = lst[i - 1] if i > 0 else None
            next_pg = lst[i + 1] if i + 1 < len(lst) else None
            changed, n = process(p, prev_pg, next_pg)
            touched += changed
            toc_count += n >= MIN_H2
            print(f"{'*' if changed else ' '} {p.url}  h2={n}  {p.date}  ←{prev_pg.url if prev_pg else '—'}  →{next_pg.url if next_pg else '—'}")
    print(f"\n{len(pages)} 长文页 · {toc_count} 页有目录 · 本次改写 {touched} 页")


if __name__ == "__main__":
    main()

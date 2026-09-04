"""站点页面扫描（tools/ 下两个脚本共用）。

只依赖标准库。页面是手写 HTML，这里用正则读取 <title> / <h1> /
meta description / datePublished，再统一解析出可排序的发布日期。
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lucylyu.life"

# 栏目 → glob。前三类是长文（有 .article-body），carousel 只进 RSS。
SECTIONS = {
    "pilates-articles": "pilates/articles/*/index.html",
    "chuhai": "work/chuhai/*/index.html",
    "ai": "ai/*/index.html",
    "carousel": "pilates/carousel/*/index.html",
}
LONGFORM = ("pilates-articles", "chuhai", "ai")

# 页面只写到月份（2026-07）的几篇，真实发布日取自 Obsidian 发布追踪表。
DATE_OVERRIDES = {
    "/pilates/articles/relax-cue/": "2026-08-05",
    "/pilates/articles/proprioception/": "2026-07-29",
    "/pilates/articles/pseudo-flexibility/": "2026-07-23",
}

TITLE_SUFFIX = re.compile(r"\s*·\s*(普拉提|工作论|AI思考)\s*·\s*Lucy Lyu\s*$")
TAG = re.compile(r"<[^>]+>")


class Page:
    def __init__(self, path, section):
        self.path = path
        self.section = section
        self.html = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).parent.as_posix()
        self.url = f"/{rel}/"
        self.link = SITE + self.url

        m = re.search(r"<title>(.*?)</title>", self.html, re.S)
        self.title = html.unescape(TITLE_SUFFIX.sub("", m.group(1).strip())) if m else self.url
        m = re.search(r"<h1[^>]*>(.*?)</h1>", self.html, re.S)
        self.h1 = html.unescape(TAG.sub("", m.group(1)).strip()) if m else self.title
        m = re.search(r'<meta name="description" content="([^"]*)"', self.html)
        self.description = html.unescape(m.group(1)) if m else self._first_paragraph()

        m = re.search(r'"datePublished":\s*"([^"]+)"', self.html) or re.search(
            r'<time datetime="([^"]+)"', self.html
        )
        if not m:  # 旧页只在元信息行写了 2026.07 这类月份
            m = re.search(r'class="article-meta">[^<]*?(\d{4})\.(\d{2})', self.html)
            self.date_raw = f"{m.group(1)}-{m.group(2)}" if m else ""
        else:
            self.date_raw = m.group(1)

        # Carousel 页：RSS 标题带系列名（页内 <title> 只有 #编号）
        m = re.search(r'<span class="series-tag">(.*?)</span>', self.html)
        if section == "carousel" and m:
            self.title = f"{html.unescape(m.group(1).strip())} · {self.h1}"

    def _first_paragraph(self):
        body = self.html.split('class="article-body"', 1)[-1]
        m = re.search(r"<p>(.*?)</p>", body, re.S)
        text = html.unescape(TAG.sub("", m.group(1))).strip() if m else ""
        return text[:200]

    def resolve_date(self, sitemap):
        """返回 YYYY-MM-DD。全日期直接用；只到月份的：覆盖表 → 同月的 sitemap
        lastmod（git 真实上站日）→ 该月 1 日。"""
        raw = self.date_raw
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            self.date = raw
        elif re.fullmatch(r"\d{4}-\d{2}", raw):
            lm = sitemap.get(self.url, "")
            if self.url in DATE_OVERRIDES:
                self.date = DATE_OVERRIDES[self.url]
            elif lm.startswith(raw):
                self.date = lm
            else:
                self.date = raw + "-01"
        else:
            self.date = sitemap.get(self.url, "1970-01-01")
        return self.date


def read_sitemap():
    s = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return {
        loc.replace(SITE, ""): lm
        for loc, lm in re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", s)
    }


def scan(sections=SECTIONS):
    sitemap = read_sitemap()
    pages = []
    for sec in sections:
        for p in sorted(ROOT.glob(SECTIONS[sec])):
            pg = Page(p, sec)
            if sec in LONGFORM and 'class="article-body"' not in pg.html:
                continue
            pg.resolve_date(sitemap)
            pages.append(pg)
    return pages

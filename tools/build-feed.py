#!/usr/bin/env python3
"""生成 /feed.xml（RSS 2.0，最新 30 条：长文 + 出海笔记 + Carousel）。

用法（仓库根目录）：python3 tools/build-feed.py
新页面上站后重跑即可；输出是确定性的（lastBuildDate 取最新一条的日期）。
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sitelib import ROOT, SITE, scan  # noqa: E402

LIMIT = 30
TZ = timezone(timedelta(hours=8))
CHANNEL = {
    "title": "Lucy Lyu",
    "link": SITE + "/",
    "description": "在身体与商业之间，寻找底层逻辑。",
    "language": "zh-CN",
}


def rfc822(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=TZ)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{days[d.weekday()]}, {d.day:02d} {months[d.month - 1]} {d.year} 00:00:00 +0800"


def main():
    pages = sorted(scan(), key=lambda p: (p.date, p.url), reverse=True)[:LIMIT]
    items = []
    for p in pages:
        items.append(
            "    <item>\n"
            f"      <title>{escape(p.title)}</title>\n"
            f"      <link>{p.link}</link>\n"
            f'      <guid isPermaLink="true">{p.link}</guid>\n'
            f"      <pubDate>{rfc822(p.date)}</pubDate>\n"
            f"      <description>{escape(p.description)}</description>\n"
            "    </item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{escape(CHANNEL['title'])}</title>\n"
        f"    <link>{CHANNEL['link']}</link>\n"
        f"    <description>{escape(CHANNEL['description'])}</description>\n"
        f"    <language>{CHANNEL['language']}</language>\n"
        f'    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>\n'
        f"    <lastBuildDate>{rfc822(pages[0].date)}</lastBuildDate>\n"
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )
    (ROOT / "feed.xml").write_text(xml, encoding="utf-8")
    for p in pages:
        print(p.date, p.section.ljust(16), p.title)
    print(f"\nfeed.xml 写入 {len(pages)} 条")


if __name__ == "__main__":
    main()

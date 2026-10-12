import json
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

cfg = json.load(open("config.json", encoding="utf-8"))
site = cfg["site_url"].rstrip("/")
ch = cfg["channel"]

def to_date(s):
    return datetime.strptime(s, "%Y-%m-%d").replace(hour=9, tzinfo=timezone.utc)

def feed_xml(title, desc, items, self_url):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
           f"<title>{escape(title)}</title>", f"<link>{escape(ch['link'])}</link>",
           f"<description>{escape(desc)}</description>", "<language>en</language>",
           f'<atom:link href="{escape(self_url)}" rel="self" type="application/rss+xml"/>']
    if items:
        out.append(f"<lastBuildDate>{format_datetime(to_date(items[0]['date']))}</lastBuildDate>")
    for i in items:
        out += ["<item>", f"<title>{escape(i['title'])}</title>", f"<link>{escape(i['link'])}</link>",
                f'<guid isPermaLink="false">{escape(i["set"] + ":" + i["title"])}</guid>',
                f"<pubDate>{format_datetime(to_date(i['date']))}</pubDate>",
                f"<description>{escape(i.get('summary', ''))}</description>", "</item>"]
    out += ["</channel>", "</rss>"]
    return "\n".join(out)

reports = sorted(cfg["reports"], key=lambda r: r["date"], reverse=True)
rows = []
for s in cfg["sets"]:
    items = [r for r in reports if r["set"] == s["folder"]]
    url = f"{site}/{s['folder']}.xml"
    open(f"{s['folder']}.xml", "w", encoding="utf-8").write(feed_xml(s["title"], s["description"], items, url))
    rows.append((s["title"], s["description"], url))

url = f"{site}/all.xml"
open("all.xml", "w", encoding="utf-8").write(feed_xml(ch["title"] + " - All Reports", ch["description"], reports, url))
rows.append(("All reports (combined)", "Everything from every set.", url))

li = "\n".join(f'<li><strong>{escape(t)}</strong><br>{escape(d)}<br><a href="{escape(u)}">{escape(u)}</a></li>' for t, d, u in rows)
open("index.html", "w", encoding="utf-8").write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(ch['title'])} - RSS Feeds</title>
<style>body{{font-family:system-ui,sans-serif;max-width:700px;margin:40px auto;padding:0 16px;line-height:1.5}}li{{margin-bottom:20px}}</style>
</head><body><h1>{escape(ch['title'])} - RSS Feeds</h1><p>{escape(ch['description'])}</p><ul>
{li}
</ul></body></html>""")
print("Built", len(rows), "feeds,", len(reports), "items")

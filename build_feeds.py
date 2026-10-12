import json, re, glob, os
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

cfg = json.load(open("config.json", encoding="utf-8"))
site = cfg["site_url"].rstrip("/")
ch = cfg["channel"]

def parse(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip('"\'')
        body = m.group(2)
    return meta, body

def load_items(folder):
    items = []
    for p in glob.glob(f"reports/{folder}/*.md"):
        meta, _ = parse(p)
        if "title" not in meta:
            continue
        try:
            d = datetime.strptime(meta.get("date", ""), "%Y-%m-%d").replace(hour=9, tzinfo=timezone.utc)
        except ValueError:
            d = datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc)
        items.append({
            "title": meta["title"],
            "link": meta.get("link") or site + "/",
            "summary": meta.get("summary", ""),
            "date": d,
            "set": folder,
        })
    return sorted(items, key=lambda i: i["date"], reverse=True)

def feed_xml(title, desc, items, self_url):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
           f"<title>{escape(title)}</title>", f"<link>{escape(ch['link'])}</link>",
           f"<description>{escape(desc)}</description>", "<language>en</language>",
           f'<atom:link href="{escape(self_url)}" rel="self" type="application/rss+xml"/>']
    if items:
        out.append(f"<lastBuildDate>{format_datetime(items[0]['date'])}</lastBuildDate>")
    for i in items:
        out += ["<item>", f"<title>{escape(i['title'])}</title>", f"<link>{escape(i['link'])}</link>",
                f'<guid isPermaLink="false">{escape(i["set"] + ":" + i["title"])}</guid>',
                f"<pubDate>{format_datetime(i['date'])}</pubDate>",
                f"<description>{escape(i['summary'])}</description>", "</item>"]
    out += ["</channel>", "</rss>"]
    return "\n".join(out)

os.makedirs("feeds", exist_ok=True)
all_items, rows = [], []
for s in cfg["sets"]:
    items = load_items(s["folder"])
    all_items += items
    url = f"{site}/feeds/{s['folder']}.xml"
    open(f"feeds/{s['folder']}.xml", "w", encoding="utf-8").write(feed_xml(s["title"], s["description"], items, url))
    rows.append((s["title"], s["description"], url))

all_items.sort(key=lambda i: i["date"], reverse=True)
url = f"{site}/feeds/all.xml"
open("feeds/all.xml", "w", encoding="utf-8").write(feed_xml(ch["title"] + " - All Reports", ch["description"], all_items, url))
rows.append(("All reports (combined)", "Everything from every set.", url))

li = "\n".join(f'<li><strong>{escape(t)}</strong><br>{escape(d)}<br><a href="{escape(u)}">{escape(u)}</a></li>' for t, d, u in rows)
open("index.html", "w", encoding="utf-8").write(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(ch['title'])} - RSS Feeds</title>
<style>body{{font-family:system-ui,sans-serif;max-width:700px;margin:40px auto;padding:0 16px;line-height:1.5}}li{{margin-bottom:20px}}</style>
</head><body><h1>{escape(ch['title'])} - RSS Feeds</h1><p>{escape(ch['description'])}</p><ul>
{li}
</ul></body></html>""")
print("Built", len(rows), "feeds,", len(all_items), "items")

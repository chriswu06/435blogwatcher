#!/usr/bin/env python3
"""Diff the CMSC435 course blog against state.json.

Usage:
  python3 blogwatch.py diff [blog.html]   # print new/changed entries as JSON
  python3 blogwatch.py commit [blog.html] # record current entry text in state.json

With no blog.html argument the page is downloaded from BLOG_URL.
"""
import html
import json
import re
import sys
import urllib.request

BLOG_URL = "https://seam.cs.umd.edu/purtilo/435/blog.html"
STATE = "state.json"


def fetch(path=None):
    if path:
        return open(path, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(BLOG_URL, headers={"User-Agent": "435blogwatcher"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse(page):
    """Return {anchor_date: plain_text} for every blog entry, newest first."""
    entries = {}
    for row in re.findall(r"<tr><td>(.*?)</td></tr>", page, re.S):
        m = re.search(r'id="(\d{4}-\d\d-\d\d)"', row)
        if not m:
            continue
        text = re.sub(r"<[^>]+>", " ", row)
        entries[m.group(1)] = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return entries


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "diff"
    entries = parse(fetch(sys.argv[2] if len(sys.argv) > 2 else None))
    if not entries:
        sys.exit("parsed zero entries -- page layout may have changed")
    state = json.load(open(STATE))
    seen = state["entries"]

    if cmd == "diff":
        out = {"new": [], "changed": []}
        for date, text in entries.items():
            if date not in seen:
                out["new"].append({"date": date, "text": text})
            elif seen[date] != text:
                out["changed"].append({"date": date, "old": seen[date], "new": text})
        print(json.dumps(out, indent=1))
    elif cmd == "commit":
        seen.update(entries)
        json.dump(state, open(STATE, "w"), indent=1)
        print(f"recorded {len(entries)} entries")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Minimal Google Tasks client for the watcher (stdlib only).

Credentials come from env vars GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.
All tasks live in a task list named "CMSC435" (created on first use).

Usage:
  python3 tasks.py list                                   # open + completed tasks as JSON
  python3 tasks.py add "<title>" <YYYY-MM-DD> "<notes>"   # prints created task JSON
  python3 tasks.py update <task_id> [--title T] [--due YYYY-MM-DD] [--notes N]
  python3 tasks.py delete <task_id>

The Tasks API stores only a due *date*; put any due time in the title/notes.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://tasks.googleapis.com/tasks/v1"
LIST_NAME = "CMSC435"


def token():
    data = urllib.parse.urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", data, timeout=30) as r:
        return json.load(r)["access_token"]


def call(tok, method, path, body=None, query=None):
    url = API + path + ("?" + urllib.parse.urlencode(query) if query else "")
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def tasklist_id(tok):
    for tl in call(tok, "GET", "/users/@me/lists").get("items", []):
        if tl["title"] == LIST_NAME:
            return tl["id"]
    return call(tok, "POST", "/users/@me/lists", {"title": LIST_NAME})["id"]


def due(date):
    return f"{date}T00:00:00.000Z"


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    tok = token()
    tl = tasklist_id(tok)
    cmd = args[0]
    if cmd == "list":
        items = call(tok, "GET", f"/lists/{tl}/tasks",
                     query={"showCompleted": "true", "showHidden": "true", "maxResults": 100})
        out = [{k: t.get(k) for k in ("id", "title", "due", "status", "notes")}
               for t in items.get("items", [])]
        print(json.dumps(out, indent=1))
    elif cmd == "add":
        title, date, notes = args[1], args[2], args[3] if len(args) > 3 else ""
        t = call(tok, "POST", f"/lists/{tl}/tasks", {"title": title, "due": due(date), "notes": notes})
        print(json.dumps({"id": t["id"], "title": t["title"], "due": t.get("due")}))
    elif cmd == "update":
        tid, patch, rest = args[1], {}, args[2:]
        for flag, val in zip(rest[::2], rest[1::2]):
            key = flag.lstrip("-")
            patch[key] = due(val) if key == "due" else val
        t = call(tok, "PATCH", f"/lists/{tl}/tasks/{tid}", patch)
        print(json.dumps({"id": t["id"], "title": t["title"], "due": t.get("due")}))
    elif cmd == "delete":
        call(tok, "DELETE", f"/lists/{tl}/tasks/{args[1]}")
        print("deleted")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

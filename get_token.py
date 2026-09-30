#!/usr/bin/env python3
"""One-time: get a Google Tasks refresh token for the watcher routine.

  python3 get_token.py path/to/client_secret.json [out.json]

Opens a browser for Google sign-in, catches the redirect on localhost, and prints
the client id/secret + refresh token to paste into the routine config. Stdlib only.
"""
import http.server
import json
import sys
import urllib.parse
import urllib.request
import webbrowser

SCOPE = "https://www.googleapis.com/auth/tasks"

cfg = json.load(open(sys.argv[1]))
cfg = cfg.get("installed") or cfg.get("web")
cid, secret = cfg["client_id"], cfg["client_secret"]

code = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Done - you can close this tab and go back to the terminal.")

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
redirect = f"http://127.0.0.1:{srv.server_port}"
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cid, "redirect_uri": redirect, "response_type": "code",
    "scope": SCOPE, "access_type": "offline", "prompt": "consent",
})
print("Opening browser for Google sign-in...\nIf it doesn't open, visit:\n" + url)
webbrowser.open(url)
while "code" not in code and "error" not in code:
    srv.handle_request()
if "error" in code:
    sys.exit("Authorization failed: " + code["error"])

data = urllib.parse.urlencode({
    "code": code["code"], "client_id": cid, "client_secret": secret,
    "redirect_uri": redirect, "grant_type": "authorization_code",
}).encode()
tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
if "refresh_token" not in tok:
    sys.exit("No refresh token returned: " + json.dumps(tok))

out = {"GOOGLE_CLIENT_ID": cid, "GOOGLE_CLIENT_SECRET": secret,
       "GOOGLE_REFRESH_TOKEN": tok["refresh_token"]}
dest = sys.argv[2] if len(sys.argv) > 2 else "google_tasks_creds.json"
json.dump(out, open(dest, "w"), indent=1)
print(f"\nSaved to {dest} (do NOT commit this file).")

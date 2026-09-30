# 435blogwatcher

A scheduled cloud routine checks the CMSC435 course blog every hour, from
7am to midnight ET. When there's a new post, it:

1. Pings Slack through an incoming webhook, so the phone gets a push notification.
2. Adds definite tasks to Google Tasks (list "CMSC435"), which show up in Google Calendar.
3. Asks yes/no in the Slack message about anything uncertain. Reply in the thread, and
   the next hourly run acts on your answer.

- `WATCHER.md`: what the agent does each run. Edit this to change its behavior.
- `blogwatch.py`: parses the blog into entries keyed by date and diffs them against state.
- `tasks.py`: minimal Google Tasks client. `get_token.py`: one-time OAuth to get a refresh token.
- `state.json`: entries already processed, pending questions, and tasks created. The
  routine commits changes to this file.

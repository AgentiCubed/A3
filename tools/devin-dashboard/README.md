# Devin Control Dashboard

A zero-dependency local dashboard for directing Devin to work on this repo.

## Features

- Lists open GitHub issues and pull requests for the repo, with one-click
  "Send to Devin" prompt prefill.
- Free-form task composer that dispatches new Devin sessions via the
  [Devin API](https://docs.devin.ai/api-reference).
- Shows recent Devin sessions with status and links to the live session,
  auto-refreshing every minute.

## Usage

Requires only Python 3 (stdlib). API keys stay server-side; the browser
never sees them.

```bash
export DEVIN_API_KEY=...   # from https://app.devin.ai/settings/api-keys
export GITHUB_TOKEN=...    # optional; raises rate limits / private repos
python3 tools/devin-dashboard/serve.py            # http://127.0.0.1:8321
python3 tools/devin-dashboard/serve.py --repo owner/name --port 9000
```

Open the printed URL, pick an issue/PR or write a task, and hit
**Dispatch to Devin**.

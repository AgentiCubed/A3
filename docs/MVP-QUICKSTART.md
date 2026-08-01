# A3 MVP Quickstart — clone to a working governed AI project

This is the shortest verified path from `git clone` to a running A3
instance that plans, executes, evaluates, remediates, and closes a real
project — first with the deterministic offline provider, then live on the
free GitHub Models tier.

What you get at the end:

- API (`http://localhost:8000`) and web UI (`http://localhost:3000`)
- One completed demo project with real artifacts (a markdown brief and a
  rendered chart), full audit trail, approval gate, evaluation rubric, and
  one automatic remediation — all inspectable in the UI
- A login of your own and the ability to create and run new projects
- A zero-cost live-model path (GitHub Models free tier)

## Prerequisites

- Docker Desktop (macOS/Windows) or docker + compose (Linux)
- git — or GitHub Desktop (no command-line git needed; see Path A0)

## Path A0 — first time with a terminal? (macOS, GitHub Desktop)

Same result as Path A, in smaller steps with no git commands.

1. **Install Docker Desktop.** Download from docker.com/products/docker-desktop,
   open the `.dmg`, drag Docker into Applications, open it, and wait for
   the whale icon in the menu bar to stop animating ("Docker Desktop is
   running").
2. **Clone with GitHub Desktop.** File → Clone Repository →
   `AgentiCubed/A3` → Clone. Note the Local Path it shows (default:
   `~/Documents/GitHub/A3`).
3. **Open Terminal** (Cmd+Space, type `Terminal`, Enter) and go to the
   repo folder — type this and press Enter:

   ```bash
   cd ~/Documents/GitHub/A3
   ```

   (If GitHub Desktop showed a different Local Path, use that instead.)
4. **Create your settings file** — two commands, one at a time:

   ```bash
   cp .env.example .env
   sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=$(openssl rand -hex 32)/" .env
   ```

   The first copies the example settings; the second replaces the
   placeholder signing key with a freshly generated random one.
5. **Start everything:**

   ```bash
   docker compose up -d --build
   ```

   The first run downloads and builds for several minutes. Success looks
   like a list of services each ending in `Started` or `Healthy`.
6. **Create the demo project and your login** (use any real-looking
   email — no mail is sent; reserved endings like `.local` are rejected):

   ```bash
   docker compose exec api python -m app.seed.demo --email you@example.com
   ```

   Success ends with `Tasks: 2/2 completed` and a closeout report.
7. **Log in.** Browser → http://localhost:3000/login — the email from
   step 6, password `demo-password-123`. Open the demo project and click
   through the plan, tasks, evaluations, and the two artifacts.
8. **Stop / restart later:** `docker compose stop` pauses it;
   `docker compose up -d` brings it back. Your data persists between
   restarts.

Then continue with "Go live on free models" below (that part is also
command-free except editing `.env`).

## Path A — Docker (recommended, ~10 minutes)

```bash
git clone https://github.com/AgentiCubed/A3.git
cd A3
cp .env.example .env
```

Edit `.env` and set `SECRET_KEY` to any random string of 32+ characters.
Everything else works as-is for local use.

```bash
docker compose up -d --build
```

First build takes a few minutes. Then seed the demo (use a real-looking
email — reserved domains like `.local` are rejected by validation):

```bash
docker compose exec api python -m app.seed.demo --email you@example.com
```

This prints a closeout report ending in `Tasks: 2/2 completed`. Now open
**http://localhost:3000/login** and sign in:

- **Email:** the address you passed above
- **Password:** `demo-password-123`

You'll see the completed project "Governed market brief: Widget X regional
demand" — open it to inspect the plan, the approval record, both task
executions, the evaluation that failed once and was automatically
remediated, and the two artifacts.

To run something of your own: create a new project from the dashboard,
generate a plan, approve it, and start it. With the default `mock`
provider this is deterministic and offline — the orchestration, approvals,
permissions, artifacts, and audit records are all real; only the model
text is canned.

## Go live on free models (~5 minutes more)

The `github_models` provider calls the GitHub Models free tier — no paid
API keys.

1. Create a GitHub fine-grained personal access token: github.com →
   Settings → Developer settings → Fine-grained tokens → Generate new
   token → Repository access: **Public repositories** → Account
   permissions: **Models: Read-only** → Generate. Copy the
   `github_pat_...` value.
2. Add it to `.env`:

   ```
   GITHUB_MODELS_TOKEN=github_pat_XXXXXXXX
   ```

3. Recreate the containers so they pick up the new variable:

   ```bash
   docker compose up -d
   ```

4. In the UI (or via the API), create your planner/executor/evaluator
   agents with:
   - **provider:** `github_models`
   - **model:** `openai/gpt-4.1` (the default), or any ID from
     github.com/marketplace/models — e.g. `openai/gpt-4o-mini` (fast),
     `deepseek/DeepSeek-R1` (reasoning)
   - the token is resolved by reference from `GITHUB_MODELS_TOKEN`; the
     secret value never enters the database, logs, or audit records.

Free-tier note: GitHub Models enforces per-model daily request and token
caps. If a task fails with a rate-limit error, use a smaller model
(`openai/gpt-4o-mini`) or wait for the window to reset. The nightly
`live-provider-smoke` CI workflow proves this path stays green at zero
cost.

## Path B — no Docker (verified fallback)

Needs local PostgreSQL 16, Redis, Python 3.11, Node 22.

```bash
# infra
pg_ctlcluster 16 main start          # or however you run postgres
sudo -u postgres psql -c "CREATE USER agenticubed WITH PASSWORD 'agenticubed' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE agenticubed OWNER agenticubed;"
redis-server --daemonize yes

# backend (from repo root)
cp .env.example .env                  # then set SECRET_KEY; point hosts at 127.0.0.1
cd backend
python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"
export $(grep -vE "^#|^$" ../.env | xargs) \
  POSTGRES_HOST=127.0.0.1 \
  DATABASE_URL="postgresql+asyncpg://agenticubed:agenticubed@127.0.0.1:5432/agenticubed" \
  DATABASE_URL_SYNC="postgresql+psycopg://agenticubed:agenticubed@127.0.0.1:5432/agenticubed" \
  REDIS_URL=redis://127.0.0.1:6379/0
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed.demo --email you@example.com
.venv/bin/uvicorn app.main:app --port 8000 &

# frontend
cd ../frontend && npm ci
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

With the `.env.example` defaults (`WORKFLOW_ENGINE_BACKEND=inline`,
`EVENT_BUS_BACKEND=memory`) no Celery worker is required; the Docker
compose stack switches these to `celery`/`redis` and runs the worker
container for you.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `value is not a valid email address` on seed/register | Use a real-looking domain (`.local`, `.test` etc. are rejected) |
| `governed scheduler did not complete the approved demo graph` | You're on a build older than the seed's inline-mode fix — update (`git pull`), `docker compose down -v && docker compose up -d --build`, and rerun the seed; or run the seed with `-e WORKFLOW_ENGINE_BACKEND=inline -e EVENT_BUS_BACKEND=memory` after `docker compose exec` |
| Seed fails with `email address is already registered` | That email already has an account from a previous seed run — pass a different `--email`, or reset with `docker compose down -v && docker compose up -d` first |
| Ports 3000/8000/5432/6379 already bound | Stop the conflicting service or change the published port in `docker-compose.yml` |
| Login fails after seeding | The seed's password is exactly `demo-password-123`; the email must match the `--email` you passed |
| Live task fails with 401/403 | Token missing `models: read` permission, or `GITHUB_MODELS_TOKEN` not present in the container env (rerun `docker compose up -d`) |
| Live task fails with 429 | Free-tier daily cap hit — smaller model or wait |
| `/readyz` red | `docker compose ps` — db/redis unhealthy; check `docker compose logs api` |

## What this MVP deliberately is not

The Agentic³ governance runtime (Phase 1+ of
[`agentic3/IMPLEMENTATION-BLUEPRINT.md`](agentic3/IMPLEMENTATION-BLUEPRINT.md)
— the append-only runtime event ledger and the machinery above it) is
specified and accepted (DR-0005) but not yet implemented. The MVP is the
shipped platform loop: governed plan → approve → execute → evaluate →
remediate → accept, with live or mock models. Iterate from here.

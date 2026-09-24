---
name: local-dev
description: Bring the llm-tuna dev stack (Postgres + FastAPI backend + Next.js frontend) up in the sandbox and verify it.
recorded: 2026-09-24
---

# Local dev — llm-tuna

Validated run: dev_stack_healthy true, snapshot `5nzf7uvg7x2wu61egncu:default` (2026-09-24T19:14:52Z).

## 1. Postgres

The repo ships **no** `docker-compose.yml` (gitignored) and Docker is unavailable in the sandbox; install and run Postgres natively:

```bash
sudo apt-get update && sudo apt-get install -y postgresql   # v17 on Debian trixie
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'finetune';"
sudo -u postgres psql -c "CREATE USER finetune WITH PASSWORD 'finetune' CREATEDB;"   # skip if exists
sudo -u postgres createdb -O finetune finetune_db
```

Matches the backend's default `DATABASE_URL=postgresql://finetune:finetune@localhost:5432/finetune_db` (fallback in `backend/app/database.py`). No env file needed. Verify: `PGPASSWORD=finetune psql -h localhost -U finetune -d finetune_db -c 'SELECT 1;'`.

## 2. Backend (Python 3.11 — not system 3.13)

torch 2.1.1 has no Python 3.13 wheels; system Python is 3.13. Use uv:

```bash
export PATH="$HOME/.local/bin:$PATH"   # uv at ~/.local/bin
curl -LsSf https://astral.sh/uv/install.sh | sh   # if uv missing
cd backend
uv python install 3.11 && uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python torch==2.1.1 --index-url https://download.pytorch.org/whl/cpu  # CPU wheel, avoids CUDA deps
uv pip install --python .venv/bin/python -r requirements.txt 'numpy<2'  # numpy>=2 breaks torch 2.1.1
```

Run detached (a foreground nohup start can outlive/kill the tool stream — background it and poll):

```bash
cd backend && (nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &) 
curl -s http://127.0.0.1:8000/health   # {"status":"healthy"}; port 8000 confirmed from uvicorn banner
```

Startup runs `init_db()` (`create_all`) — tables `datasets`, `training_jobs`, `evaluations`, `user_ratings` appear automatically; no migration step.

## 3. Frontend

npm (no lockfile committed):

```bash
cd frontend && npm install
(nohup env NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev > /tmp/frontend.log 2>&1 &)
curl -s -o /dev/null -w '%{http_code}' http://localhost:3000   # 200; "Ready in ..." in /tmp/frontend.log
```

## 4. Verify primary flow (dataset CRUD — the core user journey)

```bash
printf '{"prompt":"Summarize: ...","completion":"..."}\n' > /tmp/sample.jsonl   # 1+ lines, prompt+completion fields
curl -s -X POST http://127.0.0.1:8000/api/datasets -F "file=@/tmp/sample.jsonl"   # returns id + validation_report
curl -s http://127.0.0.1:8000/api/datasets | head -c 200
curl -s -X DELETE http://127.0.0.1:8000/api/datasets/<id> -w '%{http_code}'       # 204
```

Also: `GET /` and `GET /datasets` on :3000 return 200 with rendered content; `cd frontend && ./node_modules/.bin/tsc --noEmit` is clean.

## Gotchas learned

- `npm run lint` (`next lint`) hangs: no `.eslintrc` committed, it prompts interactively. Use `tsc --noEmit` as the type gate.
- Pin `numpy<2` after installing requirements.
- No unit tests exist in the repo; training/eval/inference flows require the ~16 GB `meta-llama/Llama-3.1-8B` download — skip in sandbox verification, CRUD + health + page render are the verification bar.
- Long commands: background with `(... &)` and poll — a foreground wait can hit the tool timeout.

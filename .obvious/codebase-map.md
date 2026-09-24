# codebase-map.md — llm-tuna

Folder-level map (depth 2). Generated 2026-09-24.

| Path | What it is | Key files |
|---|---|---|
| `backend/` | FastAPI service (port 8000) | `requirements.txt`, `Dockerfile` (python:3.11-slim, uvicorn CMD) |
| `backend/app/` | API application core | `main.py` (FastAPI app, CORS, startup `init_db()`), `database.py` (engine/session from `DATABASE_URL`), `models.py` (SQLAlchemy models: Dataset, TrainingJob, Evaluation, UserRating), `schemas.py` (Pydantic schemas) |
| `backend/app/routers/` | REST endpoints | `datasets.py` (upload/list/get/delete), `training.py` (start/status/cancel), `evaluation.py` (run/results/rate), `inference.py` (generate) |
| `backend/app/ml/` | ML logic | `data_validator.py` (JSONL validation, tiktoken lengths), `trainer.py` (LoRA fine-tune via peft/transformers), `evaluator.py` (base vs tuned comparison), `inference.py` (model loading + generation, in-memory cache) |
| `backend/datasets/` | Uploaded JSONL files (runtime, gitignored contents) | created at runtime |
| `frontend/` | Next.js 14 app (port 3000) | `package.json` (npm), `next.config.js`, `tailwind.config.js`, `Dockerfile` (node:20-alpine) |
| `frontend/app/` | App Router pages | `page.tsx` (dashboard), `datasets/page.tsx`, `training/[id]/page.tsx`, `evaluation/[id]/page.tsx`, `layout.tsx`, `globals.css`, `api/training/route.ts` (Next route handler) |
| `frontend/components/` | UI components | `DatasetUpload.tsx` (drag-drop), `TrainingProgress.tsx` (polling + recharts), `ModelComparison.tsx`, `MetricsCard.tsx` |
| `frontend/lib/` | Client API layer | `api.ts` (axios → `NEXT_PUBLIC_API_URL`, default localhost:8000) |

Cross-cutting flows: upload → validate → `datasets` table; train → background LoRA job → `training_jobs`; evaluate → `evaluations` + `user_ratings`; inference → POST `/api/inference` with a trained `model_id`.

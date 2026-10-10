
# ColdRescue - Local Development Setup

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.12+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| npm | 9+ | (bundled with Node) |

---

## 1. Clone and enter the project

```bash
cd ColdRescue
```

## 2. Python backend setup

```powershell
# Create virtual environment
py -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## 3. Environment configuration

```powershell
# Copy and edit env file
copy .env.example .env
# Edit .env as needed
```

Keep `AWS_INTEGRATIONS_ENABLED=False` for local development unless AWS integration has been explicitly configured and approved.

## 4. Run the backend

```powershell
.\.venv\Scripts\uvicorn.exe backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/api/docs
- Health: http://localhost:8000/api/v1/health

## 5. Run the simulator

```powershell
# List available scenarios
py -m simulator.engine --list-scenarios

# Run a scenario (reproducible with --seed)
py -m simulator.engine --scenario REEFER_UNIT_FAILURE --seed 42
py -m simulator.engine --scenario WAREHOUSE_GRID_OUTAGE --seed 0
py -m simulator.engine --scenario BACKUP_POWER_DEPLETED
```

## 6. Run the backend tests

```powershell
.\.venv\Scripts\pytest.exe backend\tests\ tests\ -v
```

Expected: **129 passed** (latest verified local run; the count may change as tests are added).

## 7. Frontend setup

Open a separate terminal from the project root, then run:

```powershell
cd frontend
npm install
npm run dev       # dev server at http://localhost:5173
npm test          # run Vitest test suite
npm run build     # production build
```

## 8. Regenerate fixture files

Run from the project root:

```powershell
py scripts\generate_fixtures.py
```

**Note:** This script regenerates fixture JSON files and may overwrite existing fixtures. Do not run it if you need to preserve manual changes to those files.

---

## Directory Quick Reference

```text
ColdRescue/
|-- backend/              Python FastAPI backend
|   |-- api/              HTTP route handlers
|   |-- common/           Shared utilities (UUID, datetime helpers)
|   |-- config/           Settings and logging
|   |-- middleware/       Error handler middleware
|   |-- models/           Domain models
|   |-- policies/         Safety policies
|   |-- schemas/          Pydantic schemas and event contracts
|   |-- services/         Application services
|   `-- tests/            Backend pytest suite
|-- frontend/             React + TypeScript + Vite UI
|-- simulator/             Power-failure simulator
|-- infrastructure/        AWS CDK infrastructure definitions
|-- ml/
|   |-- dataset/           Dataset foundation
|   |-- training/          Training foundation
|   |-- inference/         Inference foundation
|   `-- evaluation/        Evaluation foundation
|-- tests/                 Root-level test suite
|-- data/fixtures/          JSON schema fixtures
|-- docs/                   Project documentation
|-- scripts/                Utility scripts
|-- .env.example            Environment configuration template
|-- requirements.txt        Python dependencies
`-- README.md               Project overview
```

## Important M0 notes

- Run backend tests before considering M0 complete.
- The documented test count is a snapshot, not a permanent guarantee.
- AWS CDK synthesis does not deploy resources to AWS.
- AWS integrations must remain disabled by default during local development.
- Docker configuration and Docker build verification are separate acceptance checks.
- Do not mark M0 complete until the full M0 acceptance checklist passes.

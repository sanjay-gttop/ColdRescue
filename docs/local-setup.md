# ColdRescue — Local Development Setup

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

## 4. Run the backend

```powershell
.\.venv\Scripts\uvicorn.exe backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/api/docs
- Health:   http://localhost:8000/api/v1/health

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

Expected: **70 passed**

## 7. Frontend setup

```powershell
cd frontend
npm install
npm run dev       # dev server at http://localhost:5173
npm test          # run Vitest test suite
npm run build     # production build
```

## 8. Regenerate fixture files

```powershell
py scripts\generate_fixtures.py
```

---

## Directory Quick Reference

```
ColdRescue/
├── backend/           Python FastAPI backend
│   ├── api/           HTTP route handlers
│   ├── common/        Shared utilities (UUID, datetime helpers)
│   ├── config/        Settings (Pydantic BaseSettings) + logging
│   ├── middleware/     Error handler middleware
│   ├── schemas/       Pydantic event schemas (M0 contracts)
│   └── tests/         Backend pytest suite
├── simulator/         M2 power-failure simulator
│   ├── enums.py       IncidentType, PowerState, ReceiverCategory
│   ├── models.py      CargoProfile, ReceiverProfile, SimulatedIncident
│   ├── thermal.py     Newton-type thermal model (estimates only)
│   ├── state_machine.py  Power state transitions + event emission
│   ├── scenario.py    Deterministic scenario factory
│   └── engine.py      Main orchestrator + CLI entry point
├── frontend/          React 18 + TypeScript + Vite UI (M1)
├── tests/             Root-level simulator pytest suite
├── data/fixtures/     JSON fixtures for all 8 schema types
├── docs/              Documentation
└── scripts/           Utility scripts (fixture generation, etc.)
```

# Codebase Overview

This repository is a monorepo. It does not have one global install command.
You need to choose the subproject that matches your goal.

## Recommended Starting Points

- `generation_two/`: Python GUI alpha mining system for WorldQuant Brain.
- `generation_one/naive-ollama/`: Dockerized Ollama-based alpha miner with dashboard.
- `polymarket/`: Python prediction-market research and execution framework.
- `tradr-platform/`: Next.js + NestJS trading game platform.

## Monorepo Structure

### 1. Generation Two

Path: `generation_two/`

Purpose:
- Main Python application for WorldQuant alpha mining.
- Modular architecture with GUI, generation, simulation, evolution, storage, and Ollama integration.

Important files:
- `generation_two/README.md`
- `generation_two/DOCUMENTATION.md`
- `generation_two/gui/run_gui.py`
- `generation_two/gui/main_window.py`
- `generation_two/__init__.py`

Core flow:
1. `gui/run_gui.py` locates credentials and launches the GUI.
2. `gui/main_window.py` authenticates the user.
3. The GUI initializes `EnhancedTemplateGeneratorV3` and related services.
4. Mining, simulation, storage, and evolution are handled by modular packages under `core/`, `evolution/`, `storage/`, and `ollama/`.

Modules:
- `core/`: generation, validation, simulation, mining, config
- `evolution/`: self-optimization and alpha evolution
- `storage/`: backtest storage and historical analysis
- `ollama/`: local model integration
- `gui/`: Tkinter desktop interface

Install:

```powershell
cd generation_two
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python gui\run_gui.py
```

Credentials:
- Put `credential.txt` either in `generation_two/` or repo root.
- Format:

```json
["your.email@worldquant.com", "your_password"]
```

Optional Ollama:

```powershell
ollama pull qwen2.5-coder:1.5b
ollama serve
```

### 2. Naive-Ollama

Path: `generation_one/naive-ollama/`

Purpose:
- Docker-based alpha generation and orchestration around a local Ollama model.
- Includes a Flask dashboard and service composition for continuous mining.

Important files:
- `generation_one/naive-ollama/README.md`
- `generation_one/naive-ollama/docker-compose.gpu.yml`
- `generation_one/naive-ollama/alpha_orchestrator.py`
- `generation_one/naive-ollama/web_dashboard.py`

Core flow:
1. Docker starts Ollama-backed miner containers.
2. `alpha_orchestrator.py` schedules generation/mining/submission.
3. `web_dashboard.py` exposes monitoring on port 5000.

Install:

```powershell
cd generation_one\naive-ollama
Copy-Item ..\..\credential.example.txt .\credential.txt
docker compose -f docker-compose.gpu.yml up -d
```

Dashboard URLs:
- `http://localhost:5000`
- `http://localhost:3000`
- `http://localhost:11434`

Requirements:
- Docker Desktop
- Optional NVIDIA GPU + NVIDIA Container Toolkit for GPU compose file

Important note:
- The root `README.md` still refers to `naive-ollama/` at repo root.
- The actual directory is `generation_one/naive-ollama/`.

### 3. Polymarket

Path: `polymarket/`

Purpose:
- Modular research, backtest, risk, and execution pipeline for prediction markets.

Important files:
- `polymarket/README.md`
- `polymarket/pyproject.toml`
- `polymarket/scripts/run_research.py`
- `polymarket/scripts/run_e2e.py`
- `polymarket/scripts/run_full_cycle.py`
- `polymarket/scripts/run_dashboard.py`
- `polymarket/polymarket_core/cycle/full_cycle_runner.py`
- `polymarket/polymarket_core/web/dashboard.py`

Core flow:
1. Research pipeline loads market data and scores opportunities.
2. Backtest and risk gating decide whether execution is allowed.
3. Execution and artifacts are stored under `artifacts/`.
4. Flask dashboard runs on port 5080.

Install:

```powershell
cd polymarket
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e . pytest
python -m scripts.run_dashboard
```

Optional commands:

```powershell
python -m scripts.run_research
python -m scripts.run_e2e
python -m scripts.run_full_cycle --mode paper --auto-execute
```

Credentials:
- Use environment variables or `polymarket/credential.txt`.
- Live mode additionally needs signing credentials.

### 4. Tradr Platform

Path: `tradr-platform/`

Purpose:
- Separate TypeScript application for a game-like trading platform.
- Split into backend, frontend, and a PDaC DSL package.

Important files:
- `tradr-platform/SETUP.md`
- `tradr-platform/README.md`
- `tradr-platform/backend/package.json`
- `tradr-platform/frontend/package.json`

Architecture:
- `backend/`: NestJS + Prisma + PostgreSQL
- `frontend/`: Next.js 14 app
- `pdac/`: Product Design as Code tooling

Install:

Backend:

```powershell
cd tradr-platform\backend
npm install
```

Create `backend/.env`:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/tradr_platform"
PORT=3001
FRONTEND_URL=http://localhost:3000
JWT_SECRET=change-this
```

Then:

```powershell
npx prisma generate
npx prisma migrate dev --name init
npm run start:dev
```

Frontend:

```powershell
cd ..\frontend
npm install
npm run dev
```

### 5. Historical / Experimental Areas

These directories look like older or parallel experiments rather than the main recommended entry:

- `stone_age/`
- `mini-quant/`
- `generation_one/consultant-*`
- `generation_one/agent-*`
- `paper/`, `paper-zh/`

Use them only if you are targeting a specific legacy workflow.

## What To Install First

Choose one:

- Want the main desktop miner: install `generation_two/`.
- Want local Ollama + Docker automation: install `generation_one/naive-ollama/`.
- Want prediction-market research tools: install `polymarket/`.
- Want the trading game platform: install `tradr-platform/`.

If you are unsure, start with `generation_two/`. It is the cleanest entry point for the WorldQuant mining workflow in this repository.

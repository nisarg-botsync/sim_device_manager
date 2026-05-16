# SimDevice Manager

Industrial protocol simulation platform. Django REST backend + React frontend.
Users add simulated devices (Modbus, EthernetIP), configure registers/tags, and start/stop them individually. Each device runs as an isolated subprocess on its own port.

## Tech Stack
- **Backend:** Python 3.11+, Django 5.x, Django REST Framework
- **Package manager:** uv (all Python deps managed via pyproject.toml, NOT pip or requirements.txt)
- **Frontend:** React 18 + TypeScript, Vite, Tailwind CSS
- **Protocols:** pymodbus (Modbus TCP), cpppo (EthernetIP/CIP)
- **DB:** SQLite for dev, PostgreSQL for prod
- **Process management:** Python subprocess (multiprocessing) managed by Django

## Project Structure
```
sim-device-manager/
├── pyproject.toml        # All Python deps, ruff config, pytest config
├── uv.lock               # Locked dependency versions (committed to git)
├── .python-version       # Pins Python 3.11 for uv
├── backend/              # Django project
│   ├── core/             # Django project settings, urls, wsgi
│   ├── devices/          # Device CRUD app (models, views, serializers)
│   └── simulator/        # Process manager, protocol runners
├── frontend/             # React app (Vite + TypeScript)
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Page-level components
│       ├── hooks/        # Custom React hooks
│       ├── api/          # API client functions
│       └── types/        # TypeScript type definitions
├── .claude/              # Claude Code config
└── CLAUDE.md
```

## Commands
- Install deps: `uv sync` (creates .venv automatically, installs from uv.lock)
- Add a package: `uv add <package>` (updates pyproject.toml + uv.lock)
- Add a dev package: `uv add --group dev <package>`
- Remove a package: `uv remove <package>`
- Backend: `uv run python backend/manage.py runserver`
- Frontend: `cd frontend && npm run dev`
- Migrations: `uv run python backend/manage.py makemigrations && uv run python backend/manage.py migrate`
- Tests: `uv run pytest`
- Lint backend: `uv run ruff check backend/`
- Format backend: `uv run ruff format backend/`
- Lint frontend: `cd frontend && npm run lint`
- NEVER use pip, pip install, or requirements.txt — always use uv

## Architecture Decisions

### Device-to-Server Mapping
Each device gets its own server subprocess on a dedicated port.
- Modbus port range: 5020–5099
- EthernetIP port range: 44818–44899
- Django allocates the next available port from the range when a device is created.
- PID is stored in the Device model when running.
- Health check: periodic ping to verify subprocess is alive.

### Device Model
```
Device
├── id (UUID)
├── name (str, unique)
├── protocol (choices: modbus | ethernetip)
├── port (int, auto-assigned from pool)
├── status (choices: stopped | starting | running | error)
├── pid (int, nullable — OS process ID when running)
├── config (JSONField — protocol-specific config)
│   ├── Modbus: { unit_id, registers: [{address, value, type}] }
│   └── EthernetIP: { tags: [{name, type, value}] }
├── created_at
└── updated_at
```

### API Endpoints
```
GET    /api/devices/              # List all devices
POST   /api/devices/              # Create device
GET    /api/devices/{id}/         # Get device detail
PUT    /api/devices/{id}/         # Update device
DELETE /api/devices/{id}/         # Delete device (must be stopped)
POST   /api/devices/{id}/start/   # Start simulation
POST   /api/devices/{id}/stop/    # Stop simulation
GET    /api/devices/{id}/status/  # Health check
GET    /api/ports/available/      # Get next available port per protocol
```

## Code Style
- Python: ruff for linting/formatting, 4-space indent, type hints on all functions
- TypeScript: strict mode, no `any`, prefer interfaces over types
- React: functional components only, custom hooks for logic
- Django: fat models, thin views — business logic in model methods or services
- All API responses follow: `{ "data": ..., "error": null }` or `{ "data": null, "error": "message" }`

## Important Rules
- NEVER start a device that is already running
- ALWAYS kill subprocess before deleting a device
- Port assignment must be atomic (avoid race conditions)
- Config JSONField must be validated against protocol schema before save
- Frontend must poll /status/ every 5s for running devices
- Git: conventional commits (feat:, fix:, refactor:, docs:)

# SimDevice Manager

Industrial protocol simulation platform. Add, configure, and run simulated Modbus and EthernetIP devices from a web dashboard.

## Prerequisites

- **uv** — install from [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Node.js 18+** — for the React frontend

## Quick Start

### Backend
```bash
# Install all Python dependencies (creates .venv automatically)
uv sync

# Run migrations
uv run python backend/manage.py migrate

# Start the dev server
uv run python backend/manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Adding dependencies
```bash
# Add a production dependency
uv add <package-name>

# Add a dev-only dependency
uv add --group dev <package-name>

# Remove a dependency
uv remove <package-name>
```

### Using Claude Code
```bash
cd sim-device-manager
claude
# Then run: /plan-project to see the full implementation plan
```

## Architecture

Each simulated device runs as an isolated subprocess on its own port:

```
Django REST API (port 8000)
  ├── Device: "PLC-01" (Modbus, port 5020)  → pymodbus subprocess
  ├── Device: "PLC-02" (Modbus, port 5021)  → pymodbus subprocess
  └── Device: "EIP-01" (EthernetIP, port 44818) → cpppo subprocess
```

React frontend (port 5173) talks to Django API, polls device status every 5s.

## Supported Protocols
- **Modbus TCP** — configurable holding registers, coils, input registers
- **EthernetIP/CIP** — configurable tags with INT/REAL/DINT/BOOL types

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check backend/

# Format
uv run ruff format backend/
```

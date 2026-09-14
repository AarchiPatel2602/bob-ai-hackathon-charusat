# RouteWise AI — Source Code Architecture

All application source code for RouteWise AI 🚢 is structured under `src/`:

```
src/
├── backend/                  # FastAPI Application & Decision Engines
│   ├── app/
│   │   ├── api/              # REST Endpoints (auth, shipments, disruptions, fleet, alerts, ai, mcp)
│   │   ├── engines/          # 10 Decision Engines (risk, disruption, route, cold-chain, fleet, ai_service)
│   │   ├── models/           # SQLAlchemy Database Entities
│   │   ├── schemas/          # Pydantic Schemas & Request/Response Validators
│   │   ├── config.py         # App Configuration & Settings
│   │   ├── database.py       # DB Session & Engine
│   │   └── main.py           # FastAPI Entry Point
│   ├── tests/                # Automated Pytest Suite (19 unit & integration tests)
│   └── seed.py               # Database Seeder (50+ shipments, fleet, disruptions)
│
├── frontend/                 # React 19 + TypeScript + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── components/       # Layout, Modals, Shipment Map (Leaflet), Badges
│   │   ├── context/          # JWT Auth Context
│   │   ├── pages/            # Dashboard, Shipments, Disruptions, Fleet, Alerts, BobCopilotPage
│   │   ├── services/api.ts   # Typed REST Client
│   │   └── types/            # TypeScript Interfaces
│   ├── package.json          # Node Dependencies & Build Scripts
│   └── vite.config.ts        # Vite Bundler Configuration
│
├── mcp/                      # Model Context Protocol (MCP) Server
│   ├── routewise_mcp.py      # MCP Tool Provider & JSON-RPC Runner
│   └── __init__.py
│
├── app.py                    # Streamlit Companion Copilot Application
├── requirements.txt          # Unified Python Dependencies
├── .env.example              # Environment Configuration Template
└── README.md                 # This Documentation
```

## Running the Components

### 1. Backend REST API (FastAPI)
```bash
# From workspace root or inside src:
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
# Interactive Swagger Documentation: http://127.0.0.1:8000/docs
```

### 2. Frontend Command Center (React + Vite)
```bash
cd src/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
# Web Application: http://127.0.0.1:5173
```

### 3. Model Context Protocol (MCP) Server
```bash
python -m src.mcp.routewise_mcp --list-tools
```

### 4. Streamlit Companion Dashboard
```bash
streamlit run src/app.py
```

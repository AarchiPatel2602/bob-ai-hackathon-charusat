# Setup and Installation Guide: RouteWise AI

This comprehensive guide provides step-by-step instructions to set up, configure, test, and run RouteWise AI on your local machine.

---

## 1. Prerequisites & System Requirements

Before beginning installation, ensure your workstation meets the following minimum requirements:

- **Operating System:** Windows 10/11, macOS (12+), or modern Linux (Ubuntu 20.04+)
- **Python:** Version **3.9 or higher** (Python 3.10 or 3.11 recommended)
  - Verify with: `python --version` (or `python3 --version`)
- **Node.js & npm (Optional for React UI):** Node.js **18.x or higher**, npm **9.x or higher**
  - Verify with: `node --version` and `npm --version`
- **Git:** Version **2.30 or higher**
  - Verify with: `git --version`

---

## 2. Clone the Repository

Open your terminal or PowerShell and clone the official project repository:

```bash
git clone https://github.com/AarchiPatel2602/bob-ai-hackathon-charusat.git
cd bob-ai-hackathon-charusat
```

---

## 3. Environment Configuration

The repository includes pre-configured environment template files (`.env.example` and `src/.env.example`).

### Creating your `.env` File:

```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux Bash:
cp .env.example .env
```

### Environment Settings:
```ini
# Application Configuration
APP_NAME=RouteWise AI
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Connection (Defaults to local SQLite)
DATABASE_URL=sqlite:///./supplyguard.db

# IBM watsonx.ai Configuration (Optional - offline fallback is built-in)
# If you have IBM Cloud credentials, uncomment and provide them:
# WATSONX_APIKEY=your_ibm_cloud_api_key
# WATSONX_PROJECT_ID=your_watsonx_project_id
# WATSONX_URL=https://us-south.ml.cloud.ibm.com
# WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2
```

> **Note on IBM watsonx.ai Credentials:**
> You do **not** need an IBM Cloud API key to run and evaluate RouteWise AI! If credentials are left blank, the platform automatically activates its built-in **Deterministic Offline Reasoning Engine**, providing 100% grounded and factual supply chain recommendations without external network dependencies.

---

## 4. Option A: Streamlit Copilot Companion (Fastest Quickstart)

The fastest way to experience RouteWise AI is using the integrated Streamlit companion application in `src/app.py`. It requires only Python and delivers a complete, interactive logistics command center.

### Step 1: Create & Activate Virtual Environment

**Windows PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r src/requirements.txt
```

### Step 3: Launch the Application

```bash
streamlit run src/app.py
```

The terminal will display the local URL:
```
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Open `http://localhost:8501` in your browser to interact with the dashboard, view active disruptions, inspect cold-chain thermal graphs, and chat with the **IBM Bob Supply Chain Copilot**.

---

## 5. Option B: Full-Stack Enterprise Deployment (FastAPI + React)

For the full enterprise experience featuring the high-fidelity React 18 dashboard and asynchronous FastAPI REST & MCP gateway, follow these instructions to run both services.

### Terminal 1: Start the FastAPI Backend & MCP Gateway

Ensure your Python virtual environment is activated, then run:

```bash
python run_backend.py
```

*The backend server will start on `http://127.0.0.1:8000`.*
- **Interactive Swagger Docs:** Visit `http://127.0.0.1:8000/docs`
- **OpenAPI JSON Schema:** Visit `http://127.0.0.1:8000/openapi.json`
- **Health Check:** Visit `http://127.0.0.1:8000/health`

### Terminal 2: Start the React Frontend

In a new terminal window:

```bash
cd frontend
npm install
npm run dev
```

*The Vite development server will start on `http://localhost:5173`.*

Open `http://localhost:5173` in your browser to access the complete operations console.

---

## 6. Verifying the Model Context Protocol (MCP) Server

RouteWise AI provides a standardized MCP server allowing AI agents to interact with supply chain tools.

### Test MCP Tool Discovery:

**Using cURL:**
```bash
curl -X POST http://127.0.0.1:8000/api/mcp/tools
```

**Using PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/mcp/tools" -Method Post | ConvertTo-Json -Depth 4
```

### Test Invoking an MCP Tool:

```bash
curl -X POST http://127.0.0.1:8000/api/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_active_shipments", "arguments": {}}'
```

---

## 7. Running the Automated Test Suite

We maintain a rigorous automated test suite covering API endpoints, spatial engines, cold-chain telemetry, and conversational AI intents.

To execute all unit and integration tests:

```bash
pytest backend/tests -v
```

Expected output:
```
============================= test session starts =============================
backend/tests/test_ai_chat.py::test_ai_chat_at_risk_intent PASSED
backend/tests/test_ai_chat.py::test_ai_chat_urgent_intent PASSED
backend/tests/test_ai_chat.py::test_ai_chat_why_shipment_delayed PASSED
backend/tests/test_ai_chat.py::test_ai_chat_cold_chain_alert PASSED
backend/tests/test_ai_chat.py::test_ai_chat_reroute_options PASSED
backend/tests/test_ai_chat.py::test_ai_chat_idle_fleet PASSED
backend/tests/test_supplyguard.py::test_health_endpoint PASSED
...
============================= 19 passed in 0.85s =============================
```

---

## 8. Troubleshooting Guide

| Issue / Symptom | Possible Root Cause | Recommended Resolution |
|---|---|---|
| `streamlit: command not found` | Virtual environment is not activated or packages were installed globally. | Activate your environment (`.\venv\Scripts\Activate.ps1` or `source venv/bin/activate`) and verify `pip list`. |
| Port `8000` or `8501` already in use | Another application or previous instance is running on the target port. | Run backend on alternate port: `python -m uvicorn backend.app.main:app --port 8001`. For Streamlit: `streamlit run src/app.py --server.port 8502`. |
| `npm ERR! missing script: dev` | The terminal is in the project root instead of the `frontend` directory. | Run `cd frontend` before executing `npm run dev`. |
| Script execution disabled in PowerShell | Windows default execution policy restricts script execution. | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell, then re-activate the virtual environment. |
| SQLite `OperationalError: locked` | Multiple concurrent processes writing to the database file simultaneously. | Stop duplicate background python processes or restart the backend service. |

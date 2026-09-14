# Solution Overview: RouteWise AI

## Intelligent Supply Chain & Cold-Chain Resilience Platform

RouteWise AI is an AI-powered autonomous supply chain decision support system designed to convert complex, fragmented logistics telemetry into proactive, risk-mitigating operational actions. Built for the **IBM Bob AI Innovation Hackathon 2026 (AI Track)** by team **CHARUSAT Innovators**, the platform specifically targets high-value freight vulnerabilities, port disruptions, and time-critical cold-chain excursions.

---

## 1. The Core Mechanism

RouteWise AI transforms supply chain management from a **reactive, manual triage loop** into a **proactive, conversational intelligence experience**. The platform operates through a closed-loop autonomous pipeline:

```
[IoT Sensors & Fleet Telematics]  +  [External Disruption Feeds (Weather, Strikes)]
                                  │
                                  ▼
                ┌──────────────────────────────────┐
                │   Geospatial & Temporal Engine   │
                │     - Proximity spatial hashing  │
                │     - Delay projection modeling  │
                │     - Thermal slope calculation  │
                └─────────────────┬────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────┐
                │    Multi-Criteria Reroute Engine │
                │     - Cost vs. SLA tradeoff      │
                │     - Carrier reliability index  │
                │     - Idle asset surge matching  │
                └─────────────────┬────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────┐
                │    IBM Bob AI Copilot & MCP      │
                │     - IBM watsonx.ai Granite LLM │
                │     - Model Context Protocol API │
                │     - Deterministic fallback     │
                └─────────────────┬────────────────┘
                                  │
                                  ▼
             [Interactive Actionable Decision Matrix]
             (React Enterprise UI / Streamlit Companion)
```

1. **Continuous Telemetry & Feed Ingestion:** Active consignments across sea, air, and road corridors are ingested alongside real-time container IoT data (temperature, humidity, battery, vibration) and external disruption bulletins (port labor strikes, tropical cyclones, canal closures).
2. **Predictive Risk & Thermal Slope Modeling:** Rather than waiting for a container to exceed critical temperature boundaries ($>8.0^\circ\text{C}$), the engine calculates the rate of thermal change ($\Delta T / \Delta t$) across rolling time windows, alerting operators hours before irreversible biological invalidation occurs.
3. **Multi-Criteria Route Optimization:** When a corridor is compromised, the engine computes alternative transshipment options, scoring each route across direct financial cost, transit delta, carbon footprint, and carrier reliability.
4. **Surge Fleet Repositioning:** The system automatically cross-references nearby regional depots for idle fleet capacity (e.g., refrigerated trailers dwelling $>4\text{ hours}$), matching stranded cargo to ready assets.
5. **Conversational Synthesis via IBM Bob:** Logistics dispatchers and executives interact with the system using natural language queries. IBM Bob provides clear, context-grounded situation reports and one-click execution plans.

---

## 2. Key Capabilities & Functional Modules

### A. Conversational IBM Bob Copilot
- **Natural Language Understanding:** Evaluates dispatcher intent—from broad executive summaries ("Summarize today's supply-chain risks") to root-cause inquiries ("Why is shipment SH-001 delayed?") and tactical fleet lookups ("Find idle assets in Ahmedabad").
- **Grounded Responses:** Responses are strictly anchored in verified database state, spatial coordinates, and IoT telemetry, eliminating LLM hallucinations.
- **Bi-Modal AI Architecture:** Powered by **IBM watsonx.ai (Granite-13b-instruct)** when enterprise cloud credentials are configured, with automatic failover to an intelligent, deterministic local engine for offline reliability.

### B. Standardized Model Context Protocol (MCP) Server
- RouteWise AI exposes its entire analytical capability through an open **Model Context Protocol** interface.
- External AI agents, developer tools, and automation runtimes can natively discover and invoke 6 standardized tools:
  - `get_active_shipments`: Real-time query of active consignments with origin, destination, carrier, and cargo classification.
  - `get_disruption_feed`: Live spatial disruption alerts categorized by severity (Warning, Severe, Critical).
  - `assess_shipment_risk`: Computational risk scoring (0–100) combining distance, speed, cargo fragility, and disruption impact.
  - `simulate_route_alternatives`: Dynamic route simulation comparing time, financial cost, and carbon tradeoffs.
  - `get_idle_fleet_assets`: Depot dwell time monitoring and idle capacity detection for surge dispatch.
  - `get_cold_chain_telemetry`: IoT sensor telemetry, excursion tracking, and thermal drift slope analysis.

### C. Cold-Chain Thermal Excursion Intelligence
- Tracks temperature stability budgets for sensitive pharmaceuticals (mRNA vaccines, biologics, insulin) and perishable goods.
- Detects early refrigeration unit failure through ambient heat infiltration modeling:
  $$\text{Thermal Slope } (\beta) = \frac{T_{\text{current}} - T_{\text{initial}}}{\Delta t}$$
- Immediately flags consignments experiencing $\beta > 0.35^\circ\text{C/hr}$ even if the current temperature is still within legal limits, enabling proactive dispatch before cargo destruction.

### D. Multi-Modal Alternative Corridors
- Evaluates bypass corridors when critical chokepoints fail (e.g., bypassing Port of Rotterdam strike via Antwerp rail transshipment, or bypassing Cape Hatteras storm via inland rail corridor).
- Computes weighted recommendation scores based on configurable operational priorities:
  $$\text{Score} = w_{\text{time}} \cdot \tilde{T} + w_{\text{cost}} \cdot \tilde{C} + w_{\text{rel}} \cdot R - w_{\text{co2}} \cdot E$$

---

## 3. Difference from Naive Alternatives

| Capability | Naive Logistics Dashboard | Rule-Based Alerts | RouteWise AI (Our Solution) |
|---|---|---|---|
| **Alert Paradigm** | Static map markers with delayed status dots. | Threshold alerts ("Delay > 24 hrs") causing alert fatigue. | **Context-aware predictive alerts** factoring cargo type, temperature slope, and perishable SLA. |
| **Decision Support** | Human must mentally correlate maps, weather, and manifests. | Simple threshold notification with no actionable next step. | **Automated reroute generation** with cost, time, reliability, and idle fleet recommendations. |
| **Cold-Chain Safety** | Post-incident reporting after temperature is already breached. | Alert when $T > 8^\circ\text{C}$ (too late to save biological cargo). | **Thermal slope monitoring** detecting refrigeration failure hours prior to boundary breach. |
| **Interaction Model** | Complex filters across 6+ database tables and tabs. | Fixed notification feeds in SMS/Email. | **Conversational IBM Bob Copilot** answering natural language queries with full factual grounding. |
| **Interoperability** | Siloed web interface with proprietary APIs. | Proprietary webhook triggers. | **Standardized MCP Server** allowing any AI agent to query supply chain state and execute actions. |

---

## 4. Key Design Decisions

1. **Dual Frontend Architecture:**
   - **React 18 + Vite + Tailwind CSS + Lucide Icons:** A high-fidelity, responsive enterprise command center providing interactive disruption maps, sensor telemetry curves, rerouting matrices, and the full IBM Bob Copilot drawer.
   - **Streamlit Copilot Companion (`src/app.py`):** A single-file, zero-dependency Python dashboard for rapid stakeholder demos, hackathon evaluation, and lightweight operational field use.
2. **FastAPI Modular Backend:**
   - High-performance asynchronous Python architecture with typed Pydantic models, OpenAPI auto-documentation, and clean separation of concerns across routes, services, simulation engines, and MCP servers.
3. **Graceful Fallback & Deterministic Reliability:**
   - Cloud LLMs can suffer rate limits, latency spikes, or offline network restrictions. RouteWise AI integrates a robust offline reasoning engine that generates comprehensive, mathematically accurate supply chain recommendations even when external LLM services are unreachable.
4. **Model Context Protocol (MCP) First:**
   - Instead of locking supply chain logic inside proprietary UI components, exposing core functionality via MCP ensures RouteWise AI can act as the logistics tool layer for modern agentic workflows (IBM Bob, Claude Desktop, Cursor, and enterprise orchestrators).

---

## 5. Technical Honesty & Production Path

### What is Real in this Repository:
- Fully functional, production-ready FastAPI backend with all REST and MCP endpoints live.
- Fully functional React 18 frontend and Streamlit companion application.
- Real mathematical models for risk scoring (0–100), thermal slope derivation ($\Delta T / \Delta t$), and multi-attribute route evaluation.
- Full SQLite/SQLAlchemy schema and repository layer with active migrations.
- Complete unit test suite with 100% passing coverage for API routes, engines, and conversational AI intents.

### What is Simulated for Hackathon Demonstration:
- **Disruption Feeds:** Weather events (e.g., Tropical Storm Alex) and port strikes (e.g., Port of Rotterdam) are generated via calibrated simulation models mimicking real NOAA and maritime bulletin formats.
- **IoT Telemetry:** Reefer container temperatures are simulated using an environmental physics model that incorporates ambient temperatures and refrigeration power dropouts.
- **LLM Connection:** The system includes full IBM watsonx.ai SDK integration code. When watsonx API credentials are omitted in `.env`, the system defaults to the deterministic offline intelligence engine to guarantee reliable evaluation without requiring judges to configure cloud API keys.

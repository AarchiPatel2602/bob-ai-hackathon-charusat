# RouteWise AI 🚢

## Team
**Name:** CHARUSAT Innovators
**Track:** AI
**Lead:** Ayush Vyas (D25IT130@CHARUSAT.EDU.IN)
**Members:** [Add Member 2 Name], [Add Member 3 Name], [Add Member 4 Name]

## Problem Statement
Logistics teams manage millions of dollars in temperature-sensitive cargo (cold-chain), but tracking is highly fragmented. When global disruptions occur (extreme weather, port strikes), teams cannot manually cross-reference weather APIs with active shipments fast enough, resulting in catastrophic cargo spoilage and supply chain bottlenecks.

## Solution
RouteWise AI is an intelligent supply chain copilot powered by IBM watsonx. It acts as an AI assistant that instantly correlates active fleet IoT data with live weather/disruption APIs via MCP connectors, allowing managers to query their supply chain in natural language and receive automated rerouting recommendations before cargo spoils.

## Key Features
- **IBM Bob Conversational UI:** Natural language chat interface for non-technical logistics managers to query complex fleet data.
- **MCP Disruption Integration:** Connects to external APIs to simulate live weather and port strike alerts.
- **Cold-Chain IoT Monitoring:** Automatically flags temperature excursions across active shipments.
- **AI Rerouting Engine:** Suggests cost-optimized rerouting options to avoid active disruption zones.

## Tech Stack
- **Frontend & App Logic:** Python, Streamlit, Pandas
- **AI Integration:** IBM Bob Copilot, watsonx.ai (Granite models)
- **Data Connectivity:** Model Context Protocol (MCP)

## How to Run
Please see [docs/setup-guide.md](docs/setup-guide.md) for full installation and execution instructions.

## Demo
- **Video Walkthrough:** [Insert YouTube/Loom Link Here]
- **Live Demo:** NOT DEPLOYED (Local Execution via Streamlit)
- Screenshots are available in the `demo/screenshots/` folder.

## Known Limitations
- The current implementation uses simulated IoT data and mocked weather disruption alerts rather than a live production database.
- Rerouting logic is currently rule-based and heavily simulated for demo purposes rather than querying a live global mapping API.

## What We're Most Proud Of
We are incredibly proud of how quickly we integrated the IBM Bob conversational interface to replace a complex, multi-dashboard logistics workflow with a simple, natural language chat experience.

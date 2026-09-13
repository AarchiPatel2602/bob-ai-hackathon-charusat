# Solution Overview

## The Core Mechanism
RouteWise AI transforms supply chain management from a reactive, dashboard-heavy process into a proactive, conversational experience. The core mechanism involves three steps:
1. **Data Ingestion:** The system pulls active fleet statuses and cold-chain IoT temperature data into a unified dataframe.
2. **Disruption Correlation:** Using MCP (Model Context Protocol) connectors, the system ingests external disruption data (simulated weather events, port strikes).
3. **AI Orchestration:** IBM Bob and watsonx.ai analyze the intersection of the disruption zones and the active fleet. When a user asks a question, the AI generates a natural language summary identifying compromised shipments and provides an actionable rerouting plan.

## Difference from Naive Alternatives
Naive supply chain solutions rely on rule-based alerts (e.g., "Alert: Truck 1042 is delayed by 48 hours"). This causes massive alert fatigue for operators. 
RouteWise AI is different because it understands **context**. It recognizes that Truck 1042 is carrying *vaccines*, meaning a 48-hour delay will cause a temperature excursion. It immediately escalates this to "CRITICAL" and suggests an alternative route.

## Key Design Decisions
- **Streamlit Framework:** We chose Python and Streamlit to build the frontend. This allowed us to rapidly prototype a data-rich UI with interactive dataframes and maps while seamlessly integrating our backend AI logic in a single file.
- **Conversational UI over Dashboards:** Logistics managers are not data scientists. We designed the primary interaction method to be a chat window ("IBM Bob Copilot") because asking "Which ships are stuck in the storm?" is infinitely faster than filtering through 5 different database views.

## User Experience
The user logs into a single screen. On the right, they see high-level active disruptions and a map of their fleet. On the left, they have the IBM Bob chat interface. The user simply types their concern into the chat, and the AI instantly outputs a summarized impact report and recommended action plan.

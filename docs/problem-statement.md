# Problem Statement: Global Supply Chain Vulnerability & Cold-Chain Fragility

## 1. Target Audience & Operational Personas

RouteWise AI addresses the operational challenges faced by four key stakeholders across the freight and logistics ecosystem:

- **Global Logistics Directors & Dispatchers:** Responsible for real-time tracking and delivery compliance of active multi-modal consignments across maritime, air, and road corridors.
- **Cold-Chain Quality & Compliance Officers:** Charged with ensuring temperature-sensitive cargo (pharmaceuticals, vaccines, biologics, organs, and perishable foods) adheres to strict regulatory bounds (Good Distribution Practice - GDP, FDA 21 CFR Part 11, and WHO temperature standards).
- **Fleet & Terminal Operations Managers:** Tasked with balancing asset utilisation, dwell times, and driver scheduling across regional distribution hubs.
- **Supply Chain Risk & Resilience Analysts:** Required to quantify financial exposure, calculate cargo value at risk, and identify contingency corridors during systemic shocks.

---

## 2. The Core Problem: The Manual Correlation Bottleneck

Modern supply chains do not suffer from a lack of data—they suffer from **data fragmentation and correlation latency**.

During a major operational disruption (e.g., a regional port labor strike, tropical storm, or canal closure), a logistics manager must manually monitor and cross-reference multiple disconnected systems:
1. **External Meteorological & Geopolitical Feeds:** Public weather radars, maritime safety bulletins, and port authority strike notices.
2. **Carrier & Freight Forwarder Portals:** Web portals for ocean carriers (Maersk, MSC, CMA CGM) and freight forwarders to verify gate closures and vessel schedules.
3. **IoT Sensor & Telematics Platforms:** Cold-chain IoT dashboards tracking real-time container temperature, humidity, GPS location, and battery level.
4. **Internal Enterprise ERPs & Fleet Spreadsheets:** ERP manifests detailing cargo valuation, priority class, consignee penalty clauses, and depot fleet availability.

### Why Manual Correlation Fails:
Under normal conditions, reconciling these disparate sources is tedious. **During a crisis, it is fatal:**
- A human dispatcher takes **45 to 90 minutes** to manually cross-reference 50 active shipments against an expanding weather event or port strike perimeter.
- By the time the manager identifies that a specific container is trapped in an affected corridor, the container refrigeration auxiliary power unit (APU) may already be drained or port gates closed.
- Evaluating alternate transshipment corridors, carrier reliability ratings, and transit surcharges requires further manual phone calls and email threads, creating compounding delays.

---

## 3. Cold-Chain Excursions: The Hidden Crisis

For general dry cargo, a 48-hour delay means higher demurrage fees or minor late penalties. For **cold-chain consignments**, a 48-hour delay is often catastrophic:

- **Thermal Excursion Dynamics:** High-value pharmaceuticals (such as mRNA vaccines, monoclonal antibodies, and insulin) must remain strictly between **2.0°C and 8.0°C**. When a refrigerated container sits idle in a congested port terminal during high ambient temperatures, internal temperatures rise gradually ($\Delta T / \Delta t > 0.35^\circ\text{C/hr}$).
- **Irreversible Biological Invalidation:** Once cumulative temperature excursions exceed regulatory stability time-temperature budgets, the active pharmaceutical ingredient (API) degrades. The entire consignment must be quarantined and destroyed.
- **Extreme Financial & Human Exposure:** A single reefer container of vaccines or specialty biologics represents between **$500,000 and $2,000,000** in cargo value. In public health logistics, lost consignments result in regional vaccine shortages and delayed critical patient treatments.

---

## 4. Underutilized Fleet Capacity & Surge Repositioning

While port terminals in one region experience severe gridlock and equipment shortages, nearby inland depots frequently have refrigerated trucks and dry trailers sitting **idle** due to localized demand slumps.

Logistics teams lack real-time visibility into:
- Which assets have exceeded standard dwell thresholds (e.g., TRUCK-205 idle in Ahmedabad for 8+ hours).
- Whether those idle assets possess compatible refrigeration and capacity specifications to absorb cargo diverted from impacted ports.
- How repositioning idle fleet assets would improve network utilisation and mitigate delay penalties.

---

## 5. Why Rapid, Proactive Decision Support Matters

The logistics industry can no longer rely on **reactive dashboards** where operators merely observe green, yellow, and red status dots after an incident has already occurred.

Logistics coordinators require an **autonomous intelligence layer** that:
1. Detects disruptions spatially the moment they are reported.
2. Identifies all exposed consignments and quantifies cargo value at risk instantly.
3. Predicts thermal compliance breaches *before* upper limits are breached using thermal slope modeling.
4. Generates ranked, viable multimodal bypass options with explicit cost, time, and risk tradeoffs.
5. Surfaces available idle fleet assets for surge capacity redeployment.
6. Allows managers to query the entire network state through a natural language conversational copilot (**IBM Bob**) with guaranteed factual grounding.

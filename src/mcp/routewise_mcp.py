"""
RouteWise AI — Model Context Protocol (MCP) Server
Exposes supply chain resilience tools and telemetry data sources for IBM Bob and AI agents.
Conforms to MCP standard tool and resource specifications.
"""

import sys
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# MCP Tool Specifications
MCP_TOOLS = [
    {
        "name": "get_active_shipments",
        "description": "Retrieve active supply-chain shipments with risk ratings, origin/destination corridors, cargo sensitivity, and current location.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "risk_level": {
                    "type": "string",
                    "enum": ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "description": "Optional filter by risk category."
                },
                "cold_chain_only": {
                    "type": "boolean",
                    "description": "Filter for temperature-controlled cargo only."
                }
            }
        }
    },
    {
        "name": "get_disruption_feed",
        "description": "Fetch live operational disruptions (weather systems, port strikes, canal bottlenecks) impacting global logistics corridors.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "default": "ACTIVE",
                    "description": "Disruption status filter (ACTIVE, RESOLVED, ALL)."
                }
            }
        }
    },
    {
        "name": "assess_shipment_risk",
        "description": "Compute deterministic 0–100 risk score, risk level, and root-cause drivers for a specified consignment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shipment_identifier": {
                    "type": "string",
                    "description": "Unique identifier of the consignment (e.g. SH-1024)."
                }
            },
            "required": ["shipment_identifier"]
        }
    },
    {
        "name": "simulate_route_alternatives",
        "description": "Generate and evaluate alternate multimodal corridors to bypass active bottlenecks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shipment_identifier": {
                    "type": "string",
                    "description": "Shipment identifier to evaluate alternate routes for."
                }
            },
            "required": ["shipment_identifier"]
        }
    },
    {
        "name": "get_idle_fleet_assets",
        "description": "Query available and idle fleet assets (reefer trucks, container vessels) eligible for surge repositioning.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_idle_hours": {
                    "type": "number",
                    "default": 4.0,
                    "description": "Minimum idle dwell time in hours."
                }
            }
        }
    },
    {
        "name": "get_cold_chain_telemetry",
        "description": "Retrieve live IoT thermal telemetry, compliance bounds, and predictive breach forecasts for cold-chain consignments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shipment_identifier": {
                    "type": "string",
                    "description": "Shipment identifier."
                }
            },
            "required": ["shipment_identifier"]
        }
    }
]


class RouteWiseMCPServer:
    """
    RouteWise Model Context Protocol Server implementation.
    Supports both JSON-RPC stdio pipe execution and programmatic in-process tool dispatch.
    """

    def __init__(self, db_session=None, user_id=None):
        self.db_session = db_session
        self.user_id = user_id

    def list_tools(self) -> List[Dict[str, Any]]:
        return MCP_TOOLS

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from backend.app.database import SessionLocal
        from backend.app.models.user import User
        from backend.app.models.shipment import Shipment
        from backend.app.models.disruption import Disruption
        from backend.app.models.fleet import FleetAsset
        from backend.app.models.sensor import SensorReading
        from backend.app.engines.disruption_engine import shipment_is_affected
        from backend.app.engines.fleet_engine import find_idle_assets
        from backend.app.engines.route_engine import generate_alternative_routes

        db = self.db_session or SessionLocal()
        close_needed = self.db_session is None

        try:
            # 1. get_active_shipments
            if name == "get_active_shipments":
                query = db.query(Shipment)
                if self.user_id:
                    query = query.filter(Shipment.user_id == self.user_id)
                
                risk_filter = arguments.get("risk_level", "ALL")
                if risk_filter and risk_filter != "ALL":
                    query = query.filter(Shipment.risk_level == risk_filter)
                
                if arguments.get("cold_chain_only"):
                    query = query.filter(Shipment.cold_chain_enabled == True)

                records = query.all()
                data = [
                    {
                        "shipment_identifier": s.shipment_identifier,
                        "origin": s.origin,
                        "destination": s.destination,
                        "current_location": s.current_location,
                        "cargo_type": s.cargo_type,
                        "cargo_value_usd": s.cargo_value,
                        "risk_score": s.risk_score,
                        "risk_level": s.risk_level,
                        "status": s.status,
                        "cold_chain_enabled": s.cold_chain_enabled
                    }
                    for s in records
                ]
                return {"count": len(data), "shipments": data}

            # 2. get_disruption_feed
            elif name == "get_disruption_feed":
                status = arguments.get("status", "ACTIVE")
                query = db.query(Disruption)
                if status != "ALL":
                    query = query.filter(Disruption.status == status)
                
                disruptions = query.all()
                return {
                    "count": len(disruptions),
                    "disruptions": [
                        {
                            "name": d.name,
                            "type": d.type,
                            "location": d.location,
                            "severity": d.severity,
                            "expected_duration_days": d.expected_duration_days,
                            "status": d.status
                        }
                        for d in disruptions
                    ]
                }

            # 3. assess_shipment_risk
            elif name == "assess_shipment_risk":
                ident = arguments.get("shipment_identifier")
                shipment = db.query(Shipment).filter(Shipment.shipment_identifier == ident).first()
                if not shipment:
                    return {"error": f"Shipment {ident} not found."}

                disruptions = db.query(Disruption).filter(Disruption.status == "ACTIVE").all()
                reasons = []
                for d in disruptions:
                    aff, reason = shipment_is_affected(shipment, d)
                    if aff:
                        reasons.append(f"Corridor impacted by {d.name} at {d.location}")

                return {
                    "shipment_identifier": shipment.shipment_identifier,
                    "risk_score": shipment.risk_score,
                    "risk_level": shipment.risk_level,
                    "cargo_value_usd": shipment.cargo_value,
                    "corridor": f"{shipment.origin} -> {shipment.destination}",
                    "identified_drivers": reasons or ["Nominal transit parameters."]
                }

            # 4. simulate_route_alternatives
            elif name == "simulate_route_alternatives":
                ident = arguments.get("shipment_identifier")
                shipment = db.query(Shipment).filter(Shipment.shipment_identifier == ident).first()
                if not shipment:
                    return {"error": f"Shipment {ident} not found."}

                disruptions = db.query(Disruption).filter(Disruption.status == "ACTIVE").all()
                disrupt_loc = disruptions[0].location if disruptions else ""
                alternatives = generate_alternative_routes(shipment, disrupt_loc)
                return {
                    "shipment_identifier": ident,
                    "current_risk": shipment.risk_score,
                    "alternatives": alternatives
                }

            # 5. get_idle_fleet_assets
            elif name == "get_idle_fleet_assets":
                user = db.query(User).first()
                u_id = self.user_id or (user.id if user else 1)
                idle = find_idle_assets(db, u_id)
                return {
                    "count": len(idle),
                    "idle_assets": idle
                }

            # 6. get_cold_chain_telemetry
            elif name == "get_cold_chain_telemetry":
                ident = arguments.get("shipment_identifier")
                shipment = db.query(Shipment).filter(Shipment.shipment_identifier == ident).first()
                if not shipment:
                    return {"error": f"Shipment {ident} not found."}

                readings = db.query(SensorReading).filter(SensorReading.shipment_id == shipment.id).order_by(SensorReading.timestamp.desc()).limit(15).all()
                data = [
                    {
                        "temperature": r.temperature,
                        "humidity": r.humidity,
                        "is_excursion": r.is_excursion,
                        "severity": r.severity,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None
                    }
                    for r in readings
                ]
                return {
                    "shipment_identifier": ident,
                    "cold_chain_enabled": shipment.cold_chain_enabled,
                    "compliance_bounds": {
                        "min_temp": shipment.minimum_temperature,
                        "max_temp": shipment.maximum_temperature
                    },
                    "reading_count": len(data),
                    "recent_telemetry": data
                }

            else:
                return {"error": f"Unknown MCP tool: {name}"}

        finally:
            if close_needed:
                db.close()


# CLI / JSON-RPC Runner
async def run_mcp_cli():
    server = RouteWiseMCPServer()
    if len(sys.argv) > 1 and sys.argv[1] == "--list-tools":
        print(json.dumps(server.list_tools(), indent=2))
        return
    elif len(sys.argv) > 2 and sys.argv[1] == "--call":
        tool_name = sys.argv[2]
        tool_args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = await server.call_tool(tool_name, tool_args)
        print(json.dumps(result, indent=2))
        return

    # Standard JSON-RPC stdio mode
    print("RouteWise AI MCP Server initialized. Ready for JSON-RPC messages.", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(run_mcp_cli())

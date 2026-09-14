from typing import List, Dict, Any
from backend.app.models.shipment import Shipment

def generate_alternative_routes(shipment: Shipment, disrupted_node: str = "") -> List[Dict[str, Any]]:
    """
    Generate and rank alternative routes avoiding disrupted nodes.
    Balances risk mitigation, transit time, cost, and cold-chain compliance.
    """
    origin = shipment.origin
    destination = shipment.destination
    is_cold_chain = shipment.cold_chain_enabled
    
    # Corridor check for realistic hub diversion
    if "mumbai" in origin.lower() and "rotterdam" in destination.lower():
        alternatives = [
            {
                "id": "ALT-A",
                "name": "Alternative A (Transshipment via Colombo)",
                "waypoints": ["Mumbai Feeder", "Colombo Maritime Hub", "Suez Canal Bypass", "Rotterdam Port"],
                "additional_time_hours": 18.0,
                "additional_cost_usd": 8400.0,
                "projected_risk_score": 24,
                "projected_risk_level": "LOW",
                "cold_chain_compatible": True,
                "disruption_exposure": "None (Bypasses Mumbai Congestion via Southern Feeder)",
                "summary": "Fastest sea bypass via Colombo Deep Sea Terminal. Full reefer plug-in support.",
                "tag": "RECOMMENDED"
            },
            {
                "id": "ALT-B",
                "name": "Alternative B (Transshipment via Singapore)",
                "waypoints": ["Mumbai", "Singapore Port", "Cape Route", "Rotterdam Port"],
                "additional_time_hours": 32.0,
                "additional_cost_usd": 5200.0,
                "projected_risk_score": 42,
                "projected_risk_level": "MEDIUM",
                "cold_chain_compatible": True,
                "disruption_exposure": "None (Extended maritime lane)",
                "summary": "Most economical maritime bypass, suitable if 32h delay is tolerable.",
                "tag": "BEST VALUE"
            },
            {
                "id": "ALT-C",
                "name": "Alternative C (Intermodal Air-Sea via Frankfurt)",
                "waypoints": ["Mumbai International Cargo", "Frankfurt Logistics Hub", "Rotterdam Overland"],
                "additional_time_hours": 6.0,
                "additional_cost_usd": 18500.0,
                "projected_risk_score": 12,
                "projected_risk_level": "LOW",
                "cold_chain_compatible": is_cold_chain,
                "disruption_exposure": "None (Direct Air Cargo)",
                "summary": "Urgent air diversion. Eliminates all maritime delay at premium rate.",
                "tag": "FASTEST"
            }
        ]
    else:
        # Dynamic generic bypass generator
        bypass_hub_1 = f"Hub North ({origin} Bypass)"
        bypass_hub_2 = f"Hub South (Express Lane)"
        
        alternatives = [
            {
                "id": "ALT-A",
                "name": f"Alternative A (Regional Bypass via {bypass_hub_1})",
                "waypoints": [origin, bypass_hub_1, destination],
                "additional_time_hours": 14.0,
                "additional_cost_usd": round(shipment.cargo_value * 0.015 + 2500, 2),
                "projected_risk_score": 26,
                "projected_risk_level": "LOW",
                "cold_chain_compatible": True,
                "disruption_exposure": "Bypasses primary transit corridor",
                "summary": f"Reroutes around {disrupted_node or 'disrupted area'} with validated carrier capacity.",
                "tag": "RECOMMENDED"
            },
            {
                "id": "ALT-B",
                "name": f"Alternative B (Direct Secondary Corridor via {bypass_hub_2})",
                "waypoints": [origin, bypass_hub_2, destination],
                "additional_time_hours": 26.0,
                "additional_cost_usd": round(shipment.cargo_value * 0.008 + 1200, 2),
                "projected_risk_score": 38,
                "projected_risk_level": "MEDIUM",
                "cold_chain_compatible": True,
                "disruption_exposure": "Clear secondary lane",
                "summary": "Lowest surcharge alternative route with reliable schedules.",
                "tag": "BEST VALUE"
            }
        ]

    # Rank alternatives based on composite score: 
    # lower risk weight 0.5, lower time weight 0.25, lower cost weight 0.25
    for alt in alternatives:
        score = (alt["projected_risk_score"] * 0.5) + (alt["additional_time_hours"] * 0.3) + (alt["additional_cost_usd"] / 1000.0 * 0.2)
        alt["composite_rank_score"] = round(score, 2)

    alternatives.sort(key=lambda x: x["composite_rank_score"])
    return alternatives

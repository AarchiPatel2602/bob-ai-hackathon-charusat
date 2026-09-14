from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.carrier import Carrier
from backend.app.models.shipment import Shipment

DEFAULT_CARRIERS = [
    {"name": "Maersk Line", "code": "MAEU", "reliability_score": 94.2, "average_transit_multiplier": 1.02, "cost_index": 110.0, "cold_chain_certified": True, "status": "ACTIVE", "supported_regions": "Global, Asia-Europe, Transpacific"},
    {"name": "MSC Mediterranean", "code": "MSCU", "reliability_score": 91.8, "average_transit_multiplier": 1.08, "cost_index": 92.0, "cold_chain_certified": True, "status": "ACTIVE", "supported_regions": "Global, Asia-Europe, Transatlantic"},
    {"name": "CMA CGM Group", "code": "CMAC", "reliability_score": 89.5, "average_transit_multiplier": 1.05, "cost_index": 98.0, "cold_chain_certified": True, "status": "ACTIVE", "supported_regions": "Global, Asia, Europe, Middle East"},
    {"name": "Hapag-Lloyd", "code": "HAPG", "reliability_score": 93.0, "average_transit_multiplier": 1.01, "cost_index": 115.0, "cold_chain_certified": True, "status": "ACTIVE", "supported_regions": "Global, Americas, Europe"},
    {"name": "DHL Global Forwarding", "code": "DHLG", "reliability_score": 96.5, "average_transit_multiplier": 0.85, "cost_index": 140.0, "cold_chain_certified": True, "status": "ACTIVE", "supported_regions": "Global Express Air/Sea"},
    {"name": "Kuehne + Nagel", "code": "KNAG", "reliability_score": 92.0, "average_transit_multiplier": 1.04, "cost_index": 105.0, "cold_chain_certified": True, "status": "ACTIVE", "supported_regions": "Global Integrated Logistics"}
]

def ensure_default_carriers(db: Session):
    """Ensure standard carriers are populated in database."""
    if db.query(Carrier).count() == 0:
        for c_data in DEFAULT_CARRIERS:
            carrier = Carrier(**c_data, is_demo=True)
            db.add(carrier)
        db.commit()

def rank_alternative_carriers(db: Session, shipment: Shipment) -> List[Dict[str, Any]]:
    """
    Ranks carriers for a shipment needing reassignment or alternative contracting.
    Categorizes with BEST OVERALL, BEST VALUE, FASTEST badges.
    """
    ensure_default_carriers(db)
    
    carriers_query = db.query(Carrier).filter(
        Carrier.status == "ACTIVE",
        Carrier.name != shipment.carrier
    )

    if shipment.cold_chain_enabled:
        carriers_query = carriers_query.filter(Carrier.cold_chain_certified == True)

    carriers = carriers_query.all()
    if not carriers:
        return []

    results = []
    for c in carriers:
        # Calculate estimated cost delta based on shipment cargo value and carrier cost index
        base_shipping_estimate = shipment.cargo_value * 0.03 # assume ~3% shipping cost
        carrier_cost = round(base_shipping_estimate * (c.cost_index / 100.0), 2)
        
        # Composite score: reliability has high weight, lower transit mult and cost index preferred
        composite = (c.reliability_score * 1.5) - (c.cost_index * 0.4) - (c.average_transit_multiplier * 20)
        
        results.append({
            "carrier_id": c.id,
            "carrier_name": c.name,
            "carrier_code": c.code,
            "reliability_score": c.reliability_score,
            "transit_multiplier": c.average_transit_multiplier,
            "cost_index": c.cost_index,
            "estimated_cost_usd": carrier_cost,
            "cold_chain_certified": c.cold_chain_certified,
            "supported_regions": c.supported_regions,
            "composite_score": round(composite, 2),
            "tag": ""
        })

    # Sort and assign badges
    # Highest composite score -> BEST OVERALL
    results.sort(key=lambda x: x["composite_score"], reverse=True)
    if results:
        results[0]["tag"] = "BEST OVERALL"

    # Lowest cost -> BEST VALUE
    lowest_cost = min(results, key=lambda x: x["cost_index"])
    if not lowest_cost["tag"]:
        lowest_cost["tag"] = "BEST VALUE"

    # Fastest transit -> FASTEST
    fastest = min(results, key=lambda x: x["transit_multiplier"])
    if not fastest["tag"]:
        fastest["tag"] = "FASTEST"

    return results

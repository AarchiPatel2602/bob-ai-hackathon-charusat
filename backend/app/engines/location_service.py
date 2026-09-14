from typing import Tuple, Dict, Any, Optional, List
import math

# Authoritative geographical coordinate registry for ports, logistics hubs, maritime corridors, and fleet bases
KNOWN_LOCATIONS: Dict[str, Tuple[float, float]] = {
    # India Corridors
    "mumbai": (18.9438, 72.8387),
    "mumbai port": (18.9488, 72.8524),
    "mumbai port gate 3": (18.9488, 72.8524),
    "mumbai sea hub": (18.9438, 72.8387),
    "mumbai feeder": (18.9300, 72.8200),
    "mumbai international cargo": (19.0896, 72.8656),
    "nhava sheva": (18.9500, 72.9500),
    "ahmedabad": (23.0225, 72.5714),
    "chennai": (13.0827, 80.2707),
    "chennai hub": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "kolkata hub": (22.5726, 88.3639),

    # Middle East & South Asia
    "colombo": (6.9271, 79.8612),
    "colombo maritime hub": (6.9400, 79.8500),
    "colombo hub": (6.9271, 79.8612),
    "dubai": (25.2048, 55.2708),
    "dubai port": (25.2769, 55.2962),
    "jeddah": (21.4858, 39.1925),
    "suez canal": (30.5852, 32.2654),
    "suez canal bypass": (30.5852, 32.2654),

    # Southeast & East Asia
    "singapore": (1.3521, 103.8198),
    "singapore port": (1.2644, 103.8228),
    "malacca strait": (4.2105, 100.5562),
    "south china sea": (14.5995, 115.5492),
    "shanghai": (31.2304, 121.4737),
    "shenzhen": (22.5431, 114.0579),
    "tokyo": (35.6762, 139.6503),
    "yokohama": (35.4437, 139.6380),
    "yokohama hub": (35.4437, 139.6380),
    "busan": (35.1796, 129.0756),
    "taipei": (25.0330, 121.5654),
    "taipei hub": (25.0330, 121.5654),
    "bangkok": (13.7563, 100.5018),
    "bangkok hub": (13.7563, 100.5018),

    # Europe
    "rotterdam": (51.9244, 4.4777),
    "rotterdam gateway": (51.9500, 4.1300),
    "rotterdam port": (51.9500, 4.1300),
    "rotterdam overland": (51.9244, 4.4777),
    "amsterdam": (52.3676, 4.9041),
    "antwerp": (51.2194, 4.4025),
    "hamburg": (53.5511, 9.9937),
    "frankfurt": (50.1109, 8.6821),
    "frankfurt logistics hub": (50.0379, 8.5622),
    "frankfurt cargocity": (50.0379, 8.5622),
    "london": (51.5074, -0.1278),
    "paris": (48.8566, 2.3522),
    "genoa": (44.4056, 8.9463),
    "alps transit": (46.5000, 8.5000),
    "munich": (48.1351, 11.5820),
    "munich hub": (48.1351, 11.5820),
    "basel": (47.5596, 7.5886),
    "basel hub": (47.5596, 7.5886),
    "bergen": (60.3913, 5.3221),
    "north sea lane": (56.0000, 3.0000),
    "dublin": (53.3498, -6.2603),
    "dublin hub": (53.3498, -6.2603),
    "helsinki": (60.1699, 24.9384),
    "helsinki hub": (60.1699, 24.9384),
    "barcelona": (41.3851, 2.1734),

    # Americas & Oceania
    "new york": (40.7128, -74.0060),
    "boston": (42.3601, -71.0589),
    "chicago": (41.8781, -87.6298),
    "chicago hub": (41.8781, -87.6298),
    "midwest express": (41.5000, -88.0000),
    "dallas": (32.7767, -96.7970),
    "los angeles": (34.0522, -118.2437),
    "seattle": (47.6062, -122.3321),
    "toronto": (43.6532, -79.3832),
    "toronto hub": (43.6532, -79.3832),
    "vancouver": (49.2827, -123.1207),
    "santos": (-23.9618, -46.3322),
    "america": (37.0902, -95.7129),
    "sydney": (-33.8688, 151.2093),
    "sydney hub": (-33.8688, 151.2093),
    "melbourne": (-37.8136, 144.9631),

    # Maritime Lanes & Bypass Corridors
    "pacific lane 4": (28.0000, -160.0000),
    "north pacific": (40.0000, 170.0000),
    "south atlantic": (-20.0000, -25.0000),
    "atlantic hub": (35.0000, -40.0000),
    "indian ocean lane": (5.0000, 75.0000),
    "timor sea": (-11.0000, 127.0000),
    "cape route": (-34.5000, 20.0000),
    "hub north (mumbai bypass)": (20.5000, 72.9000),
    "hub north": (20.5000, 72.9000),
    "hub south (express lane)": (15.0000, 73.5000),
    "hub south": (15.0000, 73.5000)
}

_geocode_cache: Dict[str, Tuple[float, float]] = {}

def geocode_location(location_name: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    Deterministically resolves a location name to (latitude, longitude).
    Uses normalization, prefix/token matching, and caching.
    Guaranteed not to raise exceptions.
    """
    if not location_name or not isinstance(location_name, str):
        return None

    raw_clean = location_name.strip()
    if not raw_clean:
        return None

    norm = raw_clean.lower()
    if norm in _geocode_cache:
        return _geocode_cache[norm]

    # 1. Exact match in registry
    if norm in KNOWN_LOCATIONS:
        coords = KNOWN_LOCATIONS[norm]
        _geocode_cache[norm] = coords
        return coords

    # 2. Match with punctuation stripped
    stripped = norm.replace(",", " ").replace("-", " ").replace("(", " ").replace(")", " ").strip()
    if stripped in KNOWN_LOCATIONS:
        coords = KNOWN_LOCATIONS[stripped]
        _geocode_cache[norm] = coords
        return coords

    # 3. Substring containment match
    for key, coords in KNOWN_LOCATIONS.items():
        if key in norm or norm in key:
            _geocode_cache[norm] = coords
            return coords

    # 4. Token-based match (e.g. "Mumbai Port Gate 3" matches "mumbai")
    tokens = [t for t in stripped.split() if t not in {"port", "hub", "terminal", "gate", "bypass", "gateway", "city", "sea", "international", "logistics"}]
    for token in tokens:
        if token in KNOWN_LOCATIONS:
            coords = KNOWN_LOCATIONS[token]
            _geocode_cache[norm] = coords
            return coords

    # 5. Fallback deterministic hash to spread unmapped demo nodes sensibly around global trade coordinates
    hash_val = sum(ord(c) for c in norm)
    lat = round(20.0 + ((hash_val % 40) - 20) * 0.8, 4)
    lng = round(50.0 + ((hash_val * 7 % 120) - 60) * 1.2, 4)
    coords = (lat, lng)
    _geocode_cache[norm] = coords
    return coords

def calculate_haversine_distance_km(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculates great-circle distance between two coordinates in km."""
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, a))))
    r = 6371.0 # Earth radius in kilometers
    return round(c * r, 1)

def build_route_polyline(waypoints: List[str]) -> List[Dict[str, Any]]:
    """
    Builds structured waypoint list with resolved coordinates and sequence order.
    """
    route_data = []
    for idx, wp in enumerate(waypoints):
        coords = geocode_location(wp)
        lat = coords[0] if coords else 0.0
        lng = coords[1] if coords else 0.0
        stop_type = "ORIGIN" if idx == 0 else "DESTINATION" if idx == len(waypoints) - 1 else "TRANSIT STOP"
        route_data.append({
            "sequence_order": idx + 1,
            "location_name": wp,
            "latitude": lat,
            "longitude": lng,
            "stop_type": stop_type
        })
    return route_data

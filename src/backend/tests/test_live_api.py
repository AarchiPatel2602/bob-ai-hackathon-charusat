import httpx
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def run_integration_tests():
    print("Testing live SupplyGuard AI API on http://127.0.0.1:8000 ...")
    client = httpx.Client(timeout=10.0)

    # 1. Health check
    h_res = client.get("http://127.0.0.1:8000/health")
    assert h_res.status_code == 200, f"Health check failed: {h_res.text}"
    print(" [1/15] Health check OK")

    # 2. Login
    login_res = client.post(f"{BASE_URL}/auth/login", json={
        "email": "demo@supplyguard.io",
        "password": "SupplyGuard2026!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(" [2/15] Login OK (Token acquired)")

    # 3. Current User
    me_res = client.get(f"{BASE_URL}/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "demo@supplyguard.io"
    print(" [3/15] Auth /me OK")

    # 4. Dashboard Summary
    dash_res = client.get(f"{BASE_URL}/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["active_shipments"] >= 50
    print(f" [4/15] Dashboard summary OK ({dash_data['active_shipments']} active shipments, {dash_data['active_disruptions']} disruptions)")

    # 5. List Shipments
    ship_res = client.get(f"{BASE_URL}/shipments", headers=headers)
    assert ship_res.status_code == 200
    shipments = ship_res.json()
    assert len(shipments) >= 50
    hero_shipment = next((s for s in shipments if s["shipment_identifier"] == "SH-1024"), None)
    assert hero_shipment is not None, "Hero shipment SH-1024 not found!"
    print(f" [5/15] Shipments list OK (SH-1024 identified, cargo: {hero_shipment['cargo_type']}, value: ${hero_shipment['cargo_value']:,.2f})")

    # 6. Route Alternatives for SH-1024
    routes_res = client.get(f"{BASE_URL}/shipments/{hero_shipment['id']}/routes", headers=headers)
    assert routes_res.status_code == 200
    routes_data = routes_res.json()
    assert len(routes_data["alternatives"]) >= 2
    print(f" [6/15] Route alternatives OK (Top: {routes_data['alternatives'][0]['name']}, Risk: {routes_data['alternatives'][0]['projected_risk_score']})")

    # 7. Carrier Ranking
    carrier_res = client.get(f"{BASE_URL}/shipments/{hero_shipment['id']}/carriers", headers=headers)
    assert carrier_res.status_code == 200
    carriers_data = carrier_res.json()
    assert len(carriers_data["alternatives"]) >= 2
    best_carrier = next((c for c in carriers_data["alternatives"] if c["tag"] == "BEST OVERALL"), carriers_data["alternatives"][0])
    print(f" [7/15] Carrier ranking OK (Best overall: {best_carrier['carrier_name']} - {best_carrier['reliability_score']}%)")

    # 8. Fleet Matching
    fmatch_res = client.get(f"{BASE_URL}/shipments/{hero_shipment['id']}/fleet-matches", headers=headers)
    assert fmatch_res.status_code == 200
    matches = fmatch_res.json()["matches"]
    assert len(matches) > 0
    print(f" [8/15] Fleet matching OK (Top match: {matches[0]['asset_identifier']} - {matches[0]['current_location']})")

    # 9. Fleet Utilisation & Idle assets
    f_util_res = client.get(f"{BASE_URL}/fleet/utilisation", headers=headers)
    assert f_util_res.status_code == 200
    f_util = f_util_res.json()
    assert f_util["total_assets"] >= 15
    idle_res = client.get(f"{BASE_URL}/fleet/idle", headers=headers)
    assert idle_res.status_code == 200
    idle_assets = idle_res.json()
    truck_205 = next((a for a in idle_assets if a["asset_identifier"] == "TRUCK-205"), None)
    assert truck_205 is not None, "Idle asset TRUCK-205 not found!"
    print(f" [9/15] Fleet utilisation OK ({f_util['current_utilisation_pct']}%, Idle asset: {truck_205['asset_identifier']} in {truck_205['current_location']})")

    # 10. Approve Fleet Redeployment
    redeploy_res = client.post(f"{BASE_URL}/fleet/recommendations/{truck_205['id']}/approve?target_destination=Mumbai", headers=headers)
    assert redeploy_res.status_code == 200
    print(" [10/15] Fleet redeployment approval OK (Dispatched TRUCK-205 to Mumbai)")

    # 11. Sensor Simulation (Critical Excursion: 10.2°C)
    sim_res = client.post(f"{BASE_URL}/shipments/{hero_shipment['id']}/sensors/simulate", json={"mode": "critical"}, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["has_active_excursion"] is True
    assert sim_data["excursion_severity"] == "CRITICAL"
    print(f" [11/15] Sensor simulation OK (Peak temp: {sim_data['peak_temperature']}°C, Excursion: CRITICAL, Updated Risk: {sim_data['updated_risk_score']}/100)")

    # 12. Cold Chain Status & Predictive Breach
    cc_status_res = client.get(f"{BASE_URL}/shipments/{hero_shipment['id']}/cold-chain-status", headers=headers)
    assert cc_status_res.status_code == 200
    cc_data = cc_status_res.json()
    assert cc_data["has_active_excursion"] is True
    print(f" [12/15] Cold chain telematics status OK (Profile: {cc_data['compliance_profile_name']}, Severity: {cc_data['excursion_severity']})")

    # 13. Alerts Feed & Action Approval
    alerts_res = client.get(f"{BASE_URL}/alerts", headers=headers)
    assert alerts_res.status_code == 200
    alerts_list = alerts_res.json()
    assert len(alerts_list) > 0
    top_alert = alerts_list[0]
    approve_res = client.post(f"{BASE_URL}/alerts/{top_alert['id']}/approve", headers=headers)
    assert approve_res.status_code == 200
    print(f" [13/15] Alert action approval OK (Alert ID {top_alert['id']}: '{top_alert['title']}' approved and resolved)")

    # 14. AI Decision Support (Bob Decision Layer)
    ai_res = client.post(f"{BASE_URL}/ai/shipment-recommendation", json={"shipment_id": hero_shipment["id"]}, headers=headers)
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert "recommended_action" in ai_data
    assert "situation_summary" in ai_data
    print(f" [14/15] AI Decision Support OK (Provider: {ai_data['provider_label']}, Action: {ai_data['recommended_action'][:60]}...)")

    # 15. Hackathon Demo 1-Click Runner
    demo_res = client.post(f"{BASE_URL}/demo/run", headers=headers)
    assert demo_res.status_code == 200
    demo_summary = demo_res.json()
    assert demo_summary["status"] == "COMPLETED_SUCCESSFULLY"
    print(" [15/15] 1-Click Hackathon Demo Flow OK (All 12 steps verified)")

    print("\n ALL 15 LIVE END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_integration_tests()

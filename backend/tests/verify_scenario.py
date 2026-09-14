import sys
import os
sys.path.insert(0, os.path.abspath("."))
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.shipment import Shipment, ShipmentRoutePoint
from backend.app.models.alert import Alert

def test_full_scenario():
    client = TestClient(app)

    # 1. Login
    res = client.post('/api/auth/login', json={'email': 'demo@supplyguard.io', 'password': 'SupplyGuard2026!'})
    assert res.status_code == 200, f'Login failed: {res.text}'
    token = res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('[Step 1 Passed] Login successful, token acquired')

    # 2. Dashboard Map
    dash_res = client.get('/api/dashboard/map', headers=headers)
    assert dash_res.status_code == 200, f'Dashboard map failed: {dash_res.text}'
    dash_map = dash_res.json()
    num_shipments = len(dash_map['shipments'])
    num_disruptions = len(dash_map['disruptions'])
    num_assets = len(dash_map['fleet_assets'])
    print(f'[Step 2 Passed] Dashboard map returned {num_shipments} shipments, {num_disruptions} disruptions, {num_assets} fleet assets')

    # 3 & 4. Shipment Map for SH-1024
    sh_res = client.get('/api/shipments?search=SH-1024', headers=headers)
    assert sh_res.status_code == 200
    sh_list = sh_res.json()
    assert len(sh_list) > 0
    sh1024 = sh_list[0]
    sh_id = sh1024['id']

    map_res = client.get(f'/api/shipments/{sh_id}/map', headers=headers)
    assert map_res.status_code == 200
    s_map = map_res.json()
    print(f'[Step 3 & 4 Passed] SH-1024 map data: origin={s_map["origin"]["name"]}, dest={s_map["destination"]["name"]}, active_stops={len(s_map["active_route"]["points"])}')
    assert len(s_map['alternative_routes']) > 0

    # 5. Alternative route preview data
    cape_alt = next((a for a in s_map['alternative_routes'] if 'cape' in a['name'].lower()), s_map['alternative_routes'][0])
    print(f'[Step 5 Passed] Selected alternative route: {cape_alt["name"]}, waypoints={cape_alt["waypoints"]}, projected_risk={cape_alt["projected_risk_score"]}')

    # 6. Approve reroute
    reroute_res = client.post(f'/api/shipments/{sh_id}/approve-reroute', json={
        'waypoints': cape_alt['waypoints'],
        'route_id': cape_alt['id'],
        'route_name': cape_alt['name'],
        'projected_risk_score': cape_alt['projected_risk_score']
    }, headers=headers)
    assert reroute_res.status_code == 200, f'Reroute failed: {reroute_res.text}'
    approved_data = reroute_res.json()
    print(f'[Step 6 Passed] Reroute approved: risk={approved_data["risk_score"]}, waypoints={[p["location_name"] for p in approved_data["route_points"]]}')
    assert approved_data['risk_score'] == cape_alt['projected_risk_score']

    # 7. Persistence Check (simulating F5 hard refresh: completely new GET requests)
    fresh_sh = client.get(f'/api/shipments/{sh_id}', headers=headers).json()
    assert fresh_sh['risk_score'] == cape_alt['projected_risk_score'], f'Expected risk {cape_alt["projected_risk_score"]}, got {fresh_sh["risk_score"]}'
    fresh_map = client.get(f'/api/shipments/{sh_id}/map', headers=headers).json()
    assert [p['location_name'] for p in fresh_map['active_route']['points']] == cape_alt['waypoints']
    print(f'[Step 7 Passed] F5 Refresh persistence verified! Active route is now: {[p["location_name"] for p in fresh_map["active_route"]["points"]]}, Risk score is {fresh_sh["risk_score"]}')

    # 8. Cold chain simulation & alert resolution
    sim_res = client.post(f'/api/shipments/{sh_id}/sensors/simulate', json={'mode': 'critical', 'custom_temperature': 10.2}, headers=headers)
    assert sim_res.status_code == 200, f'Simulation failed: {sim_res.text}'
    print(f'[Step 8 Passed] Cold chain critical excursion simulated: temp={sim_res.json()["latest_temperature"]}')

    alerts_res = client.get('/api/alerts?is_read=false', headers=headers).json()
    unread_count_before = len(alerts_res)
    if unread_count_before > 0:
        target_alert = alerts_res[0]
        res_resolve = client.post(f'/api/alerts/{target_alert["id"]}/resolve', headers=headers)
        assert res_resolve.status_code == 200
        alerts_after = client.get('/api/alerts?is_read=false', headers=headers).json()
        assert len(alerts_after) == unread_count_before - 1, 'Unread alert count should decrement by 1 upon resolve'
        print(f'[Step 8 Sub-test Passed] Alert {target_alert["id"]} resolved and unread count decremented from {unread_count_before} to {len(alerts_after)}')

if __name__ == '__main__':
    test_full_scenario()

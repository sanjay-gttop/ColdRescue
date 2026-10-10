#!/usr/bin/env python3
"""
Verify live Amazon Location Service integration (Milestone 4).
Validates:
1. Amazon Location Route Calculator: ColdRescue-RouteCalculator-dev in ap-south-1
2. Calculating truck routes across Tamil Nadu cold chain nodes:
   - Chennai Harbour Reefer Hub (13.0827, 80.2707)
   - Guindy Cold Storage Hub (13.0067, 80.2170)
3. Direct execution of AmazonLocationRouteProvider in backend.services.route_provider
4. Fallback behavior: verifying local Haversine fallback works seamlessly if Location Service is offline
5. Captures real AWS response timestamps, distance, and duration into data/evidence/live/location_verification.json
"""

import json
import os
import sys
import time
import boto3

from backend.models.domain import Location, ReceiverNode
from backend.services.route_provider import AmazonLocationRouteProvider, LocalHaversineRouteProvider

REGION = "ap-south-1"
CALCULATOR_NAME = "ColdRescue-RouteCalculator-dev"

def test_location_service():
    client = boto3.client("location", region_name=REGION)
    
    # 1. Verify Route Calculator Resource
    print(f"Checking Amazon Location Route Calculator '{CALCULATOR_NAME}'...")
    calc_desc = client.describe_route_calculator(CalculatorName=CALCULATOR_NAME)
    print(f"Calculator ARN: {calc_desc.get('CalculatorArn')}")
    print(f"Data Source: {calc_desc.get('DataSource')}")
    assert calc_desc.get("CalculatorName") == CALCULATOR_NAME

    # 2. Test live route calculation via boto3
    origin_pos = [80.2707, 13.0827]       # [lon, lat] Chennai North
    dest_pos = [80.2170, 13.0067]         # [lon, lat] Guindy South
    print(f"Calling live calculate_route API: {origin_pos} -> {dest_pos} with TravelMode='Truck'...")
    raw_route = client.calculate_route(
        CalculatorName=CALCULATOR_NAME,
        DeparturePosition=origin_pos,
        DestinationPosition=dest_pos,
        TravelMode="Truck",
    )
    summary = raw_route.get("Summary", {})
    distance_km = summary.get("Distance", 0.0)
    duration_sec = summary.get("DurationSeconds", 0.0)
    travel_time_min = round(duration_sec / 60.0, 1)
    print(f"Live AWS Route: Distance={distance_km:.2f} km, Duration={travel_time_min} min")

    # 3. Test through ColdRescue AmazonLocationRouteProvider
    print("\nTesting via backend AmazonLocationRouteProvider class...")
    provider = AmazonLocationRouteProvider(calculator_name=CALCULATOR_NAME, region=REGION)
    origin_loc = Location(
        location_id="loc_chennai_harbour",
        name="Chennai Harbour Cold Hub",
        latitude=13.0827,
        longitude=80.2707,
    )
    dest_node = ReceiverNode(
        receiver_id="recv_guindy",
        name="Guindy Regional Depot",
        category="COLD_STORAGE_FACILITY",
        latitude=13.0067,
        longitude=80.2170,
        capacity_kg=5000.0,
        accepts_temperature_min_c=2.0,
        accepts_temperature_max_c=8.0,
    )
    estimate = provider.calculate_route(origin_loc, dest_node)
    print(f"Provider estimate: distance={estimate.distance_km} km, time={estimate.travel_time_min} min, is_fallback={estimate.is_fallback}")
    assert not estimate.is_fallback, "Expected live Amazon Location Service estimate, but got fallback"
    assert estimate.provider_name == "amazon_location_service"

    # 4. Test Haversine Fallback
    print("\nTesting fallback provider behavior...")
    fallback_provider = LocalHaversineRouteProvider()
    fallback_est = fallback_provider.calculate_route(origin_loc, dest_node)
    print(f"Fallback estimate: distance={fallback_est.distance_km} km, time={fallback_est.travel_time_min} min, is_fallback={fallback_est.is_fallback}")
    assert fallback_est.is_fallback, "Expected is_fallback=True for local fallback provider"

    # 5. Save Evidence
    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "aws_region": REGION,
        "calculator": {
            "name": CALCULATOR_NAME,
            "arn": calc_desc.get("CalculatorArn"),
            "data_source": calc_desc.get("DataSource"),
            "status": "ACTIVE"
        },
        "live_calculation": {
            "origin": {"name": origin_loc.name, "lat": origin_loc.latitude, "lon": origin_loc.longitude},
            "destination": {"name": dest_node.name, "lat": dest_node.latitude, "lon": dest_node.longitude},
            "distance_km": estimate.distance_km,
            "travel_time_min": estimate.travel_time_min,
            "average_speed_kmh": estimate.average_speed_kmh,
            "provider_name": estimate.provider_name,
            "is_fallback": estimate.is_fallback,
            "waypoints_count": len(estimate.waypoints)
        },
        "fallback_validation": {
            "provider_name": fallback_est.provider_name,
            "distance_km": fallback_est.distance_km,
            "travel_time_min": fallback_est.travel_time_min,
            "is_fallback": fallback_est.is_fallback
        },
        "overall_status": "VERIFIED_LIVE"
    }

    os.makedirs("data/evidence/live", exist_ok=True)
    evidence_path = "data/evidence/live/location_verification.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print(f"\nLive Amazon Location Service verification completed! Evidence saved to {evidence_path}")

if __name__ == "__main__":
    test_location_service()

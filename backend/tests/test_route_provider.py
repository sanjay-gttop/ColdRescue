"""
Tests for RouteProvider and LocalHaversineRouteProvider.

Tests cover:
  - Haversine distance calculations between known coordinate pairs
  - Transit time estimation based on speed and road circuity factor
  - Handling preconfigured destination distances
  - Fallback behavior on missing coordinates
  - Invalid coordinate and speed input rejection
"""
from __future__ import annotations

import pytest

from backend.models.domain import Location, ReceiverCategory, ReceiverNode
from backend.services.route_provider import LocalHaversineRouteProvider


def test_haversine_known_coordinates():
    # London (51.5074, -0.1278) to Paris (48.8566, 2.3522) ~ 343 km straight line
    dist = LocalHaversineRouteProvider.haversine_distance_km(
        51.5074, -0.1278, 48.8566, 2.3522
    )
    assert 340.0 < dist < 350.0


def test_calculate_route_with_coordinates():
    provider = LocalHaversineRouteProvider(default_speed_kmh=60.0)
    origin = Location(
        location_id="loc_01",
        name="Warehouse A",
        latitude=12.9716,
        longitude=77.5946,
    )
    destination = ReceiverNode(
        receiver_id="recv_01",
        name="Distribution Hub B",
        category=ReceiverCategory.COLD_STORAGE_FACILITY,
        capacity_kg=5000.0,
        current_load_kg=1000.0,
        accepts_temperature_min_c=0.0,
        accepts_temperature_max_c=10.0,
        latitude=13.0827,
        longitude=80.2707,  # Bangalore to Chennai ~ 290 km straight line
    )

    estimate = provider.calculate_route(origin, destination)
    assert estimate.origin_id == "loc_01"
    assert estimate.destination_id == "recv_01"
    assert estimate.distance_km > 300.0  # including road circuity
    assert estimate.travel_time_min > 0.0
    assert estimate.is_fallback is True
    assert len(estimate.waypoints) == 2


def test_calculate_route_with_preconfigured_distance():
    provider = LocalHaversineRouteProvider(default_speed_kmh=50.0)
    origin = Location(location_id="loc_02", name="Origin Farm")
    destination = ReceiverNode(
        receiver_id="recv_02",
        name="Local Depot",
        category=ReceiverCategory.FOOD_BANK,
        capacity_kg=1000.0,
        current_load_kg=200.0,
        accepts_temperature_min_c=0.0,
        accepts_temperature_max_c=8.0,
        distance_km=25.0,
        travel_time_min=30.0,
    )

    estimate = provider.calculate_route(origin, destination)
    assert estimate.distance_km == 25.0
    assert estimate.travel_time_min == 30.0
    assert estimate.provider_name == "preconfigured_distance_fallback"


def test_missing_coordinates_default_fallback():
    provider = LocalHaversineRouteProvider()
    origin = Location(location_id="loc_03", name="Unknown Origin")
    destination = ReceiverNode(
        receiver_id="recv_03",
        name="Unknown Dest",
        category=ReceiverCategory.COMMUNITY_COLD_ROOM,
        capacity_kg=500.0,
        current_load_kg=50.0,
        accepts_temperature_min_c=0.0,
        accepts_temperature_max_c=8.0,
    )

    estimate = provider.calculate_route(origin, destination)
    assert estimate.distance_km == 25.0
    assert estimate.confidence < 0.5


def test_invalid_coordinates_raise_error():
    with pytest.raises(ValueError, match="Latitude must be between"):
        LocalHaversineRouteProvider.haversine_distance_km(95.0, 0.0, 0.0, 0.0)


def test_negative_speed_raises_error():
    provider = LocalHaversineRouteProvider()
    origin = Location(location_id="loc_04", name="Origin")
    destination = ReceiverNode(
        receiver_id="recv_04",
        name="Dest",
        category=ReceiverCategory.HOSPITAL_OR_CLINIC,
        capacity_kg=100.0,
        accepts_temperature_min_c=2.0,
        accepts_temperature_max_c=8.0,
        distance_km=10.0,
    )
    with pytest.raises(ValueError, match="Speed must be positive"):
        provider.calculate_route(origin, destination, average_speed_kmh=-10.0)

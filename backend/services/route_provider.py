"""
ColdRescue Route Estimation and Provider Service.

Provides distance and transit-time estimations between incident origins
and candidate receiving facilities.

Features:
  - Deterministic Haversine local calculation with road curvature multiplier (1.3x)
  - Clear labeling of fallback / heuristic estimates vs live routing
  - Provider interface abstraction for future map provider plug-ins
  - Robust handling of missing coordinates and invalid inputs
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.models.domain import Location, ReceiverNode


class WaypointCoordinate(BaseModel):
    label: str
    latitude: float
    longitude: float
    eta_min: Optional[float] = None


class RouteEstimate(BaseModel):
    origin_id: str
    destination_id: str
    distance_km: float
    travel_time_min: float
    average_speed_kmh: float
    provider_name: str
    is_fallback: bool
    confidence: float
    waypoints: List[WaypointCoordinate] = Field(default_factory=list)
    notes: Optional[str] = None


class RouteProvider(ABC):
    """Abstract interface for route estimation services."""

    @abstractmethod
    def calculate_route(
        self,
        origin: Location,
        destination: ReceiverNode,
        average_speed_kmh: float = 50.0,
    ) -> RouteEstimate:
        """Calculate or estimate route metrics between origin and destination."""
        pass


class LocalHaversineRouteProvider(RouteProvider):
    """
    Deterministic local fallback route provider.

    Uses spherical Haversine formula with a 1.30x road-network winding factor
    and urban/regional transit speeds.
    """

    EARTH_RADIUS_KM: float = 6371.0
    ROAD_CIRCUITY_FACTOR: float = 1.30  # Real-world road distance ~ 30% longer than straight-line

    def __init__(self, default_speed_kmh: float = 45.0) -> None:
        self.default_speed_kmh = default_speed_kmh

    @classmethod
    def haversine_distance_km(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Compute great-circle distance between two GPS coordinates in kilometers."""
        # Validate coordinate boundaries
        if not (-90.0 <= lat1 <= 90.0 and -90.0 <= lat2 <= 90.0):
            raise ValueError(f"Latitude must be between -90 and 90. Got ({lat1}, {lat2}).")
        if not (-180.0 <= lon1 <= 180.0 and -180.0 <= lon2 <= 180.0):
            raise ValueError(f"Longitude must be between -180 and 180. Got ({lon1}, {lon2}).")

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_KM * c

    def calculate_route(
        self,
        origin: Location,
        destination: ReceiverNode,
        average_speed_kmh: Optional[float] = None,
    ) -> RouteEstimate:
        """Estimate route using coordinates or pre-defined receiver distance."""
        speed = average_speed_kmh or self.default_speed_kmh
        if speed <= 0:
            raise ValueError(f"Speed must be positive. Got {speed} km/h.")

        # Case 1: Both coordinates available
        if (
            origin.latitude is not None
            and origin.longitude is not None
            and destination.latitude is not None
            and destination.longitude is not None
        ):
            straight_line = self.haversine_distance_km(
                origin.latitude,
                origin.longitude,
                destination.latitude,
                destination.longitude,
            )
            estimated_road_dist = round(straight_line * self.ROAD_CIRCUITY_FACTOR, 2)
            time_hours = estimated_road_dist / speed
            travel_time_min = round(time_hours * 60.0, 1)

            waypoints = [
                WaypointCoordinate(
                    label=f"Origin: {origin.name}",
                    latitude=origin.latitude,
                    longitude=origin.longitude,
                    eta_min=0.0,
                ),
                WaypointCoordinate(
                    label=f"Destination: {destination.name}",
                    latitude=destination.latitude,
                    longitude=destination.longitude,
                    eta_min=travel_time_min,
                ),
            ]

            return RouteEstimate(
                origin_id=origin.location_id,
                destination_id=destination.receiver_id,
                distance_km=estimated_road_dist,
                travel_time_min=travel_time_min,
                average_speed_kmh=speed,
                provider_name="local_haversine_fallback",
                is_fallback=True,
                confidence=0.85,
                waypoints=waypoints,
                notes=(
                    f"Estimated via Haversine distance ({straight_line:.2f} km straight-line x "
                    f"{self.ROAD_CIRCUITY_FACTOR} circuity) @ {speed} km/h."
                ),
            )

        # Case 2: Pre-populated distance_km on destination
        if destination.distance_km is not None:
            dist = destination.distance_km
            time_min = (
                destination.travel_time_min
                if destination.travel_time_min is not None
                else round((dist / speed) * 60.0, 1)
            )
            return RouteEstimate(
                origin_id=origin.location_id,
                destination_id=destination.receiver_id,
                distance_km=dist,
                travel_time_min=time_min,
                average_speed_kmh=speed,
                provider_name="preconfigured_distance_fallback",
                is_fallback=True,
                confidence=0.75,
                notes="Using preconfigured destination distance.",
            )

        # Case 3: Incomplete data fallback (default safety assumption)
        default_dist = 25.0
        default_time = round((default_dist / speed) * 60.0, 1)
        return RouteEstimate(
            origin_id=origin.location_id,
            destination_id=destination.receiver_id,
            distance_km=default_dist,
            travel_time_min=default_time,
            average_speed_kmh=speed,
            provider_name="default_fallback",
            is_fallback=True,
            confidence=0.30,
            notes="Missing origin/destination coordinates; fallback estimate applied.",
        )

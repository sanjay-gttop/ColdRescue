"""
ColdRescue ECS Fargate Continuous Telemetry Emitter (Milestone 14).
Runs cold-chain power failure simulations and publishes events to ColdRescue Ingestion.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict

import requests

from simulator.engine import run_simulation, SimulationResult
from simulator.scenario import AVAILABLE_SCENARIOS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("coldrescue.telemetry_emitter")


def emit_events(
    api_url: str,
    scenario_name: str = "REEFER_UNIT_FAILURE",
    seed: int = 42,
    interval_sec: float = 60.0,
    burst_count: int = 1,
) -> None:
    """Continuously run simulations and post events to the ColdRescue ingestion endpoint."""
    logger.info(
        f"Starting Telemetry Emitter: scenario={scenario_name}, seed={seed}, "
        f"api_url={api_url}, interval={interval_sec}s, burst={burst_count}"
    )

    iteration = 0

    while True:
        iteration += 1
        current_seed = seed + iteration
        logger.info(f"Running simulation iteration #{iteration} (seed={current_seed})...")

        try:
            # Run simulation
            sim_result = run_simulation(scenario_name=scenario_name, seed=current_seed)
            report = sim_result.to_report()

            # Formulate ingestion payload
            payload = {
                "event_id": f"sim_evt_{int(time.time())}_{iteration}",
                "event_type": "incident",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0.0",
                "correlation_id": f"sim_corr_{iteration}",
                "idempotency_key": f"sim_idem_{iteration}_{current_seed}",
                "sequence_number": iteration,
                "incident_type": "REEFER_UNIT_FAILURE",
                "status": "OPEN",
                "location_id": "loc_sim_depot",
                "location_name": "Tamil Nadu Cold Chain Depot",
                "reported_by": "fargate_telemetry_simulator",
                "cooling_status": "failed",
                "cargo": {
                    "cargo_id": f"cargo_sim_{iteration}",
                    "description": "Tamil Nadu Pasteurized Milk",
                    "cargo_type": "dairy",
                    "mass_kg": 500.0,
                    "current_temperature_c": sim_result.final_temp_c,
                    "ambient_temperature_c": 32.0,
                    "safe_temperature_min_c": 2.0,
                    "safe_temperature_max_c": 8.0,
                    "backup_runtime_min": 45.0,
                },
                "receivers": [
                    {
                        "receiver_id": "recv_salem_hub",
                        "name": "Salem Cold Distribution",
                        "category": "COLD_STORAGE_FACILITY",
                        "capacity_kg": 2500.0,
                        "accepts_temp_min_c": 0.0,
                        "accepts_temp_max_c": 8.0,
                        "distance_km": 12.0,
                        "cooling_status": "operational",
                        "backup_runtime_min": 180.0,
                    }
                ],
            }

            headers = {"Content-Type": "application/json"}
            target_endpoint = f"{api_url.rstrip('/')}/api/v1/events"
            logger.info(f"Emitting telemetry to {target_endpoint}...")

            res = requests.post(target_endpoint, json=payload, headers=headers, timeout=10)
            logger.info(f"Response [{res.status_code}]: {res.text}")

        except Exception as exc:
            logger.error(f"Error during simulation emission: {exc}")

        if burst_count > 0 and iteration >= burst_count:
            logger.info(f"Burst run completed ({iteration} iterations). Exiting.")
            break

        time.sleep(interval_sec)


def main() -> None:
    parser = argparse.ArgumentParser(description="ColdRescue ECS Fargate Telemetry Emitter")
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("COLDRESCUE_API_URL", "http://localhost:8000"),
        help="Target backend API base URL",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="tamil_nadu_dairy_grid_outage",
        help="Simulation scenario name",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--interval", type=float, default=60.0, help="Interval between events (s)")
    parser.add_argument("--burst", type=int, default=1, help="Number of iterations (0 for infinite)")

    args = parser.parse_args()
    emit_events(
        api_url=args.api_url,
        scenario_name=args.scenario,
        seed=args.seed,
        interval_sec=args.interval,
        burst_count=args.burst,
    )


if __name__ == "__main__":
    main()

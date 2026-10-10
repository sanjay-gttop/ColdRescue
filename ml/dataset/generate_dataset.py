"""
ColdRescue ML Synthetic Dataset Generator.

Generates reproducible synthetic thermal degradation datasets for training
and evaluating remaining safe time prediction models.
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import List, Dict, Any


def generate_synthetic_dataset(
    output_path: Path,
    num_samples: int = 1000,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    records = []

    cargo_types = ["dairy", "perishable_food", "temperature_sensitive_supplies", "frozen_goods"]
    cooling_statuses = ["active", "degraded", "failed"]

    for i in range(num_samples):
        cargo = rng.choice(cargo_types)
        cooling = rng.choice(cooling_statuses)
        ambient_temp = round(rng.uniform(15.0, 42.0), 2)

        if cargo == "frozen_goods":
            current_temp = round(rng.uniform(-22.0, -14.0), 2)
            safe_limit = -12.0
            k_base = 0.003
        elif cargo == "dairy":
            current_temp = round(rng.uniform(2.0, 7.0), 2)
            safe_limit = 8.0
            k_base = 0.007
        elif cargo == "perishable_food":
            current_temp = round(rng.uniform(1.0, 5.0), 2)
            safe_limit = 6.0
            k_base = 0.005
        else:
            current_temp = round(rng.uniform(2.0, 6.0), 2)
            safe_limit = 8.0
            k_base = 0.004

        thermal_resistance = round(rng.uniform(0.7, 1.8), 2)
        mass_kg = round(rng.uniform(100.0, 4000.0), 1)
        backup_runtime = round(rng.uniform(0.0, 180.0), 1) if cooling != "failed" else 0.0
        door_open_count = rng.randint(0, 4)

        # Simplified physics simulation target calculation
        temp = current_temp
        minutes = 0.0
        step_min = 1.0
        effective_k = (k_base / thermal_resistance) * (1.0 if cooling == "failed" else 0.4 if cooling == "degraded" else 0.05)

        # Run until breach or max horizon
        while temp < safe_limit and minutes < 720.0:
            if minutes < backup_runtime and cooling != "failed":
                # Active backup slows down warming
                temp += effective_k * 0.1 * (ambient_temp - temp) * step_min
            else:
                temp += effective_k * (ambient_temp - temp) * step_min

            minutes += step_min

        breach_minutes = round(minutes, 1)

        records.append({
            "sample_id": f"sample_{i:05d}",
            "cargo_type": cargo,
            "cooling_status": cooling,
            "current_temp_c": current_temp,
            "ambient_temp_c": ambient_temp,
            "safe_limit_c": safe_limit,
            "mass_kg": mass_kg,
            "thermal_resistance": thermal_resistance,
            "backup_runtime_min": backup_runtime,
            "door_open_count": door_open_count,
            "breach_minutes": breach_minutes,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    return records


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "dataset.csv"
    data = generate_synthetic_dataset(out)
    print(f"Generated {len(data)} synthetic samples to {out}")

# ColdRescue Milestone 18 — Stress Benchmark Report
**Benchmark Date:** 2026-10-11T14:10:41.315792+00:00
**Total Scenarios Evaluated:** 20

## Executive Summary
| Metric | Greedy Solver | Global Solver | Advantage |
|---|---|---|---|
| **Total Cargo Diverted (kg)** | 37,873.5 kg | **37,649.8 kg** | **+-223.7 kg (-0.59%)** |
| **Solver Win Rate** | 1 (1%) | **1 (5.0%)** | **+0 wins** |
| **Ties (Identical Optimal)** | - | 18 (90.0%) | - |
| **Avg Decision Time** | 43.78 ms | 65.67 ms | Fast sub-second |
| **Energy/Safety Violations** | 0 | **0 (Strict deterministic block)** | Pass |

## Environmental Impact (Track 03: Waste and Energy)
- **Primary Metric (Cargo Diverted):** **37,649.8 kg** kept out of simulated spoilage.
- **Illustrative Embedded Emissions Avoided:** **90,359.5 kg CO2e**
  *(Based on Tamil Nadu dairy emissions factor of 2.4 kg CO2e / kg milk. Illustrative estimate based on stated simulation assumptions, not measured real-world savings).*

## Scenario Breakdown (First 10 of 20)
| Scenario | Incidents | Receivers | Cargo (kg) | Greedy Div. (kg) | Global Div. (kg) | Outcome | Runtime (ms) |
|---|---|---|---|---|---|---|---|
| scenario_001 | 2 | 6 | 1500.1 | 1500.1 | 1500.1 | TIE | 99.87 |
| scenario_002 | 3 | 2 | 4236.2 | 1376.2 | 1376.2 | TIE | 63.39 |
| scenario_003 | 5 | 2 | 5640.0 | 4205.6 | 4209.9 | GLOBAL_WIN | 68.91 |
| scenario_004 | 2 | 6 | 1954.5 | 1954.5 | 1954.5 | TIE | 76.24 |
| scenario_005 | 1 | 6 | 203.6 | 0 | 0 | TIE | 78.14 |
| scenario_006 | 5 | 5 | 4084.3 | 3357.7 | 3357.7 | TIE | 227.75 |
| scenario_007 | 5 | 6 | 3427.1 | 2234.4 | 2234.4 | TIE | 272.36 |
| scenario_008 | 3 | 4 | 4254.6 | 1581.2 | 1581.2 | TIE | 103.3 |
| scenario_009 | 3 | 2 | 1548.1 | 545.4 | 545.4 | TIE | 77.14 |
| scenario_010 | 5 | 4 | 3968.5 | 3301.6 | 3301.6 | TIE | 161.01 |

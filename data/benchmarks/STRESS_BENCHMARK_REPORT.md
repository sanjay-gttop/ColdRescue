# ColdRescue Milestone 18 — Stress Benchmark Report
**Benchmark Date:** 2026-10-11T04:37:33.521041+00:00
**Total Scenarios Evaluated:** 50

## Executive Summary
| Metric | Greedy Solver | Global Solver | Advantage |
|---|---|---|---|
| **Total Cargo Diverted (kg)** | 5,704.8 kg | **6,180.6 kg** | **+475.8 kg (8.34%)** |
| **Solver Win Rate** | 0 (0%) | **1 (2.0%)** | **+1 wins** |
| **Ties (Identical Optimal)** | - | 49 (98.0%) | - |
| **Avg Decision Time** | 71.97 ms | 107.95 ms | Fast sub-second |
| **Energy/Safety Violations** | 0 | **0 (Strict deterministic block)** | Pass |

## Environmental Impact (Track 03: Waste and Energy)
- **Primary Metric (Cargo Diverted):** **6,180.6 kg** kept out of simulated spoilage.
- **Illustrative Embedded Emissions Avoided:** **14,833.4 kg CO2e**
  *(Based on Tamil Nadu dairy emissions factor of 2.4 kg CO2e / kg milk. Illustrative estimate based on stated simulation assumptions, not measured real-world savings).*

## Scenario Breakdown (First 10 of 50)
| Scenario | Incidents | Receivers | Cargo (kg) | Greedy Div. (kg) | Global Div. (kg) | Outcome | Runtime (ms) |
|---|---|---|---|---|---|---|---|
| contention_001 | 5 | 3 | 5116.5 | 0 | 0 | TIE | 139.68 |
| contention_002 | 3 | 4 | 3830.5 | 0 | 0 | TIE | 0.47 |
| contention_003 | 3 | 3 | 2957.0 | 0 | 0 | TIE | 39.55 |
| contention_004 | 6 | 3 | 5416.2 | 0 | 0 | TIE | 247.36 |
| contention_005 | 3 | 3 | 3711.7 | 0 | 0 | TIE | 0.08 |
| contention_006 | 5 | 3 | 6218.4 | 0 | 0 | TIE | 115.4 |
| contention_007 | 3 | 4 | 4071.6 | 0 | 0 | TIE | 0.1 |
| contention_008 | 4 | 4 | 4071.1 | 0 | 0 | TIE | 0.1 |
| contention_009 | 6 | 3 | 6712.3 | 0 | 0 | TIE | 326.6 |
| contention_010 | 3 | 4 | 3340.0 | 0 | 0 | TIE | 0.09 |

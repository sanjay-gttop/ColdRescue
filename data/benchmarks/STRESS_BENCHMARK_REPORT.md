# ColdRescue Milestone 18 — Stress Benchmark Report
**Benchmark Date:** 2026-10-11T08:23:11.426549+00:00
**Total Scenarios Evaluated:** 50

## Executive Summary
| Metric | Greedy Solver | Global Solver | Advantage |
|---|---|---|---|
| **Total Cargo Diverted (kg)** | 56,190.4 kg | **56,190.4 kg** | **+0.0 kg (0.0%)** |
| **Solver Win Rate** | 0 (0%) | **0 (0.0%)** | **+0 wins** |
| **Ties (Identical Optimal)** | - | 50 (100.0%) | - |
| **Avg Decision Time** | 191.66 ms | 287.49 ms | Fast sub-second |
| **Energy/Safety Violations** | 0 | **0 (Strict deterministic block)** | Pass |

## Environmental Impact (Track 03: Waste and Energy)
- **Primary Metric (Cargo Diverted):** **56,190.4 kg** kept out of simulated spoilage.
- **Illustrative Embedded Emissions Avoided:** **134,857.0 kg CO2e**
  *(Based on Tamil Nadu dairy emissions factor of 2.4 kg CO2e / kg milk. Illustrative estimate based on stated simulation assumptions, not measured real-world savings).*

## Scenario Breakdown (First 10 of 50)
| Scenario | Incidents | Receivers | Cargo (kg) | Greedy Div. (kg) | Global Div. (kg) | Outcome | Runtime (ms) |
|---|---|---|---|---|---|---|---|
| scenario_001 | 3 | 4 | 2985.4 | 1478.2 | 1478.2 | TIE | 210.22 |
| scenario_002 | 5 | 6 | 4668.4 | 1635.1 | 1635.1 | TIE | 459.27 |
| scenario_003 | 4 | 6 | 3988.2 | 0 | 0 | TIE | 697.4 |
| scenario_004 | 1 | 2 | 992.2 | 0 | 0 | TIE | 95.85 |
| scenario_005 | 2 | 5 | 2259.8 | 0 | 0 | TIE | 391.57 |
| scenario_006 | 5 | 2 | 5448.7 | 3077.1 | 3077.1 | TIE | 211.43 |
| scenario_007 | 4 | 2 | 5736.3 | 0 | 0 | TIE | 1.09 |
| scenario_008 | 3 | 5 | 3282.8 | 2469.6 | 2469.6 | TIE | 539.75 |
| scenario_009 | 3 | 3 | 2937.1 | 2127.0 | 2127.0 | TIE | 311.93 |
| scenario_010 | 5 | 2 | 3553.7 | 229.0 | 229.0 | TIE | 530.5 |

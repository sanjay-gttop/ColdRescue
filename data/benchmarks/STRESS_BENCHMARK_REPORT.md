# ColdRescue Milestone 18 — Stress Benchmark Report
**Benchmark Date:** 2026-10-10T19:47:10.733753+00:00
**Total Scenarios Evaluated:** 50

## Executive Summary
| Metric | Greedy Solver | Global Solver | Advantage |
|---|---|---|---|
| **Total Cargo Diverted (kg)** | 75,449.3 kg | **75,763.6 kg** | **+314.3 kg (0.42%)** |
| **Solver Win Rate** | 1 (1%) | **1 (2.0%)** | **+0 wins** |
| **Ties (Identical Optimal)** | - | 48 (96.0%) | - |
| **Avg Decision Time** | 99.61 ms | 149.42 ms | Fast sub-second |
| **Energy/Safety Violations** | 0 | **0 (Strict deterministic block)** | Pass |

## Environmental Impact (Track 03: Waste and Energy)
- **Primary Metric (Cargo Diverted):** **75,763.6 kg** kept out of simulated spoilage.
- **Illustrative Embedded Emissions Avoided:** **181,832.6 kg CO2e**
  *(Based on Tamil Nadu dairy emissions factor of 2.4 kg CO2e / kg milk. Illustrative estimate based on stated simulation assumptions, not measured real-world savings).*

## Scenario Breakdown (First 10 of 50)
| Scenario | Incidents | Receivers | Cargo (kg) | Greedy Div. (kg) | Global Div. (kg) | Outcome | Runtime (ms) |
|---|---|---|---|---|---|---|---|
| scenario_001 | 1 | 2 | 518.3 | 0 | 0 | TIE | 28.0 |
| scenario_002 | 5 | 5 | 4168.8 | 3256.8 | 3256.8 | TIE | 238.66 |
| scenario_003 | 1 | 6 | 1353.1 | 1353.1 | 1353.1 | TIE | 31.69 |
| scenario_004 | 2 | 6 | 1984.8 | 414.0 | 414.0 | TIE | 105.36 |
| scenario_005 | 5 | 4 | 4345.4 | 2662.4 | 2662.4 | TIE | 163.33 |
| scenario_006 | 5 | 3 | 6128.0 | 2294.4 | 2294.4 | TIE | 124.07 |
| scenario_007 | 2 | 3 | 1294.6 | 381.3 | 381.3 | TIE | 66.15 |
| scenario_008 | 3 | 5 | 3704.6 | 3065.0 | 3065.0 | TIE | 161.7 |
| scenario_009 | 3 | 3 | 2473.8 | 543.8 | 543.8 | TIE | 76.13 |
| scenario_010 | 5 | 6 | 4725.6 | 3495.2 | 3495.2 | TIE | 282.07 |

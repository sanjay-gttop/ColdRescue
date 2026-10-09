"""
ColdRescue Simulator Package — M2 Cold-Chain Power-Failure Simulator.

Usage:
    py -m simulator.engine --scenario REEFER_UNIT_FAILURE
    py -m simulator.engine --scenario WAREHOUSE_GRID_OUTAGE --seed 42
    py -m simulator.engine --list-scenarios

Components:
    enums        : IncidentType, PowerState, ReceiverCategory enums
    models       : CargoProfile, ReceiverProfile, SimulatedIncident
    thermal      : Newton-type linear thermal model (labelled estimate)
    state_machine: Power-state transitions with validation
    scenario     : Deterministic scenario generation by scenario_id + seed
    engine       : Main orchestration — runs and prints a full simulation
"""

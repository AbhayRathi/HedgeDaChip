# FPGA collateral

This directory is the bridge from simulation into implementation.

## Current contents

- `constraints/timing.xdc` provides the initial timing skeleton for the MVP clock and reset.
- `xilinx_vivado/` is reserved for the board-specific build scripts and project files that will be added in the FPGA-targeting phase.

## Intent

The current PR keeps the FPGA collateral lightweight but real: constraints exist, the directory is tracked, and later phases can add board part selection, top-level IO mapping, and timing-closure guidance without changing the RTL contracts already validated in simulation.

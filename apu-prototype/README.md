# APU Prototype

FPGA-first, ASIC-ready Agent Processing Unit prototype focused on a deterministic reflex path:

`host replay -> parser -> orderbook/features -> decision -> risk -> action encoder`

## Repository layout

- `docs/`: architecture, contracts, timing, verification, and roadmap
- `rtl/`: SystemVerilog packages, interfaces, and MVP modules
- `tb/`: cocotb tests
- `sw_golden/`: Python source-of-truth models
- `sim/`: Verilator and cocotb runners
- `fpga/`: placeholder FPGA integration directories

## Validation

```bash
python3 -m pip install -r tb/requirements.txt
./sim/verilator/run.sh
./sim/cocotb/run.sh
```

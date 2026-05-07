# MVP timing skeleton for the APU prototype
create_clock -name apu_clk -period 5.000 [get_ports clk]
set_input_delay -clock apu_clk 1.000 [get_ports {in_valid in_data[*] kill_switch stamp_ts spread_threshold[*] imbalance_threshold[*] max_orders_per_window[*]}]
set_output_delay -clock apu_clk 1.000 [get_ports {in_ready out_valid out_data[*] ingress_count[*] egress_count[*] stall_cycles[*] fifo_max_occupancy[*]}]

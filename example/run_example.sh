#!/bin/sh

python ../fpga_port2pin_mapper.py map connection.yaml b_1.yaml,[b_2_c_1.yaml,[b_2_c_2_f_1.yaml,b_2_c_2_f_2.yaml]] tmp.xdc

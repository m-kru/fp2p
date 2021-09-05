#!/bin/sh

../../fp2p.py assign tree.yaml assignment.yaml vivado > test.xdc
cmp golden.xdc test.xdc

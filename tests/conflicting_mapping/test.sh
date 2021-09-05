#!/bin/sh

../../fp2p.py assign tree.yaml assignment.yaml vivado 1> /dev/null 2> stderr
cmp stderr.golden stderr

#!/bin/sh

python ../../fp2p.py assign assignment.yaml tree.yaml tmp.xdc
cmp golden.xdc tmp.xdc

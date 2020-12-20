#!/bin/sh

python ../../fp2p.py assign tree.yaml assignment.yaml test.xdc
cmp golden.xdc test.xdc

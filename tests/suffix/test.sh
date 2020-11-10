#!/bin/sh

python ../../fp2p.py assign assignment.yaml tree.yaml test.xdc
cmp golden.xdc test.xdc

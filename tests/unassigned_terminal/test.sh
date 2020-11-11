#!/bin/sh

python ../../fp2p.py assign assignment.yaml tree.yaml test.xdc > test.stdout
cmp golden.stdout test.stdout

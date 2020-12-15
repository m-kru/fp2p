#!/bin/sh

python ../../fp2p.py assign tree.yaml assignment.yaml test.xdc > test.stdout
cmp golden.stdout test.stdout

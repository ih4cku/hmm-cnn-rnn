#!/bin/bash
set -e

./pipeline.py
(cd kaldi && ./run.sh)
utils/show_aligns.sh aligns 99

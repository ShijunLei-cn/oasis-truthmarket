#!/bin/bash
python example/run_rq1_experiment.py --runs 10 --rounds 10 --sellers 5 --buyers 5 --market-type reputation_only --output-dir experiments/rq1_wo

python example/run_rq1_experiment.py --runs 10 --rounds 10 --sellers 5 --buyers 5 --market-type reputation_and_warrant --output-dir experiments/rq1_rw

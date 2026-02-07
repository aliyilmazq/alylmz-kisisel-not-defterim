#!/bin/bash

cd "/Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim"

# Load credentials from run_local.sh (which is not in git)
if [ -f "./run_local.sh" ]; then
    # Extract APP_SECRET_KEY and GCP_CREDENTIALS
    eval "$(grep 'export APP_SECRET_KEY' ./run_local.sh)"
    eval "$(grep -A20 'export GCP_CREDENTIALS' ./run_local.sh | head -14)"
else
    echo "ERROR: run_local.sh not found. Please create it with APP_SECRET_KEY and GCP_CREDENTIALS."
    exit 1
fi

# 2 saniye sonra tarayiciyi ac
(sleep 2 && open "http://localhost:8510") &

uvicorn main:app --host 0.0.0.0 --port 8510

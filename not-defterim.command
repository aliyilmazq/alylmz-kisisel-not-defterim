#!/bin/bash

cd "/Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim"

# 2 saniye sonra tarayıcıyı aç
(sleep 2 && open "http://localhost:8510") &

streamlit run app.py --server.port 8510

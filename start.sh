#!/bin/bash

INTERVAL=3600  # 60 minutes

while true; do
    python main.py
    sleep $INTERVAL
done
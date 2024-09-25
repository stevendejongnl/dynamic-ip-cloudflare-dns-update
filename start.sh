#!/bin/bash

INTERVAL=300  # 5 minutes

while true; do
    python main.py
    sleep $INTERVAL
done
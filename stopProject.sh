#!/bin/bash

pids=$(sudo lsof -t -i :8000)

if [ -n "$pids" ]; then
  echo "Killing processes on port 8000: $pids"
  sudo kill $pids
else
  echo "No processes found on port 8000."
fi
echo "--=DONE=--"
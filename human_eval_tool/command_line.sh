#!/bin/bash

export PYTHONPATH=$PYTHONPATH:$(pwd)/server/
export MODEL_NAME=mt5

python $(pwd)/server/app.py

#!/bin/bash

export MODEL_NAME=mt5
export MODEL_TYPE=dst
export PYTHONPATH=$PYTHONPATH:$(pwd)


conda activate tod && celery -A human_eval_service.celery_worker.celery_app worker --loglevel info --pool=solo -Q ${MODEL_NAME}_${MODEL_TYPE}
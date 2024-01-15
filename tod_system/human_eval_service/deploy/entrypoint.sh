#!/bin/bash


celery -A human_eval_service.celery_worker.celery_app worker -l info --concurrency 1 --logfile /root/tod_system/logs/celery_worker.log -Q ${MODEL_NAME}_${MODEL_TYPE}
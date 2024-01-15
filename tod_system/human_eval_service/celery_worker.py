# -*- coding: utf-8 -*-
"""
Celery Worker Initialization and Configuration for the Model Server
(the dashed yellow rounded rectangles in the Figure 3 in the paper https://arxiv.org/pdf/2401.02208.pdf)

This script initializes and configures a Celery application for handling asynchronous task processing in a distributed environment.
It is specifically designed to work with a langauge models. The script sets up Celery workers, configures queues, and initialises a model for processing tasks.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

import configparser
from celery import Celery, signals
from human_eval_service.task_process import generate_output
from human_eval_service.model_loader import ModelLoader
from kombu import Queue
import os
from dotenv import load_dotenv
import logging

def make_celery(config_file_path):
    """
    Initializes and configures a Celery application based on the provided `config_file_path`.

    Args:
        config_file_path (str): The path to the configuration file.

    Returns:
        app (Celery): The configured Celery application.

    Raises:
        FileNotFoundError: If the `config_file_path` does not exist.
        configparser.Error: If there is an error parsing the configuration file.
    """
    print(config_file_path)
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file_path)
    redis_address = os.getenv('REDIS_ADDRESS', 'redis://localhost:6379/5')
    redis_password = os.getenv('REDIS_PASSWORD', 'redis://localhost:6379/6')
    CELERY_RESULT_BACKEND = f'redis://:{redis_password}@{redis_address}:6379/5'
    CELERY_BROKER_URL = f'redis://:{redis_password}@{redis_address}:6379/6'
    app_name = os.getenv('APP_NAME', "chatbot")
    app = Celery(app_name, backend=CELERY_RESULT_BACKEND, broker=CELERY_BROKER_URL)
    if os.getenv('system_type','microservice') == 'microservice':
        dst_queue = os.getenv('dst_model_id','mt5_dst')
        rg_queue = os.getenv('rg_model_id','mt5_rg')
        total_list = [dst_queue,rg_queue]
    else:
        e2e_queue = os.getenv('e2e_model_id','mt5_e2e')
        total_list = [e2e_queue]    
    app.conf.task_default_queue = total_list[0]
    app.conf.task_queues = tuple()
    for i in total_list:
        app.conf.task_queues += (Queue(i, routing_key=i),)
    app.conf.task_default_routing_key = total_list[0]
    app.conf.update(
        CELERY_REDIS_SOCKET_CONNECT_TIMEOUT = 5,
        CELERYD_CONCURRENCY = 1,
        CELERYD_MAX_TASKS_PER_CHILD = 1,
    )
    return app

load_dotenv()
config_path = os.getenv('MODEL_CONFIG_FILE_PATH', '/root/tod_system/human_eval_service/config/example_worker_rg.cfg')
celery_app = make_celery(config_path)
logging.info("celery worker init")
model_loader = None


@signals.worker_process_init.connect
def setup_model(signal, sender, **kwargs):
    """
    Set up the model for the worker process.
    If you are using your own model on the worker,
    you can set up your own ModelLoader in model_loader.py

    Parameters:
    - signal: The signal that triggered the setup.
    - sender: The sender of the signal.
    - **kwargs: Additional keyword arguments.

    Returns:
    None
    """
    global model_loader
    logging.info('begin to load model')
    model_loader = ModelLoader(config_path)


@celery_app.task(name='generate_text_task')
def generate_text_task(history):
    print(history)
    response = generate_output(history, model_loader)
    return response

if __name__ == '__main__':
    # config_file_path = ""
    import os
    
    config_file_path = os.getenv('MODEL_CONFIG_FILE_PATH', '/root/tod_system/human_eval_service/config/example_worker_rg.cfg')
    celery = make_celery(config_file_path)
    celery.worker_main(argv= ['worker','--loglevel=info','--concurrency=1','-Q', 'mt5_rg'])

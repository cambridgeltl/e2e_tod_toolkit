# -*- coding: utf-8 -*-
"""
Flask extensions and Celery Configuration for the Dialogue Evaluation Tool

This script is responsible for initializing Flask extensions. It sets up Bcrypt for password hashing, PyMongo for MongoDB interactions,
JWTManager for JWT-based authentication, and CORS for handling cross-origin requests.

Additionally, it includes the configuration of Celery for asynchronous task processing, supporting distributed task queues
with Redis as the broker and result backend. The configuration varies based on the system's architecture, supporting either
'microservice' or the traditional 'end2end' designs.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from flask_cors import CORS
import os
from celery import Celery
from kombu import Queue
import logging

bcrypt = Bcrypt()
pymongo = PyMongo()
jwt = JWTManager()
cors = CORS()

def make_celery(flask):
    """
    Configures and initializes a Celery application.

    Args:
        flask (Flask): The Flask application object to bind with Celery.

    Returns:
        Celery: The configured Celery object.
    """

    redis_address = os.getenv('REDIS_ADDRESS', 'localhost')
    redis_password = os.getenv('REDIS_PASSWORD', 'Humaneval12345')
    logging.info("redis addres is {}".format(redis_address))
    logging.info("redis password is {}".format(redis_password))
    CELERY_RESULT_BACKEND = f'redis://:{redis_password}@{redis_address}:6379/5'
    CELERY_BROKER_URL = f'redis://:{redis_password}@{redis_address}:6379/6'
    app_name = os.getenv('APP_NAME','human_eval_tool')
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
    
    class ContextTask(app.Task):
        def __call__(self, *args, **kwargs):
            with flask.app_context():
                return self.run(*args, **kwargs)
    
    app.Task = ContextTask
    return app

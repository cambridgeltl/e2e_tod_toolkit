# -*- coding: utf-8 -*-
"""
Task Environment Configuration

This script is designed for setting up and managing the task environment in a dialogue evaluation experiment. It includes
functionalities for initializing the task environment with specific configurations, retrieving random tasks, and providing
relevant information about the tasks such as their language and dataset.

Author: Songbo Hu and Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

import json
import logging
import random
import os

class TaskEnvironment:

    def __init__(self):
        """
        Initializes an instance of the class.

        Parameters:
            config_file_path (str): The path to the configuration file.

        Returns:
            None
        """
        self.task_dic = None
        
        current_path = os.path.abspath(os.path.dirname(__file__))
        config_path = current_path + "/config/test_goals.json"
        goal_path = os.getenv("TASK_PATH",config_path)

        with open(goal_path, "r", encoding="utf-8") as f:
            self.task_dic = json.load(f)
        assert self.task_dic

        self.language = os.getenv('TASK_LANGUAGE', 'English')
        self.dataset = os.getenv('TASK_DATASET', 'human_eval')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'admin@localhost')
        
        logging.info('This is the {} language system which is using {} dataset.'.format(self.language, self.dataset))

    def get_task(self):
        """
        Get a random task from the task dictionary.

        Returns:
            dict: A dictionary containing the randomly selected task with the following keys:
                - "task_id" (str): The ID of the task.
                - "task" (str): The task itself.
                - "language" (str): The language of the task.
                - "dataset" (str): The dataset of the task.
        """

        random_key = random.sample(self.task_dic.keys(), 1)[0]
        dial_task = self.task_dic[random_key]
        return {
            "task_id": random_key,
            "task" : dial_task,
            "language" : self.language,
            "dataset" : self.dataset
        }
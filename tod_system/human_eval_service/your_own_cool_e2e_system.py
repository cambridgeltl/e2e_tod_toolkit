# -*- coding: utf-8 -*-
"""
Example Dialogue System Interface

This is an example interface for building custom dialogue systems that can seamlessly integrate with our human evaluation tool.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License

"""




class CustomiseSystems:
    """
    This class defines a simple custom e2e system that can be used in the our service.
    If you want to build your own model and just use the human evaluation service tool, just implement this class.
    This class must have a method predict(self, history) which could bu used in the Celery worker process.
    Your system will automaticly deployed to the service during the celery worker start up or docekr start up,
    therefore, you have to make sure your model could be successfully loaded in the worker process.
    """
    def __init__(self):
        """
        Constructor for the class.
        If you have some initialization variables which have to be used in the model, please add them here.
        And don't forget to add them in the build_your_own_system function in the model_loader.py file.
        """
        pass
    def predict(self, history):
        """
        Predicts the response given a history of inputs.

        Args:
            history (list): A list of inputs. In the format [['history1', 'user'], ['history2', 'system'], ...]

        Returns:
            str: The predicted response.
        """
        response = None
        return response


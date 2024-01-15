# -*- coding: utf-8 -*-
"""
Dialogue System Output Generation

This script contains the `generate_output` function, which is essential for generating responses in a dialogue model/system.
The function operates by taking the conversation history and using either a DST model, a RG model, or an E2E model to generate
appropriate outputs.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License

"""

import logging
def generate_output(history, model_loader):
    """
    Generates output based on the input history using the DST model or the RG model.

    This function takes the conversation history (and the generated dialogue state) and uses the loaded model (either DST
    or RG) to generate a dialogue state (or a system response).
    
    We also provide a customized e2e prediction method here.

    Args:
        history: The input conversation history. This could be a single string or a tuple of strings, depending on the model type.
        model: The language model object.

    Returns:
        The generated response from the model. The format of the response depends on the model type. It can be a linearised dialogue state or a system response.
    """

    if model_loader.model_type == 'dst':
        logging.info(history)
        response = model_loader.model.predict(history)
        response = [history, response]
    elif model_loader.model_type == 'rg':
        logging.info(history)
        response = model_loader.model.predict(history[0],history[1])
    elif model_loader.model_type == 'e2e':
        response = model_loader.model.predict(history)
        # this part should be modified when you are going to use e2e model, which should be implemented by yourself.
    else:
        response = None
    return response

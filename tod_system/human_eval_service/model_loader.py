# -*- coding: utf-8 -*-
"""
Model Loader for the Model Server
(the dashed yellow rounded rectangles in the Figure 3 in the paper https://arxiv.org/pdf/2401.02208.pdf)

This script defines the ModelLoader class, which is responsible for loading and configuring dialogue state tracking (DST)
and response generation (RG) models for dialogue systems. The class supports multiple model types, including Huggingface, OpenAI, and LlamaCPP models.
It uses a configuration file to determine the model type and parameters.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

import os
import configparser
from agent.dst_models import FTHuggingfaceDSTModel, ICLOpenAIDSTModel, ICLLlamacppDSTModel, ICLHuggingfaceDSTModel
from agent.rg_models import ICLOpenAIRGModel, FTHuggingfaceRGModel, ICLLlamacppRGModel, ICLHuggingfaceRGModel
import logging
from human_eval_service.your_own_cool_e2e_system import CustomiseSystems

class ModelLoader:
    def __init__(self, config_file_path: str):
        self.model_path = config_file_path
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(self.model_path)
        self.system_server = os.getenv('MODEL_NAME', 'mt5')
        self.model_type = os.getenv('MODEL_TYPE', 'dst')
        logging.info(self.system_server)
        logging.info(self.model_type)
        self.model = self._load_model()


    def _load_model(self):
        """
        Load the appropriate model based on the given `model_type` and return it.

        Returns:
            model: The loaded model.
        
        Raises:
            ValueError: If an invalid `model_type` is provided.
        """
        if self.model_type == 'dst':
            model = self.load_dst_model(self.config)
        elif self.model_type == 'rg':
            model = self.load_rg_model(self.config)
        elif self.model_type =='e2e':
            model = self.build_your_own_system(self.config)
        else:
            raise ValueError('no model type fund')
        return model

    def load_dst_model(self, config):
        agent_type = config["experiment"]["agent_type"]
        assert agent_type in ["openai", "huggingface", "llamacpp", "iclhuggingface"]

        # These models are stateless.
        dst_model = None
        if agent_type == "huggingface":
            dst_model = FTHuggingfaceDSTModel(config)
        elif agent_type == "openai":
            dst_model = ICLOpenAIDSTModel(config)
        elif agent_type == "llamacpp":
            dst_model = ICLLlamacppDSTModel(config)
        elif agent_type == "iclhuggingface":
            dst_model = ICLHuggingfaceDSTModel(config)
        return dst_model

    def load_rg_model(self, config):
        agent_type = config["experiment"]["agent_type"]
        assert agent_type in ["openai", "huggingface", "llamacpp", "iclhuggingface"]

        # These models are stateless.
        rg_model = None
        if agent_type == "huggingface":
            rg_model = FTHuggingfaceRGModel(config)
        elif agent_type == "openai":
            rg_model = ICLOpenAIRGModel(config)
        elif agent_type == "llamacpp":
            rg_model = ICLLlamacppRGModel(config)
        elif agent_type == "iclhuggingface":
            rg_model = ICLHuggingfaceRGModel(config)
        return rg_model
    
    
    def build_your_own_system(self, config):
        # If you really want to use e2e model, please implement the CustomiseSystems class
        # if you have some initialization input variables for your own system, 
        # don't forget to add them here.
        # The predict method in CustomiseSystems will be called in the generate_output function in task_process.py
        model = CustomiseSystems()
        return model
    
        

if __name__ == '__main__':
    config_file_path = "config/example_mac_openai_ar.cfg"
    model_loader = ModelLoader(config_file_path)
    print(model_loader.model)
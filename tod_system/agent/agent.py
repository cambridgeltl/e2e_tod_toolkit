# -*- coding: utf-8 -*-
"""
MultiWOZ Dialogue Agent

This script implements a dialogue agent for the MultiWOZ dataset. The agent is capable of conversing with users, generating responses based on user input, and maintaining the history of the conversation.

Each sub models of the agent can be instantiated with any models implemented in agent/dst_models.py and agent/rg_models.py.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""
import argparse
import configparser
import torch

from dst_models import FTHuggingfaceDSTModel, ICLOpenAIDSTModel, ICLLlamacppDSTModel, ICLHuggingfaceDSTModel
from rg_models import FTHuggingfaceRGModel, ICLOpenAIRGModel, ICLLlamacppRGModel, ICLHuggingfaceRGModel
from dataset.database import MultiWOZDatabase

device = "cuda" if torch.cuda.is_available() else "cpu"


class Agent():
    """
    Base class for dialogue agents.

    Defines the interface for a dialogue agent. Subclasses should implement the chat method to process user utterances.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def chat(self, utterance):
        raise NotImplementedError()

class MultiWOZAgent(Agent):
    """
    Dialogue agent for the MultiWOZ dataset.

    This agent converses using models for DST and RG.
    """

    def __init__(self, config):
        super().__init__()
        self.reset()
        self.database = MultiWOZDatabase(config)
        self.agent_type = config["experiment"]["agent_type"]
        assert self.agent_type in ["fthuggingface", "iclopenai", "iclllamacpp", "iclhuggingface"]

        # These models are stateless.
        if self.agent_type == "fthuggingface":
            self.dst_model = FTHuggingfaceDSTModel(config)
            self.rg_model = FTHuggingfaceRGModel(config)
        elif self.agent_type == "iclopenai":
            self.dst_model = ICLOpenAIDSTModel(config)
            self.rg_model = ICLOpenAIRGModel(config)
        elif self.agent_type == "iclllamacpp":
            self.dst_model = ICLLlamacppDSTModel(config)
            self.rg_model = ICLLlamacppRGModel(config)
        elif self.agent_type == "iclhuggingface":
            self.dst_model = ICLHuggingfaceDSTModel(config)
            self.rg_model = ICLHuggingfaceRGModel(config)

        self.conversation_history = []

    def reset(self):
        self.conversation_history = []

    def chat(self, utterance):
        self.conversation_history.append((utterance, "user"))
        state = self.dst_model.predict(self.conversation_history)
        response = self.rg_model.predict(self.conversation_history, state)
        self.conversation_history.append((response["utt_lex"], "system"))
        return response["utt_lex"]

    def start_a_chat(self):
        print("The system is ready. Please say `bye` or `exit` to end the conversation.")
        while (True):
            string = str(input())
            if string.lower() in ["exit", "bye"]:
                break
            reply = agent.chat(string)
            print(reply)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Config Loader")
    parser.add_argument("-C","-c", "--config", help="set config file", required=True, type=argparse.FileType('r'))
    args = parser.parse_args()
    config_file_path = args.config.name
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file_path)
    agent = MultiWOZAgent(config)
    agent.start_a_chat()
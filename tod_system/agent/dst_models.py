# -*- coding: utf-8 -*-
"""
Multilingual Dialogue State Tracking (DST) Model as a Server

This script evaluates dialogue state tracking models for multilingual dialogue systems. It supports various model architectures
like fine-tuned Huggingface models,  Huggingface models with in-context learning, OpenAI's GPT models with in-context learning,
llama.cpp models with in-context learning. All the models follow the defined API which takes the dialogue history as input
and response the dialogue state summarising the dialogue.

All models are implemented as stateless machine learning models waiting for queries from the dialogue system agents.
We intend to follow the Microservices architecture.

Author: Songbo Hu and Zhangdie Yuan
Date: 20 November 2023
License: MIT License
"""

import json
import random

from openai import OpenAI

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
from llama_cpp import Llama
import torch
import time

from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
from dataset.utils import from_string_to_state, categorical_value_mapping, multiwoz_domains, multiwoz_slots, \
    state_json_formatter

device = "cuda" if torch.cuda.is_available() else "cpu"

class DSTModel():
    """
    Base class for Dialogue State Tracking models.
    This class provides a common interface for different DST model types. Each model type should implement the predict method.
    All the models are stateless.
    """
    def __init__(self):
        pass

    def predict(self, history):
        raise NotImplementedError()

class FTHuggingfaceDSTModel(DSTModel):
    """
    Fine-tuned Huggingface model for DST.

    This model predicts the dialogue state based on the conversation history using a sequence-to-sequence architecture.
    """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.model_path = config["experiment"]["dst_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.generation_max_length = int(config["experiment"]["generation_max_length"])
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path).to(device)

    def predict(self, history):

        prefix = "dialogue state tracking"
        context = []
        for (utt, speaker) in history:
            assert speaker.lower() in ["user", "system"]
            if speaker.lower() == "user":
                context.append(" User: " + utt)
            else:
                context.append(" System: " + utt)

        context_text = "".join(context[-(self.context_window - 1):])[-self.max_context_char_length:]
        inputs = prefix + " : " + context_text

        model_inputs = self.tokenizer([inputs], return_tensors="pt").to(device)

        generated_ids = self.model.generate(**model_inputs,  max_new_tokens=self.generation_max_length)

        output = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)[0]

        state = from_string_to_state(output)

        return state




class ICLOpenAIDSTModel(DSTModel):
    """
    In-context learning-based OpenAI's GPT model for DST.

    This model uses OpenAI's GPT models to predict the dialogue state based on conversation history.
    """

    def __init__(self, config):

        super().__init__()
        self.config = config
        self.model_path = config["experiment"]["dst_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.language = config["experiment"]["language"].lower()
        self.dataset = MultilingualMultiWoZDataset(config)
        self.model_name = config["experiment"]["dst_model_path"]
        self.number_training_example = int(config["experiment"]["num_of_example"])
        self.training_data = list(self.dataset.load_data(task="dst")["train"])
        self.client = OpenAI(api_key=config["experiment"]["openai_key"])


    def get_random_incontext_learning_examples(self, num_of_exmaples):
        sampled_examples = random.sample(self.training_data, num_of_exmaples)

        return " ".join(map(lambda x : "Example Input: " + x["source"] + " Example Output: " + str(x["state"]) , sampled_examples))


    def get_instruction_prompt(self):

        instruction = "Following the instructions, predict the belief state based on the history."

        train_example_instruction = "The following are some examples of input and expected output pairs. " + \
                                    self.get_random_incontext_learning_examples(self.number_training_example)

        output_format_instruction = "The predicted output should be in JSON format. The output should be in the format of {domain : { slot : value }}. Please note that there may be one or multiple domains in a dialogue."

        ontology_instruction = "domain should be in one of the following values: " + str(multiwoz_domains) + ". Please do not output a domain if it is not mentioned in the dialogue."
        ontology_instruction = ontology_instruction + " The slot can be one of the following values: " + str(multiwoz_slots) + ". Please do not output a slot if it is not mentioned in the dialogue or the user does not care about the value of the slot."

        categorical_slot_instruction = "There are " + str(len(categorical_value_mapping)) +  " categorical slots, which the values of these slots are from a closed set."
        for slot, values in categorical_value_mapping.items():
            categorical_slot_instruction = categorical_slot_instruction + " Slot " + slot + " can be any value from: " + str(values) + "."

        time_slot_instruction = "The leaveat, arriveby, and booktime slots are about time. The values for these slots should use the 24 hour clock and the format of hh:mm."
        number_slot_instruction = "The bookstay and bookpeople slots have the values of an integer number."

        instruction_input = instruction + " " + train_example_instruction + " " + output_format_instruction + " " + ontology_instruction + " " +\
                            categorical_slot_instruction + " " + time_slot_instruction + " " + number_slot_instruction

        return instruction_input

    def get_context_prompt(self, history):
        context = []
        for (utt, speaker) in history:
            assert speaker.lower() in ["user", "system"]
            if speaker.lower() == "user":
                context.append(" User: " + utt)
            else:
                context.append(" System: " + utt)

        context_text = "".join(context[-(self.context_window - 1):])[-self.max_context_char_length:]
        return context_text


    def predict(self, history):

        dialogue_input = self.get_context_prompt(history)

        instruction_input = self.get_instruction_prompt()

        try_counter = 0

        while try_counter < 50:
            try:
                try_counter += 1
                response = self.client.chat.completions.create(model=self.model_name,
                messages=[
                    {"role": "system", "content": instruction_input},
                    {"role": "user", "content": dialogue_input},
                ])
                state = response.choices[0].message.content

                state = state_json_formatter(state)
                return state
            except Exception as e:
                print("DST Fail " +  str(try_counter) + " times.")
                print(e)
                time.sleep(1)
                continue

        raise Exception("Failed to get results from OpenAI.")




class ICLLlamacppDSTModel(DSTModel):
    """
    Llama.cpp model for DST.

    This model leverages the llama.cpp library for on device LLM inference.
    """
    def __init__(self, config):

        super().__init__()
        self.config = config
        self.model_path = config["experiment"]["dst_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.language = config["experiment"]["language"].lower()
        self.dataset = MultilingualMultiWoZDataset(config)
        self.model_name = config["experiment"]["dst_model_path"]
        self.gpu_layers = int(config["experiment"]["gpu_layers"])
        self.main_gpu = int(config["experiment"]["main_gpu"])
        self.max_tokens = int(config["experiment"]["generation_max_length"])
        self.chat_format = config["experiment"]["chat_format"]
        
        self.model = Llama(model_path=self.model_path,
                           n_ctx=self.context_window,
                           n_gpu_layers=self.gpu_layers,
                           main_gpu=self.main_gpu,
                           chat_format=self.chat_format)
        self.number_training_example = int(config["experiment"]["num_of_example"])

        self.training_data = list(self.dataset.load_data(task="dst")["train"])


    def get_random_incontext_learning_examples(self, num_of_exmaples):
        sampled_examples = random.sample(self.training_data, num_of_exmaples)

        return " ".join(map(lambda x : "Example Input: " + x["source"] + " Example Output: " + str(x["state"]) , sampled_examples))

    def get_instruction_prompt(self):

        instruction = "Following the instructions, predict the belief state based on the history."

        train_example_instruction = "The following are some examples of input and expected output pairs. " + \
                                    self.get_random_incontext_learning_examples(self.number_training_example)

        output_format_instruction = "The predicted output should be in JSON format. The output should be in the format of {domain : { slot : value }}. Please note that there may be one or multiple domains in a dialogue."

        ontology_instruction = "domain should be in one of the following values: " + str(multiwoz_domains) + ". Please do not output a domain if it is not mentioned in the dialogue."
        ontology_instruction = ontology_instruction + " The slot can be one of the following values: " + str(multiwoz_slots) + ". Please do not output a slot if it is not mentioned in the dialogue or the user does not care about the value of the slot."

        categorical_slot_instruction = "There are " + str(len(categorical_value_mapping)) +  " categorical slots, which the values of these slots are from a closed set."
        for slot, values in categorical_value_mapping.items():
            categorical_slot_instruction = categorical_slot_instruction + " Slot " + slot + " can be any value from: " + str(values) + "."

        time_slot_instruction = "The leaveat, arriveby, and booktime slots are about time. The values for these slots should use the 24 hour clock and the format of hh:mm."
        number_slot_instruction = "The bookstay and bookpeople slots have the values of an integer number."

        instruction_input = instruction + " " + train_example_instruction + " " + output_format_instruction + " " + ontology_instruction + " " +\
                            categorical_slot_instruction + " " + time_slot_instruction + " " + number_slot_instruction

        return instruction_input

    def get_context_prompt(self, history):
        context = []
        for (utt, speaker) in history:
            assert speaker.lower() in ["user", "system"]
            if speaker.lower() == "user":
                context.append(" User: " + utt)
            else:
                context.append(" System: " + utt)

        context_text = "".join(context[-(self.context_window - 1):])[-self.max_context_char_length:]
        return context_text

    def predict(self, history):

        dialogue_input = self.get_context_prompt(history)

        instruction_input = self.get_instruction_prompt()

        response = self.model.create_chat_completion(
            messages=[
                {"role": "system", "content": instruction_input},
                {
                    "role": "user",
                    "content": dialogue_input
                }
            ],
            max_tokens=self.max_tokens,
            stop=["user:", "User:"]
        )

        state = response["choices"][0]["message"]["content"]
        state = "{" + state.split('{', 1)[-1]
        try:
            state = state[:state.rindex('}') + 1]
        except:
            pass
        state = state_json_formatter(state)
        return state


class ICLHuggingfaceDSTModel(DSTModel):
    """
    Hugging Face's causal language model for DST based on in-context learning.

    This model uses causal language models from Hugging Face to predict dialogue responses based on conversation history and state.
    """

    def __init__(self, config):

        super().__init__()
        self.config = config
        self.model_path = config["experiment"]["dst_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.generation_max_length = int(config["experiment"]["generation_max_length"])
        # self.padding_side = int(config["experiment"]["padding_side"])
        self.load_in_4bit = bool(config["experiment"]["load_in_4bit"])
        self.dataset = MultilingualMultiWoZDataset(config)
        #
        # self.tokenizer = AutoTokenizer.from_pretrained(self.model_path,
        #                                                padding_side=self.padding_side).to(device)

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path).to(device)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path,
                                                          device_map="auto",
                                                          load_in_4bit=self.load_in_4bit)
                                                          

        self.number_training_example = int(config["experiment"]["num_of_example"])
        self.training_data = list(self.dataset.load_data(task="dst")["train"])


    def get_random_incontext_learning_examples(self, num_of_exmaples):
        sampled_examples = random.sample(self.training_data, num_of_exmaples)

        return " ".join(map(lambda x : "Example Input: " + x["source"] + " Example Output: " + str(x["state"]) , sampled_examples))

    def get_instruction_prompt(self):

        instruction = "Following the instructions, predict the belief state based on the history."

        train_example_instruction = "The following are some examples of input and expected output pairs. " + \
                                    self.get_random_incontext_learning_examples(self.number_training_example)

        output_format_instruction = "The predicted output should be in JSON format. The output should be in the format of {domain : { slot : value }}. Please note that there may be one or multiple domains in a dialogue."

        ontology_instruction = "domain should be in one of the following values: " + str(multiwoz_domains) + ". Please do not output a domain if it is not mentioned in the dialogue."
        ontology_instruction = ontology_instruction + " The slot can be one of the following values: " + str(multiwoz_slots) + ". Please do not output a slot if it is not mentioned in the dialogue or the user does not care about the value of the slot."

        categorical_slot_instruction = "There are " + str(len(categorical_value_mapping)) +  " categorical slots, which the values of these slots are from a closed set."
        for slot, values in categorical_value_mapping.items():
            categorical_slot_instruction = categorical_slot_instruction + " Slot " + slot + " can be any value from: " + str(values) + "."

        time_slot_instruction = "The leaveat, arriveby, and booktime slots are about time. The values for these slots should use the 24 hour clock and the format of hh:mm."
        number_slot_instruction = "The bookstay and bookpeople slots have the values of an integer number."

        instruction_input = instruction + " " + train_example_instruction + " " + output_format_instruction + " " + ontology_instruction + " " +\
                            categorical_slot_instruction + " " + time_slot_instruction + " " + number_slot_instruction

        return instruction_input

    def get_context_prompt(self, history):
        context = []
        for (utt, speaker) in history:
            assert speaker.lower() in ["user", "system"]
            if speaker.lower() == "user":
                context.append(" User: " + utt)
            else:
                context.append(" System: " + utt)

        context_text = "".join(context[-(self.context_window - 1):])[-self.max_context_char_length:]
        return context_text


    def predict(self, history):

        dialogue_input = self.get_context_prompt(history)

        instruction_input = self.get_instruction_prompt()
        
        model_inputs = self.tokenizer([f"system: {instruction_input} user: {dialogue_input}"], return_tensors="pt").to(device)
        generated_ids = self.model.generate(**model_inputs, max_new_tokens=self.generation_max_length)
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

        state = response[0]
        state = state_json_formatter(state)
        return json.loads(state)

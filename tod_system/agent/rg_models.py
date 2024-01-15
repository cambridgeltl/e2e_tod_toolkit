# -*- coding: utf-8 -*-
"""
Multilingual Dialogue Response Generation Model as a Server

This script evaluates various response generation models for multilingual dialogue systems. It supports various model architectures
like fine-tuned Huggingface models,  Huggingface models with in-context learning, OpenAI's GPT models with in-context learning,
llama.cpp models with in-context learning. All the models follow the defined API which takes the dialogue history and predicted
dialogue state of the current turn as input and generate both delexicalised and lexicalised dialogue responses to the history.

All models are implemented as stateless machine learning models waiting for queries from the dialogue system agents.
We intend to follow the Microservices architecture.

Author: Songbo Hu and Zhangdie Yuan
Date: 20 November 2023
License: MIT License
"""

import random
import time
from random import choices
from string import ascii_uppercase, digits

from openai import OpenAI

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
from llama_cpp import Llama

from dataset.database import MultiWOZDatabase
from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
from dataset.utils import db_result_to_summary, multiwoz_holders, multiwoz_domains, multiwoz_slots

device = "cuda" if torch.cuda.is_available() else "cpu"

class RGModel():
    """
    Base class for Response Generation models.

    This class defines a common interface for various RG model types. Each subclass implements the predict method.
    """
    def __init__(self, config):
        self.config = config
        self.dataset = MultilingualMultiWoZDataset(config)
        self.database = MultiWOZDatabase(config)
        pass

    def predict(self, history, state):
        raise NotImplementedError()

    def lexicalise_utt(self, utt, state, db_result = None):
        if not db_result:
            db_result = self.database.query_state(state)
        assert db_result != None

        lex_utt = utt

        domain_slot_value_map = {}
        domain_slot_value_map["booking"] = {}
        book_ref_num = ''.join(choices(ascii_uppercase + digits, k=8))
        domain_slot_value_map["booking"]["ref"] = book_ref_num
        domain_slot_value_map["train"] = {}
        train_ref_num = ''.join(choices(ascii_uppercase + digits, k=8))
        domain_slot_value_map["train"]["ref"] = train_ref_num

        for domain in state:
            slot_val_map = domain_slot_value_map.get(domain, {})
            sv_pair = state[domain].copy()
            all_db_entry = []
            for id in db_result[domain]:
                db_entry = self.database.get_entry_by_id(domain, id)[0]
                all_db_entry.append(db_entry)
            sv_pair["entries"] = all_db_entry
            slot_val_map.update(sv_pair)
            domain_slot_value_map[domain] = slot_val_map

        for domain in state:
            for slot, value in state[domain].items():
                if "book" in slot:
                    domain_slot_value_map["booking"][slot[4:]] = value

        for place_holder in multiwoz_holders:
            if place_holder in utt:
                domain, slot = (place_holder.split("_"))
                domain = domain[1:]
                slot = slot[:-1]


                if domain not in domain_slot_value_map:
                    continue
                sv_pair = domain_slot_value_map[domain]

                if slot == "choice":
                    if "entries" in sv_pair:
                        num_of_choice = len(sv_pair["entries"])
                    else:
                        num_of_choice = 0
                    lex_utt = lex_utt.replace(place_holder, str(num_of_choice))

                assert slot != "entries"

                if slot in sv_pair:
                    value = sv_pair[slot]
                    lex_utt = lex_utt.replace(place_holder, value)


                if slot not in sv_pair and "entries" in sv_pair and len(sv_pair["entries"]) > 0:
                    if slot in sv_pair["entries"][0].keys():
                        number_of_count = utt.count(place_holder)
                        all_values = list(map(lambda x:x[slot], sv_pair["entries"]))
                        for idx, value in zip(range(number_of_count), all_values):
                            if value == "?":
                                value = "unknown"
                            lex_utt = lex_utt.replace(place_holder, value, 1)

        return lex_utt


class FTHuggingfaceRGModel(RGModel):
    """
    Fine-tuned Huggingface Sequence-to-Sequence model for RG.

    This model predicts both delexicalised and lexicalised dialogue responses based on conversation history and current state using a sequence-to-sequence architecture.
    """
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.model_path = config["experiment"]["rg_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.generation_max_length = int(config["experiment"]["generation_max_length"])

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path).to(device)


    def predict(self, history, state):
        # Inputs are texts.
        prefix = "response generation"
        context = []
        for (utt, speaker) in history:
            assert speaker.lower() in ["user", "system"]
            if speaker.lower() == "user":
                context.append(" User: " + utt)
            else:
                context.append(" System: " + utt)

        db_result = self.database.query_state(state)

        db_summary = db_result_to_summary(db_result)

        if self.context_window <= 1:
            context_text = "data base result summary: " + db_summary
        else:
            context_text = "data base result summary: " + db_summary + "".join(context[-(self.context_window - 1):])[
                                                                       -self.max_context_char_length:]
        inputs = prefix + " : " + context_text

        model_inputs = self.tokenizer([inputs], return_tensors="pt").to(device)

        generated_ids = self.model.generate(**model_inputs, max_new_tokens=self.generation_max_length)

        utt_delex = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        utt_lex = self.lexicalise_utt(utt_delex, state, db_result)
        return {"utt_lex" : utt_lex, "utt_delex" : utt_delex}


class ICLOpenAIRGModel(RGModel):
    """
    OpenAI's GPT model for RG.

    This model uses OpenAI's GPT models to predict dialogue responses based on conversation history and current state.
    """

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.model_path = config["experiment"]["dst_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.language = config["experiment"]["language"].lower()
        self.model_name = config["experiment"]["rg_model_path"]
        self.number_training_example = int(config["experiment"]["num_of_example"])
        self.training_data = list(self.dataset.load_data(task="response")["train"])
        self.client = OpenAI(api_key=config["experiment"]["openai_key"])

    def get_random_incontext_learning_examples(self, num_of_examples):
        sampled_examples = random.sample(self.training_data, num_of_examples)
        return " ".join(map(lambda x : "Example Input: " + x["source"] + " Example Output: " + str(x["target"]) , sampled_examples))


    def get_instruction_prompt(self):

        instruction = "You are a very helpful assistant, and you will help the users to accomplish their tasks via conversation. Following the instructions, generate a dialogue response based on the dialogue history and the summary of the database query result."

        train_example_instruction = "The following are some examples of input and expected output pairs. " + \
                                    self.get_random_incontext_learning_examples(self.number_training_example)

        ontology_instruction = "The dialogue covers one or several domains: " + str(multiwoz_domains) + "."

        delex_instruction = "Slots are important information for a task-oriented system to accomplish its task. Usually, these slots are essential information for the user to place the booking or the information that the user wants to query from the system."
        delex_instruction = delex_instruction + " All the slots related in this conversation are: " + str(multiwoz_slots) + "."
        delex_instruction = delex_instruction + " For those slots, you should replace the value in the generated utterance with a set of predefined placeholds."
        delex_instruction = delex_instruction + " These placeholders are in the format of [domain_slot], and they are: " + str(multiwoz_holders) + "."

        instruction_input = instruction + " " + train_example_instruction + " " + ontology_instruction + " " + delex_instruction
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
    #
    def predict(self, history, state):

        db_result = self.database.query_state(state)

        db_summary = db_result_to_summary(db_result)
        # print(db_summary)
        instruction_input = self.get_instruction_prompt()

        dialogue_input = "The data summary is: " + db_summary + ". And the dialogue history is: " + self.get_context_prompt(history)

        try_counter = 0
        while try_counter < 50:
            try:
                try_counter += 1
                response = self.client.chat.completions.create(model=self.model_name,
                messages=[
                    {"role": "system", "content": instruction_input},
                    {"role": "user", "content": dialogue_input},
                ])
                utt_delex = response.choices[0].message.content
                utt_lex = self.lexicalise_utt(utt_delex, state, db_result)
                return {"utt_lex": utt_lex, "utt_delex": utt_delex}


            except Exception as e:
                print("RG Fail " +  str(try_counter) + " times.")
                print(e)
                time.sleep(1)

                continue



        raise Exception("Failed to get results from OpenAI.")


class ICLLlamacppRGModel(RGModel):
    """
    Llama.cpp model for RG.

    This model leverages the llama.cpp library for on device LLM inference.
    """
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.model_path = config["experiment"]["dst_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.language = config["experiment"]["language"].lower()
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

        self.training_data = list(self.dataset.load_data(task="response")["train"])

    def get_random_incontext_learning_examples(self, num_of_examples):
        sampled_examples = random.sample(self.training_data, num_of_examples)
        return " ".join(map(lambda x : "Example Input: " + x["source"] + " Example Output: " + str(x["target"]) , sampled_examples))


    def get_instruction_prompt(self):

        instruction = "You are a very helpful assistant, and you will help the users to accomplish their tasks via conversation. Following the instructions, generate a dialogue response based on the dialogue history and the summary of the database query result."

        train_example_instruction = "The following are some examples of input and expected output pairs. " + \
                                    self.get_random_incontext_learning_examples(self.number_training_example)

        ontology_instruction = "The dialogue covers one or several domains: " + str(multiwoz_domains) + "."

        delex_instruction = "Slots are important information for a task-oriented system to accomplish its task. Usually, these slots are essential information for the user to place the booking or the information that the user wants to query from the system."
        delex_instruction = delex_instruction + " All the slots related in this conversation are: " + str(multiwoz_slots) + "."
        delex_instruction = delex_instruction + " For those slots, you should replace the value in the generated utterance with a set of predefined placeholds."
        delex_instruction = delex_instruction + " These placeholders are in the format of [domain_slot], and they are: " + str(multiwoz_holders) + "."

        language_instruction = "You should generate the response in " + self.language + "."

        instruction_input = instruction + " " + train_example_instruction +  " " + ontology_instruction + " " + delex_instruction + " " + language_instruction
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

    def predict(self, history, state):
        db_result = self.database.query_state(state)
        db_summary = db_result_to_summary(db_result)
        instruction_input = self.get_instruction_prompt()
        dialogue_input = "The data summary is: " + db_summary + ". And the dialogue history is: " + self.get_context_prompt(
            history)
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

        utt_delex = response["choices"][0]["message"]["content"]

        utt_lex = self.lexicalise_utt(utt_delex, state, db_result)
        return {"utt_lex": utt_lex, "utt_delex": utt_delex}


class ICLHuggingfaceRGModel(RGModel):
    """
    Hugging Face's causal language model for RG based on in-context learning.

    This model uses causal language models from Hugging Face to predict dialogue responses based on conversation history and state.
    """

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.model_path = config["experiment"]["dst_model_path"]
        self.context_window = int(config["experiment"]["context_window"])
        self.max_context_char_length = int(config["experiment"]["max_context_char_length"])
        self.generation_max_length = int(config["experiment"]["generation_max_length"])
        self.padding_side = int(config["experiment"]["padding_side"])
        self.load_in_4bit = bool(config["experiment"]["load_in_4bit"])
        self.language = config["experiment"]["language"].lower()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path,
                                                       padding_side=self.padding_side).to(device)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path,
                                                          device_map="auto",
                                                          load_in_4bit=self.load_in_4bit)
        self.number_training_example = int(config["experiment"]["num_of_example"])
        self.training_data = list(self.dataset.load_data(task="response")["train"])

    def get_random_incontext_learning_examples(self, num_of_examples):
        sampled_examples = random.sample(self.training_data, num_of_examples)
        return " ".join(map(lambda x : "Example Input: " + x["source"] + " Example Output: " + str(x["target"]) , sampled_examples))


    def get_instruction_prompt(self):

        instruction = "You are a very helpful assistant, and you will help the users to accomplish their tasks via conversation. Following the instructions, generate a dialogue response based on the dialogue history and the summary of the database query result."

        train_example_instruction = "The following are some examples of input and expected output pairs. " + \
                                    self.get_random_incontext_learning_examples(self.number_training_example)

        ontology_instruction = "The dialogue covers one or several domains: " + str(multiwoz_domains) + "."

        delex_instruction = "Slots are important information for a task-oriented system to accomplish its task. Usually, these slots are essential information for the user to place the booking or the information that the user wants to query from the system."
        delex_instruction = delex_instruction + " All the slots related in this conversation are: " + str(multiwoz_slots) + "."
        delex_instruction = delex_instruction + " For those slots, you should replace the value in the generated utterance with a set of predefined placeholds."
        delex_instruction = delex_instruction + " These placeholders are in the format of [domain_slot], and they are: " + str(multiwoz_holders) + "."
        language_instruction = "You should generate the response in " + self.language + "."

        instruction_input = instruction + " " + train_example_instruction + " " + ontology_instruction + " " + delex_instruction + " " + language_instruction

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
    #
    def predict(self, history, state):

        db_result = self.database.query_state(state)

        db_summary = db_result_to_summary(db_result)
        instruction_input = self.get_instruction_prompt()

        dialogue_input = "The data summary is: " + db_summary + ". And the dialogue history is: " + self.get_context_prompt(history)

        model_inputs = self.tokenizer([f"system: {instruction_input} user: {dialogue_input}"], return_tensors="pt").to(device)
        generated_ids = self.model.generate(**model_inputs, max_new_tokens=self.generation_max_length)
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        
        utt_delex = response[0]

        utt_lex = self.lexicalise_utt(utt_delex, state, db_result)
        return {"utt_lex" : utt_lex, "utt_delex" : utt_delex}


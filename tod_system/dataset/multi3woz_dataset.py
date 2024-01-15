# -*- coding: utf-8 -*-
"""
Multilingual MultiWOZ Dataset Interface

This module provides an interface for loading and processing the Multi3WOZ dataset,
suitable for dialogue state tracking (DST) and response generation tasks.
It offers support for multiple languages, namely Arabic, English, French, and Turkish.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import json
from datasets import Dataset, DatasetDict
import pandas as pd
import os

from dataset.database import MultiWOZDatabase
from dataset.utils import metadata_to_state, lex_to_delex_utt,\
	from_state_to_string, from_string_to_state, \
	db_result_to_summary

class MultilingualMultiWoZDataset():
	"""
	A class for loading Multilingual MultiWOZ Datasets.

	This class is designed to load and preprocess the Multilingual MultiWOZ dataset for different NLP tasks like
	dialogue state tracking (DST) and response generation. It supports multiple languages.

	Attributes:
	    config (dict): Configuration dictionary containing necessary paths and settings.
	    language (str): Language of the dataset. Supporting four langauges at the moment: Arabic, English, French, Turkish.
	    data_path (str): Path to the dataset files.
	    raw_train_dic (dict): Raw training data loaded from the dataset without any preprocessing.
	    raw_val_dic (dict): Raw validation data loaded from the dataset without any preprocessing.
	    raw_test_dic (dict): Raw testing data loaded from the dataset without any preprocessing.
	    raw_data_dic (dict): Aggregated raw data dictionary for train, val, and test splits.
	    task (str): The NLP task for which the dataset is being prepared. Currently, it support two tasks: DST and response generation.
	    database (MultiWOZDatabase): Instance of MultiWOZDatabase for querying data. This is required for Training response generation models.
	"""



	def __init__(self, config, language = None):
		"""
		Initializes the MultilingualMultiWoZDataset class.

		Args:
		    config (dict): Configuration dictionary containing necessary paths and settings.
		    language (str, optional): Language of the dataset. Defaults to None. Other value will overwrite the value in the config file.
		"""


		assert config
		self.config = config

		self.language = self.config["experiment"]["language"].lower()

		if language:
			self.language = language.lower()

		assert self.language in ["arabic", "english", "french", "turkish"]

		project_root_path = config["project"]["project_root_path"]

		self.data_path = os.path.join(project_root_path, config["data"][self.language + "_data_path"])

		self.raw_train_dic, self.raw_val_dic, self.raw_test_dic = self._load_raw_dataset()

		self.raw_data_dic = {
			"train": self.raw_train_dic,
			"val": self.raw_val_dic,
			"test": self.raw_test_dic,
		}

		self.task = None

		self.database = MultiWOZDatabase(cfg=self.config)

	def _load_raw_dataset(self):
		"""
		Loads the raw MultiWOZ related dataset from the data paths defined in the config files.

		The data is divided into training, validation, and test dictionaries based on predefined lists.

		Returns:
		    tuple: A tuple containing dictionaries for training, validation, and test datasets.
		"""


		with open(os.path.join(self.data_path, "data.json"), "r", encoding="utf-8") as f:
			data = json.load(f)

		f = open(os.path.join(self.data_path, "valListFile.txt"))
		val_list = f.read().splitlines()
		f.close()
		f = open(os.path.join(self.data_path, "testListFile.txt"))
		test_list = f.read().splitlines()
		f.close()

		train_dic = {}
		val_dic = {}
		test_dic = {}

		for dial_id, dial in data.items():
			if dial_id in test_list:
				test_dic[dial_id] = dial
			elif dial_id in val_list:
				val_dic[dial_id] = dial
			else:
				train_dic[dial_id] = dial

		assert len(train_dic) + len(val_dic) + len(test_dic) == len(data)
		return train_dic, val_dic, test_dic

	def load_data(self, task = None):
		"""
		Loads and preprocesses the dataset for a specified task.

		Args:
		    task (str, optional): The NLP task for which the dataset is being prepared (e.g., "dst", "response"). Defaults to None. Other value will overwrite the value in the config file.

		Returns:
		    DatasetDict: A dictionary of datasets for each data split (train, val, test) preprocessed for the specified task.
		"""


		if task is not None:
			self.task = task
		else:
			self.task = self.config["experiment"]["task"]

		assert self.task in ["dst", "response"]

		dataset_dict = None

		if self.task == "dst":
			processed_data = self._preprocess_dst_dataset()
			for data_key, data in processed_data.items():
				data = pd.DataFrame.from_dict(data)
				data = Dataset.from_pandas(data)
				processed_data[data_key] = data
			dataset_dict = DatasetDict(processed_data)

		elif self.task == "response":
			processed_data = self._preprocess_response_generation_dataset()
			for data_key, data in processed_data.items():
				data = pd.DataFrame.from_dict(data)
				data = Dataset.from_pandas(data)
				processed_data[data_key] = data
			dataset_dict = DatasetDict(processed_data)

		return dataset_dict

	def _preprocess_dst_dataset(self):
		"""
		Preprocesses the dataset for the DST task.

		Returns:
		    dict: Processed data for DST task.
		"""

		self.context_window = int(self.config["experiment"]["context_window"])
		self.max_context_char_length = int(self.config["experiment"]["max_context_char_length"])

		processed_data = {}

		for data_key, dataset in self.raw_data_dic.items():
			processed_data[data_key] = []

			for dial_id, dial in list(dataset.items())[:]:

				context = []

				for turn_id, turn in enumerate(dial['log']):

					if turn_id % 2 == 0:
						context.append(" User: " + turn['text'])
						continue

					if self.context_window <= 1:
						context_text = ""
					else:
						context_text = "".join(context[-(self.context_window - 1):])[-self.max_context_char_length:]

					metadata = turn["metadata"]
					state = metadata_to_state(metadata)
					state_str = from_state_to_string(state)

					assert state ==	from_string_to_state(state_str)

					data_entry = {}
					data_entry["source"] = context_text
					data_entry["target"] = state_str
					data_entry["language"] = self.language
					data_entry["turn_id"] = turn_id
					data_entry["dail_id"] = dial_id
					data_entry["context"] = context.copy()
					data_entry["utterance"] = turn["text"]
					data_entry["state_string"] = state_str
					data_entry["state"] = state
					processed_data[data_key].append(data_entry)

					# We append lexicalised system response to the history based on empericial performance. It outperforms its delexicalised counterpart.
					# context.append(" System: " + lex_to_delex_utt(turn))
					context.append(" System: " + turn["text"])

		return processed_data

	def _preprocess_response_generation_dataset(self):
		"""
		Preprocesses the dataset for response generation task.

		Returns:
		    dict: Processed data for response generation task.
		"""

		self.context_window = int(self.config["experiment"]["context_window"])
		self.max_context_char_length = int(self.config["experiment"]["max_context_char_length"])

		self.db_result_cash_path = os.path.join(self.data_path, "db_results.json")

		if os.path.exists(self.db_result_cash_path):
			with open(self.db_result_cash_path, "r", encoding="utf-8") as f:
				db_result_cache_dic = json.load(f)
		else:
			print("Generating DB query results. It may make a while.")
			db_result_cache_dic = {}

			for data_key, dataset in self.raw_data_dic.items():
				for dial_id, dial in dataset.items():
					for turn_id, turn in enumerate(dial['log']):
						if turn_id % 2 == 0:
							continue
						metadata = turn["metadata"]
						state = metadata_to_state(metadata)
						db_result = self.database.query_state(state)

						dial_dic = db_result_cache_dic.get(dial_id, {})
						dial_dic[str(turn_id)] = db_result
						db_result_cache_dic[dial_id] = dial_dic
			with open(self.db_result_cash_path, 'w', encoding='utf-8') as f:
				json.dump(db_result_cache_dic, f, ensure_ascii=False, indent=4)


		processed_data = {}

		for data_key, dataset in self.raw_data_dic.items():
			processed_data[data_key] = []

			for dial_id, dial in dataset.items():

				context = []

				for turn_id, turn in enumerate(dial['log']):

					if turn_id % 2 == 0:
						context.append(" User: " + turn['text'])
						continue

					db_result = db_result_cache_dic[dial_id][str(turn_id)]
					db_summary = db_result_to_summary(db_result)

					if self.context_window <= 1:
						context_text = "data base result summary: "  + db_summary
					else:
						context_text = "data base result summary: "  + db_summary  + "".join(context[-(self.context_window - 1):])[-self.max_context_char_length:]

					delex_utt = lex_to_delex_utt(turn)

					data_entry = {}
					data_entry["source"] = context_text
					data_entry["target"] = delex_utt
					data_entry["language"] = self.language
					data_entry["turn_id"] = turn_id
					data_entry["dail_id"] = dial_id
					data_entry["context"] = context.copy()
					data_entry["utterance"] = turn["text"]
					data_entry["db_summary"] = db_summary
					processed_data[data_key].append(data_entry)
					context.append(" System: " + turn['text'])

		return processed_data

	def build_response_generation_dataset_with_db_results(self, db_result_cache_dic):
		"""
		Builds the dataset for response generation task using cached database results. This function is required for the
		end-to-end systems because we need the DB results based on the dialogue states from the DST model.

		Args:
		    db_result_cache_dic (dict): Cached database query results.

		Returns:
		    DatasetDict: Dataset for response generation task.
		"""


		self.context_window = int(self.config["experiment"]["context_window"])
		self.max_context_char_length = int(self.config["experiment"]["max_context_char_length"])

		processed_data = {}

		for data_key, dataset in self.raw_data_dic.items():

			if data_key == "train":
				processed_data[data_key] = []
				continue


			processed_data[data_key] = []

			for dial_id, dial in dataset.items():

				context = []

				for turn_id, turn in enumerate(dial['log']):

					if turn_id % 2 == 0:
						context.append(" User: " + turn['text'])
						continue

					state =  db_result_cache_dic[dial_id][str(turn_id)]["state"]
					db_result = db_result_cache_dic[dial_id][str(turn_id)]["db_result"]
					db_summary = db_result_to_summary(db_result)

					if self.context_window <= 1:
						context_text = "data base result summary: "  + db_summary
					else:
						context_text = "data base result summary: "  + db_summary  + "".join(context[-(self.context_window - 1):])[-self.max_context_char_length:]

					delex_utt = lex_to_delex_utt(turn)

					data_entry = {}
					data_entry["source"] = context_text
					data_entry["target"] = delex_utt
					data_entry["language"] = self.language
					data_entry["turn_id"] = turn_id
					data_entry["dail_id"] = dial_id
					data_entry["context"] = context.copy()
					data_entry["utterance"] = turn["text"]
					data_entry["db_summary"] = db_summary
					data_entry["state"] = state
					processed_data[data_key].append(data_entry)
					context.append(" [system_utt] " + turn['text'])

		for data_key, data in processed_data.items():
			data = pd.DataFrame.from_dict(data)
			data = Dataset.from_pandas(data)
			processed_data[data_key] = data
		dataset_dict = DatasetDict(processed_data)
		return dataset_dict

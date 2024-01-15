# -*- coding: utf-8 -*-
"""
MultiWOZ Database Interface

This module provides a database interface for a task-oriented dialogue system toolkit,
specifically designed to interact with the MultiWOZ dataset. It includes functionalities
for loading and querying database entries based on the structured dialogue state,
handling various domains like hotels, attractions, restaurants, and trains.

This file is adapted from the MultiWOZ_Evaluation project by Tomáš Nekvinda and Ondřej Dušek
(https://github.com/Tomiinek/MultiWOZ_Evaluation), which is released under the MIT License.
Modifications were made to suit specific requirements of the current project.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License (original source), MIT License (this file)

"""

import os
import json
import re
from fuzzywuzzy import fuzz
from dataset.utils import slot_normalisation_mapping, dont_care_slot_values, db_supported_domains, lower_dic


class MultiWOZDatabase:
    """
    A class to represent and interact with the MultiWOZ database.

    Attributes:
        supported_domains (list): A list of domains supported by the database.
        IGNORE_VALUES (dict): The set of slot value pairs to ignore during data loading.
        FUZZY_KEYS (dict): The set of slot value pairs where fuzzy matching is applied.
        config (dict): Configuration file which specify the paths required to load database files.
        project_root_path (str): The root path of the project.
        language (str): The language of the database.
        db_path (str): Path to the database files.
        data (dict): Loaded database data.
        data_keys (set): The dictionary of supported domain and relevant slot pairs for each domain.
    """

    def __init__(self, cfg, language = None):
        """
        Initializes the MultiWOZDatabase class.

        Args:
            cfg (dict): Configuration dictionary containing necessary paths and settings.
        """

        self.supported_domains = db_supported_domains

        self.IGNORE_VALUES = {
            'attraction': ['location', 'openhours'],
            'hotel': ['location', 'price', 'takesbookings'],
            'restaurant': ['location', 'introduction', 'signature']
        }

        self.FUZZY_KEYS = {
            'hotel': {'name'},
            'attraction': {'name'},
            'restaurant': {'name', 'food'},
            'train': {'departure', 'destination'}
        }

        # Set paths
        self.config = cfg
        self.project_root_path = self.config["project"]["project_root_path"]
        self.language = self.config["experiment"]["language"].lower()
        if language:
            self.language = language.lower()

        self.db_path = os.path.join(self.project_root_path, self.config["data"][self.language + "_data_path"])

        # Load database data
        self.data, self.data_keys = self._load_data()

    def _time_str_to_minutes(self, time_string):
        """
        Converts a time string in the format "HH:MM" to minutes.

        Args:
            time_string (str): A string representing time in "HH:MM" format.

        Returns:
            int: The time converted to minutes.
        """
        if not re.match(r"[0-9][0-9]:[0-9][0-9]", str(time_string)):
            return 0

        try:
            hour = int(time_string.split(':')[0])
        except:
            hour = 0

        try:
            minute = int(time_string.split(':')[1])
        except:
            minute = 0

        return hour * 60 + minute

    def _load_data(self):
        """
        Loads the data from the database files into memory.

        Returns:
            tuple: A tuple containing the loaded data and the data keys.
        """

        database_data, database_keys = {}, {}

        for domain in self.supported_domains:
            with open(os.path.join(self.db_path, f"{domain}_db.json"), "r") as f:
                database_data[domain] = json.load(f)

            if domain in self.IGNORE_VALUES:
                for i in database_data[domain]:
                    for ignore in self.IGNORE_VALUES[domain]:
                        if ignore in i:
                            i.pop(ignore)


            for i, database_item in enumerate(database_data[domain]):
                database_data[domain][i] =  {slot_normalisation_mapping[k.lower()] : v.lower() if isinstance(v, str) else v for k, v in database_item.items()}

            database_keys[domain] = set(database_data[domain][0].keys())
        return database_data, database_keys

    def query(self, domain, sv_pairs, fuzzy_ratio=90, fuzzy_matching = True):
        """
        Query the database based on the domain and slot-value pairs provided.

        Args:
            domain (str): The domain to query in.
            sv_pairs (dict): Slot-value pairs to use for querying.
            fuzzy_ratio (int, optional): The threshold for fuzzy matching. Defaults to 90.

        Returns:
            list: A list of entities IDs matching the query criteria.
        """

        sv_pairs = lower_dic(sv_pairs)

        results = []

        if domain not in self.supported_domains:
            return results

        query = {}
        for key in self.data_keys[domain]:
            if key in sv_pairs:

                if sv_pairs[key] in dont_care_slot_values:
                    continue

                # We do not do normalisation because we could not normalise other languages easily.
                query[key] = sv_pairs[key]
                if key in ['arriveby', 'leaveat']:
                    query[key] = self._time_str_to_minutes(query[key])
            else:
                query[key] = None


        for i, item in enumerate(self.data[domain]):

            for k, v in query.items():
                if v is None or item[k] == '?':
                    continue

                if k == 'arriveby':
                    time = self._time_str_to_minutes(item[k])
                    if time > v:
                        break
                elif k == 'leaveat':
                    time = self._time_str_to_minutes(item[k])
                    if time < v:
                        break
                else:


                    if fuzzy_matching:
                        if k in self.FUZZY_KEYS.get(domain, {}):

                            f = (lambda x: fuzz.partial_ratio(item[k], x) < fuzzy_ratio)
                        else:
                            f = (lambda x: str(item[k]).lower() != str(x).lower())
                    else:
                        f = (lambda x: str(item[k]).lower() != str(x).lower())

                    if f(v):
                        break
            else:

                results.append(item["id"])

        return results


    def query_state(self, state, fuzzy_matching = True):

        """
        Queries the database based on a dialogue state.

        Args:
            state (dict): A dictionary representing the dialogue state.

        Returns:
            dict: A dictionary with query IDs for each domain.
        """

        result_dic = {}
        for domain, sv_pairs in state.items():
            result_dic[domain] = self.query(domain,sv_pairs, fuzzy_matching)
        return result_dic

    def get_entry_by_id(self, domain, id):
        """
        Retrieves an entry from the database by its ID.

        Args:
            domain (str): The domain of the database entry.
            id (str): The ID of the database entry.

        Returns:
            list: A list containing the requested database entry. Return empty list if no result found.
        """
        all_items = self.data[domain]
        result = list(filter(lambda x : str(x["id"]) == str(id), all_items))

        return result

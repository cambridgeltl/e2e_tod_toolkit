# -*- coding: utf-8 -*-
"""
Multilingual MultiWOZ Dataset Testing Module

This module provides comprehensive unit tests for the Multilingual MultiWOZ Dataset interface.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import json
import unittest
import configparser
import os

from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
from dataset.utils import lex_to_delex_utt, metadata_to_state, multiwoz_slots, slot_normalisation_mapping, \
    multiwoz_domains, multiwoz_holders, from_state_to_string, from_string_to_state, state_json_formatter


class TestMultilingualMultiWoZDataset(unittest.TestCase):

    def setUp(self):
        self.config_file_path = "../dst/config/example_en.cfg"
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(self.config_file_path)
        self.dataset = MultilingualMultiWoZDataset(self.config)

    def test_initialization(self):
        self.assertEqual(self.dataset.language, self.config["experiment"]["language"].lower())


    def test_load_raw_dataset(self):
        dataset = MultilingualMultiWoZDataset(self.config)
        train_data, val_data, test_data = dataset._load_raw_dataset()
        self.assertIsInstance(train_data, dict)
        self.assertIsInstance(val_data, dict)
        self.assertIsInstance(test_data, dict)

        self.assertEqual(len(train_data) + len(val_data) + len(test_data), 9160)

    def test_basic_delexicalization(self):
        utt = {
            "text": "I want to book a hotel in the east area.",
            "span_info": [["hotel-inform", "Area", "east", 30, 34]]
        }
        expected_output = "I want to book a hotel in the [hotel_area] area."
        self.assertEqual(lex_to_delex_utt(utt), expected_output)

    def test_empty_span(self):
        utt = {
            "text": "I want to book a hotel in the east area.",
            "span_info": []
        }
        expected_output = "I want to book a hotel in the east area."
        self.assertEqual(lex_to_delex_utt(utt), expected_output)

    def test_multiwoz_slots(self):

        all_slot = set()
        for split, data in self.dataset.raw_data_dic.items():
            for dialID, dial in data.items():
                for utt in dial["log"]:
                    metadata = utt["metadata"]
                    state = metadata_to_state(metadata)
                    for domain, sv_pair in state.items():
                        for slot, value in sv_pair.items():
                            all_slot.add(slot_normalisation_mapping[slot])
                    dial_act = utt["dialog_act"]
                    for domain_intent, sv_list in dial_act.items():
                        for slot, value in sv_list:
                            if slot.lower() == "none":
                                continue
                            all_slot.add(slot_normalisation_mapping[slot.lower()])

        self.assertEqual(multiwoz_slots, all_slot)




    def test_multiwoz_holders(self):
        all_place_holders = set()
        with open(os.path.join("../data/English/ontology.json"), "r", encoding="utf-8") as f:
            ontology = json.load(f)

        for domain , sv_pairs in ontology.items():
            if domain not in multiwoz_domains:
                continue
            for slot, value in sv_pairs.items():
                if slot in ["none"]:
                    continue
                all_place_holders.add("[" + domain.lower() + "_" + slot_normalisation_mapping[slot.lower()] + "]")

        self.assertGreaterEqual(multiwoz_holders, all_place_holders)


    def test_multiwoz_state_to_string_and_back(self):

        for split, data in self.dataset.raw_data_dic.items():
            for dialID, dial in data.items():
                for utt in dial["log"]:
                    metadata = utt["metadata"]
                    state = metadata_to_state(metadata)
                    state_string = from_state_to_string(state)
                    state_back = from_string_to_state(state_string)
                    self.assertEqual(state, state_back)

    def test_state_json_formatter(self):

        for split, data in self.dataset.raw_data_dic.items():
            for dialID, dial in data.items():
                for utt in dial["log"]:
                    metadata = utt["metadata"]
                    state = metadata_to_state(metadata)
                    checked_state = state_json_formatter(json.dumps(state))
                    self.assertEqual(state, checked_state)

if __name__ == '__main__':
    unittest.main()

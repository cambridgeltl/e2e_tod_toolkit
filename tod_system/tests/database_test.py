# -*- coding: utf-8 -*-
"""
MultiWOZ Database Testing Module

This module provides unit tests for the MultiWOZ Database Interface.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import configparser
import json
import os
import unittest

from dataset.database import MultiWOZDatabase
from dataset.utils import metadata_to_state


class TestMultiWOZDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Assuming you have a configuration setup for your database
        # Replace 'your_config' with your actual configuration
        config_file_path = "config/example_en.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.db_en = MultiWOZDatabase(config)

        config_file_path = "config/example_ar.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.db_ar = MultiWOZDatabase(config)

        config_file_path = "config/example_fr.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.db_fr = MultiWOZDatabase(config)


        config_file_path = "config/example_tr.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.db_tr = MultiWOZDatabase(config)




    def test_load_data(self):

        self.assertIsNotNone(self.db_en.data, "Data should not be None")
        self.assertIsNotNone(self.db_en.data_keys, "Data keys should not be None")

    def test_query(self):

        domain = "hotel"
        sv_pairs = {"name": "a and b guest house"}
        results = self.db_en.query(domain, sv_pairs)
        self.assertIsInstance(results, list, "Query results should be a list")
        self.assertEqual(results, ["0"])

    def test_query_state(self):

        state = {"hotel": {"name": "a and b guest house"}}
        results = self.db_en.query_state(state)
        self.assertIsInstance(results, dict, "Query state results should be a dictionary")
        self.assertEqual(results, {'hotel': ['0']})


    def test_get_entry_by_id(self):

        domain = "hotel"
        entry_id = "0"
        entry = self.db_en.get_entry_by_id(domain, entry_id)
        self.assertIsInstance(entry, list, "Entry should be a list")
        self.assertEqual(entry[0]["name"], "a and b guest house")


    def test_query_user_goal(self):

        with open(os.path.join("../data/English/data.json"), "r", encoding="utf-8") as f:
            en_data = json.load(f)

        f = open(os.path.join("../data/English/valListFile.txt"))
        val_list = f.read().splitlines()
        f.close()

        f = open(os.path.join("../data/English/testListFile.txt"))
        test_list = f.read().splitlines()
        f.close()


        with open(os.path.join("../data/Arabic/data.json"), "r", encoding="utf-8") as f:
            ar_data = json.load(f)

        with open(os.path.join("../data/French/data.json"), "r", encoding="utf-8") as f:
            fr_data = json.load(f)

        with open(os.path.join("../data/Turkish/data.json"), "r", encoding="utf-8") as f:
            tr_data = json.load(f)

        for dial_id in list(en_data.keys())[:]:

            en_dial = en_data[dial_id]
            fr_dial = fr_data[dial_id]
            ar_dial = ar_data[dial_id]
            tr_dial = tr_data[dial_id]

            en_goal = en_dial["goal"]
            fr_goal = fr_dial["goal"]
            ar_goal = ar_dial["goal"]
            tr_goal = tr_dial["goal"]

            assert en_goal.keys() == fr_goal.keys() and en_goal.keys() == ar_goal.keys() and en_goal.keys() == tr_goal.keys()

            for domain in en_goal:

                if domain == "train":
                    continue

                if "info" in en_goal[domain]:


                    en_state = en_goal[domain]["info"]
                    en_result = sorted(self.db_en.query(domain, en_state))
                    fr_state = fr_goal[domain]["info"]
                    fr_result = sorted(self.db_fr.query(domain, fr_state))
                    ar_state = ar_goal[domain]["info"]
                    ar_result = sorted(self.db_ar.query(domain, ar_state))
                    tr_state = tr_goal[domain]["info"]
                    tr_result = sorted(self.db_tr.query(domain, tr_state))

                    self.assertTrue(
                        (len(fr_result) > 0 and len(en_result) > 0) or (len(fr_result) == 0 and len(en_result) == 0) and
                        (len(ar_result) > 0 and len(en_result) > 0) or (len(ar_result) == 0 and len(en_result) == 0) and
                        (len(tr_result) > 0 and len(en_result) > 0) or (len(tr_result) == 0 and len(en_result) == 0)
                    )


    # This test takes a while...
    def test_multiparallalism(self):

        with open(os.path.join("../data/English/data.json"), "r", encoding="utf-8") as f:
            en_data = json.load(f)

        f = open(os.path.join("../data/English/valListFile.txt"))
        val_list = f.read().splitlines()
        f.close()

        f = open(os.path.join("../data/English/testListFile.txt"))
        test_list = f.read().splitlines()
        f.close()


        with open(os.path.join("../data/Arabic/data.json"), "r", encoding="utf-8") as f:
            ar_data = json.load(f)

        with open(os.path.join("../data/French/data.json"), "r", encoding="utf-8") as f:
            fr_data = json.load(f)

        with open(os.path.join("../data/Turkish/data.json"), "r", encoding="utf-8") as f:
            tr_data = json.load(f)

        for dial_id in list(en_data.keys())[:]:

            # Out of ontology utterance.
            # English dialogues have so many south indian and north indian food type slots.
            if dial_id in ["MUL1496.json", "MUL1569.json", "SNG0586.json", "PMUL3858.json", "PMUL4850.json", "PMUL2281.json", "MUL0311.json", "PMUL0073.json", "MUL0139.json" , "SNG0614.json", "PMUL3270.json", "MUL0193.json", "MUL1394.json", "MUL0825.json", "PMUL0429.json" , "PMUL2125.json", "SNG0656.json", "MUL0019.json", "PMUL0200.json", "PMUL0085.json", "PMUL0855.json", "PMUL0001.json", "SSNG0152.json"]:
                continue
            en_dial = en_data[dial_id]
            fr_dial = fr_data[dial_id]
            ar_dial = ar_data[dial_id]
            tr_dial = tr_data[dial_id]

            en_utts = en_dial["log"]
            ar_utts = ar_dial["log"]
            fr_utts = fr_dial["log"]
            tr_utts = tr_dial["log"]

            for en_utt, fr_utt, tr_utt in zip(en_utts, fr_utts, tr_utts):
                en_state = metadata_to_state(en_utt["metadata"])
                fr_state = metadata_to_state(fr_utt["metadata"])
                tr_state = metadata_to_state(tr_utt["metadata"])

                en_result = self.db_en.query_state(en_state, fuzzy_matching=False)
                fr_result = self.db_fr.query_state(fr_state, fuzzy_matching=False)
                tr_result = self.db_tr.query_state(tr_state, fuzzy_matching=False)

                self.assertEqual(en_result.keys(), fr_result.keys())
                self.assertEqual(en_result.keys(), tr_result.keys())



                for domain in en_result:
                    if domain == "train":
                        continue

                    self.assertLessEqual( abs(len(en_result[domain])-len(fr_result[domain])) , 0)
                    self.assertLessEqual( abs(len(en_result[domain])-len(tr_result[domain])) , 0)


if __name__ == '__main__':
    unittest.main()

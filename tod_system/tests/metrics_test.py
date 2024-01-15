# -*- coding: utf-8 -*-
"""
Multi3WOZ Metric Testing Module

This module is dedicated to testing the Multi3WOZ Inform and Success Rates across various language configurations.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""


import unittest
import configparser
from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
from dataset.utils import generate_prediction_from_dialogue
from evaluation.metrics import Multi3WOZSuccess


class TestMulti3WOZSuccess(unittest.TestCase):

    def setUp(self):
        config_file_path = "config/example_en.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.data_en = MultilingualMultiWoZDataset(config)
        self.metric_en = Multi3WOZSuccess(config)


        config_file_path = "config/example_ar.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.data_ar = MultilingualMultiWoZDataset(config)
        self.metric_ar = Multi3WOZSuccess(config)


        config_file_path = "config/example_fr.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.data_fr = MultilingualMultiWoZDataset(config)
        self.metric_fr = Multi3WOZSuccess(config)


        config_file_path = "config/example_tr.cfg"
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
        self.data_tr = MultilingualMultiWoZDataset(config)
        self.metric_tr = Multi3WOZSuccess(config)

    def test_multiparallalism(self):

        en_prediction = {}

        for data_key in ["val", "test"]:

            for dialID, dial in self.data_en.raw_data_dic[data_key].items():
                prediction = generate_prediction_from_dialogue(dial)
                en_prediction[dialID] = prediction
        en_test_result =  self.metric_en.eval(en_prediction)

        ar_prediction = {}

        for data_key in ["val", "test"]:

            for dialID, dial in self.data_ar.raw_data_dic[data_key].items():
                prediction = generate_prediction_from_dialogue(dial)
                ar_prediction[dialID] = prediction
        ar_test_result = self.metric_ar.eval(ar_prediction)

        fr_prediction = {}

        for data_key in ["val", "test"]:

            for dialID, dial in self.data_fr.raw_data_dic[data_key].items():
                prediction = generate_prediction_from_dialogue(dial)
                fr_prediction[dialID] = prediction
        fr_test_result = self.metric_fr.eval(fr_prediction)

        tr_prediction = {}

        for data_key in ["val", "test"]:

            for dialID, dial in self.data_tr.raw_data_dic[data_key].items():
                prediction = generate_prediction_from_dialogue(dial)
                tr_prediction[dialID] = prediction
        tr_test_result = self.metric_tr.eval(tr_prediction)

        self.assertLessEqual(abs(en_test_result["inform"]["all"] - ar_test_result["inform"]["all"]), 1)
        self.assertLessEqual(abs(en_test_result["success"]["all"] - ar_test_result["success"]["all"]), 1)

        self.assertLessEqual(abs(en_test_result["inform"]["all"] - fr_test_result["inform"]["all"]), 1)
        self.assertLessEqual(abs(en_test_result["success"]["all"] - fr_test_result["success"]["all"]), 1)

        self.assertLessEqual(abs(en_test_result["inform"]["all"] - tr_test_result["inform"]["all"]), 1)
        self.assertLessEqual(abs(en_test_result["success"]["all"] - tr_test_result["success"]["all"]), 1)


if __name__ == '__main__':
    unittest.main()

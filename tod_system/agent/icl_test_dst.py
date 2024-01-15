# -*- coding: utf-8 -*-
"""
Multilingual Dialogue State Tracking (DST) Model Evaluation for In-context Learning Models

This script evaluates an in-context learning-based DST model in multilingual dialogue systems.

It uses a specified model to predict the state of dialogues in a test dataset and then evaluates these predictions against the gold standard.

This script is designed for the in-context learning-based models. You can use it for fine-tuned based models. However, you may find using this script ./dst/test_dst.py is way more efficient.

The DST model is tested on a subset of dialogues because OpenAI's API is very slow.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""
import random

from agent import ICLOpenAIDSTModel, FTHuggingfaceDSTModel, ICLLlamacppDSTModel, ICLHuggingfaceDSTModel
from evaluation.metrics import Multi3WOZDST
from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
import configparser
import argparse
import json
import os
from transformers import set_seed

from dataset.utils import metadata_to_state, from_state_to_string

result_dic = {}

def run_experiment():
    """
    Conducts the DST model evaluation experiment.

    Parses configuration and command line arguments, prepares the dataset,
    initializes the DST model, and performs the evaluation. The results are
    saved in a file.
    """

    global result_dic

    parser = argparse.ArgumentParser(description="Config Loader")
    parser.add_argument("-C","-c", "--config", help="set config file", required=True, type=argparse.FileType('r'))
    parser.add_argument("-n", "--note", help="note for the experiment")
    parser.add_argument("-l", "--language", help="language for testing")
    args = parser.parse_args()

    config = None

    config_file_path = args.config.name
    if config_file_path is not None:
        try:
            config = configparser.ConfigParser(allow_no_value=True)
            config.read(config_file_path)
        except Exception as inst:
            print('Failed to parse file', inst)
    else:
        config = configparser.ConfigParser(allow_no_value=True)

    config.set("project", "config_path", args.config.name)
    config.set("experiment", "task", "dst")

    experiment_note = args.note if args.note else "dst_testing"

    eval_language = args.language if args.language else config["experiment"]["language"]
    current_language = eval_language.lower()

    result_save_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"],  "dst_evaluation_result_"+ experiment_note +".json")

    set_seed(int(config["experiment"]["seed"]))

    dataset = MultilingualMultiWoZDataset(config,language=current_language)

    agent_type = config["experiment"]["agent_type"]
    assert agent_type in ["fthuggingface", "iclopenai", "iclllamacpp", "iclhuggingface"]

    # These models are stateless.
    dst_model = None

    if agent_type == "fthuggingface":
        dst_model = FTHuggingfaceDSTModel(config)
    elif agent_type == "iclopenai":
        dst_model = ICLOpenAIDSTModel(config)
    elif agent_type == "iclllamacpp":
        dst_model = ICLLlamacppDSTModel(config)
    elif agent_type == "iclhuggingface":
        dst_model = ICLHuggingfaceDSTModel(config)

    assert dst_model

    output_save_dir = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"])


    if not os.path.exists(output_save_dir):
        os.makedirs(output_save_dir)
    output_prediction_file = os.path.join(output_save_dir,
                                          "dst_predictions_test.json")

    if os.path.isfile(output_prediction_file):
        with open(output_prediction_file, "r", encoding="utf-8") as f:
            prediction_dic = json.load(f)
    else:
        prediction_dic = {}

    print(str(len(prediction_dic)) + " results loaded from the prediction.")

    target_ids = sorted(list(dataset.raw_data_dic["test"].keys()))
    random.seed(0)

    # You may adjust this value to a larger or smaller number, as making predictions for the entire test set with
    # Large Language Models (LLMs) can be time-consuming and resource-intensive.
    target_ids = random.sample(target_ids, 100)

    for dial_id in target_ids:

        dial = dataset.raw_data_dic["test"][dial_id]
        if dial_id in prediction_dic:
            continue
        utt_list = []
        utt_len = len(dial["log"])

        history = []
        print(dial_id)

        for i in range(utt_len):
            if i % 2 == 0:
                history.append((dial["log"][i]["text"], "user"))
            else:
                state = dst_model.predict(history)
                utt_list.append({"state" : state,
                                 "gold_state" : from_state_to_string(metadata_to_state(dial["log"][i]["metadata"]))
                                 })

                history.append((dial["log"][i]["text"], "system"))

        prediction_dic[dial_id] = utt_list



        with open(output_prediction_file, 'w', encoding='utf-8') as f:
            json.dump(prediction_dic, f, ensure_ascii=False, indent=4)

    this_metric = Multi3WOZDST(config)
    result_dic["test"] = this_metric.eval(prediction_dic, split="test", skip_check = True)
    print("printing result")
    print(result_dic)

    with open(result_save_path, 'w', encoding='utf-8') as f:
        json.dump(result_dic, f, ensure_ascii=False, indent=4)


def main():
    """
    Main function to run the DST model evaluation experiment.
    """
    run_experiment()

if __name__ == '__main__':
    main()
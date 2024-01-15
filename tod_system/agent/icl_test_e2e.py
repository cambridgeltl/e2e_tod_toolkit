# -*- coding: utf-8 -*-
"""
End-to-End Evaluation of Multilingual Dialogue System Model for In-context Learning Models

This script performs an end-to-end evaluation of an in-context learning-based dialogue system model on the Multilingual MultiWOZ dataset. T

This script is designed for the in-context learning-based models. You can use it for fine-tuned based models. However, you may find using this script ./e2e/test_e2e.py is way more efficient.

The DST model is tested on a subset of dialogues because OpenAI's API is very slow.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""
import random

from agent import  ICLOpenAIDSTModel, FTHuggingfaceDSTModel, ICLLlamacppDSTModel, ICLHuggingfaceDSTModel, \
    ICLOpenAIRGModel, FTHuggingfaceRGModel, ICLLlamacppRGModel, ICLHuggingfaceRGModel

from dataset.utils import metadata_to_state, from_state_to_string
from evaluation.metrics import Multi3WOZDST, Multi3WOZCorpusBLEU, Multi3WOZSuccess
from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
import configparser
import argparse
import json
import os
import datetime
result_dic = {}

def run_experiment():
    """
    Conducts the end-to-end evaluation experiment for a dialogue system model.

    This function parses configuration and command line arguments, initializes the dataset, DST, and RG models,
    and performs the evaluation. The evaluation results for each dialogue are saved and printed.
    """
    global result_dic

    parser = argparse.ArgumentParser(description="Config Loader")
    parser.add_argument("-C","-c", "--config", help="set config file", required=True, type=argparse.FileType('r'))
    parser.add_argument("-n", "--note", help="note for the experiment")
    parser.add_argument("-l", "--language", help="language for testing")
    args = parser.parse_args()

    config = None

    config_file_path = args.config.name
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
    except Exception as inst:
        print('Failed to parse file', inst)

    config.set("project", "config_path", args.config.name)

    experiment_note = args.note if args.note else "e2e_testing"

    eval_language = args.language if args.language else config["experiment"]["language"]
    current_language = eval_language.lower()

    dataset = MultilingualMultiWoZDataset(config,language=current_language)


    output_save_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"])
    if not os.path.exists(output_save_path):
        os.makedirs(output_save_path)
    output_prediction_file = os.path.join(output_save_path, "e2e_predictions.json")

    if os.path.isfile(output_prediction_file):
        with open(output_prediction_file, "r", encoding="utf-8") as f:
            prediction_dic = json.load(f)
    else:
        prediction_dic = {}

    print(str(len(prediction_dic)) + " results loaded from the prediction.")

    agent_type = config["experiment"]["agent_type"]
    assert agent_type in ["fthuggingface", "iclopenai", "iclllamacpp", "iclhuggingface"]

    dst_model = None
    rg_model = None

    if agent_type == "fthuggingface":
        dst_model = FTHuggingfaceDSTModel(config)
        rg_model = FTHuggingfaceRGModel(config)
    elif agent_type == "iclopenai":
        dst_model = ICLOpenAIDSTModel(config)
        rg_model = ICLOpenAIRGModel(config)
    elif agent_type == "iclllamacpp":
        dst_model = ICLLlamacppDSTModel(config)
        rg_model = ICLLlamacppRGModel(config)
    elif agent_type == "iclhuggingface":
        dst_model = ICLHuggingfaceDSTModel(config)
        rg_model = ICLHuggingfaceRGModel(config)

    assert dst_model
    assert rg_model


    # You may adjust this value to a larger or smaller number, as making predictions for the entire test set with
    # Large Language Models (LLMs) can be time-consuming and resource-intensive.
    target_ids = sorted(list(dataset.raw_data_dic["test"].keys()))
    random.seed(0)
    target_ids = random.sample(target_ids, 100)

    for dial_id in target_ids:

        if dial_id in prediction_dic:
            continue


        dial = dataset.raw_data_dic["test"][dial_id]
        utt_list = []
        utt_len = len(dial["log"])

        history = []

        print(dial_id)
        print(len(prediction_dic))
        now = datetime.datetime.now()
        print(now.time())
        for i in range(utt_len):
            if i % 2 == 0:
                history.append((dial["log"][i]["text"], "user"))
            else:
                state = dst_model.predict(history)
                response = rg_model.predict(history, state)

                utt_list.append({"state" : state,
                                 "gold_state" : from_state_to_string(metadata_to_state(dial["log"][i]["metadata"])),
                                 "response_delex": response["utt_delex"],
                                 "response_lex": response["utt_lex"],
                })

                history.append((dial["log"][i]["text"], "system"))

        prediction_dic[dial_id] = utt_list

        with open(output_prediction_file, 'w', encoding='utf-8') as f:
            json.dump(prediction_dic, f, ensure_ascii=False, indent=4)



    metric_bleu = Multi3WOZCorpusBLEU(config)
    metric_dst = Multi3WOZDST(config)
    metric_success = Multi3WOZSuccess(config)

    result_dic["test_bleu"] = (metric_bleu.eval(prediction_dic, split = "test", skip_check = True).score)
    result_dic["test_dst"] = (metric_dst.eval(prediction_dic, split = "test", skip_check = True))
    result_dic["test_success"] = (metric_success.eval(prediction_dic, split = "test", skip_check = True))

    print("printing result")
    print(result_dic)

    result_save_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"],  "evaluation_result_"+ experiment_note +".json")
    with open(result_save_path, 'w', encoding='utf-8') as f:
        json.dump(result_dic, f, ensure_ascii=False, indent=4)

def main():
    """
    Main function to run the end-to-end evaluation experiment.
    """
    run_experiment()

if __name__ == '__main__':
    main()
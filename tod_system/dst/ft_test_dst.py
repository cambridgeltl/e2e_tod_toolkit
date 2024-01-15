# -*- coding: utf-8 -*-
"""
Dialogue State Tracking Model Evaluation Script

This script is designed to evaluate a sequence-to-sequence model for the DST task.
The evaluation process includes generating predictions for dialogue states and comparing them against reference states.

Results of the evaluation are saved, and the evaluated model is loaded through the config file, on which the model was trained.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import shutil

from evaluation.metrics import Multi3WOZDST
from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, \
    DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments

import configparser
import argparse
import json
import os

import numpy as np
from transformers import set_seed

from dataset.utils import metadata_to_state, from_string_to_state, from_state_to_string

result_dic = {}

def run_experiment():
    """
    Main function to run the evaluation.

    It handles saving the evaluation results and configuration for future reference.
    """

    global result_dic

    parser = argparse.ArgumentParser(description="Config Loader")
    parser.add_argument("-C","-c", "--config", help="set config file", required=True, type=argparse.FileType('r'))
    parser.add_argument("-s", "--seed", help="set random seed", type=int)
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


    experiment_note = args.note if args.note else "testing"

    eval_language = args.language if args.language else config["experiment"]["language"]
    current_language = eval_language.lower()

    result_save_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"],  "evaluation_result_"+ experiment_note +".json")

    set_seed(int(config["experiment"]["seed"]))
    prediction_dic = get_dst_prediction(config, ["val", "test"], current_language)


    output_prediction_file = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"], "predictions.json")
    with open(output_prediction_file, 'w', encoding='utf-8') as f:
        json.dump(prediction_dic, f, ensure_ascii=False, indent=4)

    this_metric = Multi3WOZDST(config)
    result_dic["val"] = (this_metric.eval(prediction_dic, split="val"))
    result_dic["test"] = (this_metric.eval(prediction_dic))

    with open(result_save_path, 'w', encoding='utf-8') as f:
        json.dump(result_dic, f, ensure_ascii=False, indent=4)

    config_save_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"], experiment_note+ "_config.cfg")
    shutil.copyfile(config["project"]["config_path"], config_save_path)

    print("printing result")
    print(result_dic)

def get_dst_prediction(config, splits, current_language):
    """
    Generates predictions for the dialogue state tracking task.

    Args:
        config: Configuration settings for the model training. This is used to load the trained model back.
        splits: On which dataset splits (e.g., 'val', 'test') to generate predictions.
        current_language: The language of the dataset for which predictions are generated.

    Returns:
        A dictionary containing the prediction result.
    """

    for split in splits:
        assert split in ["val" , "dev", "test", "testing"]

    dataset = MultilingualMultiWoZDataset(config,language=current_language)

    data_dic = dataset.load_data()

    prefix = "dialogue state tracking"

    model_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"], "checkpoint-best")

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to("cuda")

    def preprocess_function(examples):

        inputs = [prefix + " : " + example for example in examples["source"]]
        targets = [example for example in examples["target"]]
        model_inputs = tokenizer(inputs, text_target=targets, max_length=int(config["experiment"]["generation_max_length"]))
        return model_inputs

    tokenized_dataset = data_dic.map(preprocess_function, batched=True)

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    training_args = Seq2SeqTrainingArguments(
        output_dir=os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"]),
        learning_rate=float(config["experiment"]["learning_rate"]),
        per_device_train_batch_size=int(config["experiment"]["batch_size"]),
        per_device_eval_batch_size=int(config["experiment"]["batch_size"]),
        weight_decay=float(config["experiment"]["weight_decay"]),
        save_total_limit=int(config["experiment"]["save_total_limit"]),
        predict_with_generate=True,
        max_steps=int(config["experiment"]["max_training_steps"]),
        save_steps=int(config["experiment"]["eval_and_save_steps"]),
        eval_steps=int(config["experiment"]["eval_and_save_steps"]),
        save_strategy="steps",
        evaluation_strategy="steps",
        load_best_model_at_end=True,
        push_to_hub=False,
        fp16=config["experiment"]["fp16"].lower()=="true",
        metric_for_best_model="bleu",
        greater_is_better=True,
        generation_max_length=int(config["experiment"]["generation_max_length"])
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["val"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    prediction_dic = {}

    if "val" in splits or "dev" in splits:

        predict_results = trainer.predict(tokenized_dataset["val"])
        predictions = predict_results.predictions
        predictions = np.where(predictions != -100, predictions, tokenizer.pad_token_id)
        predictions = tokenizer.batch_decode(
            predictions, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        predictions = [pred.strip() for pred in predictions]

        raw_prediction_dic = {}

        for (test_entry, pred) in zip(tokenized_dataset["val"], predictions):

            dial_dic = raw_prediction_dic.get(test_entry["dail_id"], {})
            dial_dic[test_entry["turn_id"]] = pred
            raw_prediction_dic[test_entry["dail_id"]] = dial_dic


        for dial_id, dial in dataset.raw_data_dic["val"].items():
            utt_list = []
            utt_len = len(dial["log"])
            preds = raw_prediction_dic.get(dial_id, {})
            for i in range(1, utt_len, 2):
                state = from_string_to_state(preds.get(i, "").strip())
                utt_list.append({"state" : state,
                                 "raw_output" : preds.get(i, "")
                                 })
            prediction_dic[dial_id] = utt_list


    if "test" in splits or "testing" in splits:


        predict_results = trainer.predict(tokenized_dataset["test"])
        predictions = predict_results.predictions
        predictions = np.where(predictions != -100, predictions, tokenizer.pad_token_id)
        predictions = tokenizer.batch_decode(
            predictions, skip_special_tokens=True, clean_up_tokenization_spaces=True
        )
        predictions = [pred.strip() for pred in predictions]

        raw_prediction_dic = {}

        for (test_entry, pred) in zip(tokenized_dataset["test"], predictions):

            dial_dic = raw_prediction_dic.get(test_entry["dail_id"], {})
            dial_dic[test_entry["turn_id"]] = pred
            raw_prediction_dic[test_entry["dail_id"]] = dial_dic

        for dial_id, dial in dataset.raw_data_dic["test"].items():
            utt_list = []
            utt_len = len(dial["log"])
            preds = raw_prediction_dic.get(dial_id, {})
            for i in range(1, utt_len, 2):
                state = from_string_to_state(preds.get(i, "").strip())
                utt_list.append({"state" : state,
                                 "raw_output" : preds.get(i, ""),
                                 "gold_state" : from_state_to_string(metadata_to_state(dial["log"][i]["metadata"]))
                                 })
            prediction_dic[dial_id] = utt_list

    return prediction_dic

def main():
    """
    Main execution function.
    """
    run_experiment()

if __name__ == '__main__':
    main()
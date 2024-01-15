# -*- coding: utf-8 -*-
"""
Multilingual Dialogue System Model Evaluation on the End-to-end Modelling Task

This script is designed to evaluate a sequence-to-sequence model for the end-to-end modelling task in multilingual dialogue systems.
The script is capable of handling various metrics such as BLEU score, joint goal accuracy, and task inform and success rates
to assess the model's performance comprehensively.

The evaluation process involves generating predictions for both the dialogue state and response generation tasks
and then assessing these predictions against reference data.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import shutil

from dataset.database import MultiWOZDatabase
from dst.ft_test_dst import get_dst_prediction
from evaluation.metrics import Multi3WOZDST, Multi3WOZCorpusBLEU, Multi3WOZSuccess
from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, \
    DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments

import configparser
import argparse
import json
import os

import numpy as np

result_dic = {}

def run_experiment():
    """
    Main function to initiate the evaluation experiment.

    It has three steps in the pipeline. 1) DST, 2) query the database and generate the database result summaries, and 3)
    generate the delexicalised responses. This code is for benchmark automatic evaluation, so no lexicalisation happening here.
    """

    global result_dic

    parser = argparse.ArgumentParser(description="Config Loader")
    parser.add_argument("-C","-c", "--config", help="set config file", required=True, type=argparse.FileType('r'))
    parser.add_argument("-s", "--seed", help="set random seed", type=int)
    parser.add_argument("-n", "--note", help="note for the experiment")
    parser.add_argument("-l", "--language", help="language for testing")
    args = parser.parse_args()

    e2e_config = None
    dst_config = None
    rg_config = None

    config_file_path = args.config.name
    try:
        e2e_config = configparser.ConfigParser(allow_no_value=True)
        e2e_config.read(config_file_path)
    except Exception as inst:
        print('Failed to parse file', inst)

    e2e_config.set("project", "config_path", args.config.name)
    dst_config_path = e2e_config["experiment"]["dst_config"]
    rg_config_path = e2e_config["experiment"]["rg_config"]


    try:
        dst_config = configparser.ConfigParser(allow_no_value=True)
        dst_config.read(dst_config_path)
    except Exception as inst:
        print('Failed to parse file', inst)

    try:
        rg_config = configparser.ConfigParser(allow_no_value=True)
        rg_config.read(rg_config_path)
    except Exception as inst:
        print('Failed to parse file', inst)

    experiment_note = args.note if args.note else "e2e_testing"

    eval_language = args.language if args.language else e2e_config["experiment"]["language"]
    current_language = eval_language.lower()

    # Step 1): DST.
    dst_prediction = get_dst_prediction(dst_config, ["val", "test"], current_language)

    # Step 2): DB query.
    db_result = get_db_summery(dst_config, dst_prediction, current_language)

    # Step 3): RG.
    response_prediction = get_response_prediction(rg_config, db_result, dst_prediction, current_language)

    output_save_path = os.path.join(e2e_config["project"]["project_root_path"], e2e_config["experiment"]["output_dir"])
    if not os.path.exists(output_save_path):
        os.makedirs(output_save_path)

    output_prediction_file = os.path.join(e2e_config["project"]["project_root_path"], e2e_config["experiment"]["output_dir"], "predictions.json")
    with open(output_prediction_file, 'w', encoding='utf-8') as f:
        json.dump(response_prediction, f, ensure_ascii=False, indent=4)


    metric_dst = Multi3WOZDST(e2e_config)
    metric_bleu = Multi3WOZCorpusBLEU(e2e_config)
    metric_success = Multi3WOZSuccess(e2e_config)
    result_dic["val_dst"] = (metric_dst.eval(response_prediction, split = "val"))
    result_dic["test_dst"] = (metric_dst.eval(response_prediction, split = "test"))
    result_dic["val_bleu"] = metric_bleu.eval(response_prediction, split = "val").score
    result_dic["test_bleu"] = metric_bleu.eval(response_prediction, split = "test").score
    result_dic["val_success"] = metric_success.eval(response_prediction, split = "val")
    result_dic["test_success"] = metric_success.eval(response_prediction, split = "test")

    print("printing result")
    print(result_dic)

    result_save_path = os.path.join(e2e_config["project"]["project_root_path"], e2e_config["experiment"]["output_dir"],  "evaluation_result_"+ experiment_note +".json")
    with open(result_save_path, 'w', encoding='utf-8') as f:
        json.dump(result_dic, f, ensure_ascii=False, indent=4)

    config_save_path = os.path.join(e2e_config["project"]["project_root_path"], e2e_config["experiment"]["output_dir"], experiment_note+ "_config.cfg")
    shutil.copyfile(e2e_config["project"]["config_path"], config_save_path)


def get_db_summery(config, dst_prediction, current_language):
    """
    Generates database summaries based on DST predictions.

    Args:
        config: Configuration settings for the database query.
        dst_prediction: Predicted dialogue states.
        current_language: The language of the dataset for evaluation.

    Returns:
        A dictionary containing database query results for each dialogue turn.
    """

    database = MultiWOZDatabase(config, current_language)

    print("Generating DB query results. It may make a while.")
    db_result_cache_dic = {}

    for dial_id in dst_prediction:

        for idx in range(0, len(dst_prediction[dial_id])):
            state = dst_prediction[dial_id][idx]["state"]
            turn_id = 2 * idx + 1

            db_result = database.query_state(state)

            dial_dic = db_result_cache_dic.get(dial_id, {})
            dial_dic[str(turn_id)] = {
                "db_result" :db_result,
                "state" : state
            }
            db_result_cache_dic[dial_id] = dial_dic

    return db_result_cache_dic


def get_response_prediction(config, db_result, dst_result, current_language):
    """
    Generates response predictions based on the database summary.

    Args:
        config: Configuration settings for the response generation task.
        db_summary: Summaries of database query results.
        current_language: The language of the dataset for evaluation.

    Returns:
        A dictionary containing response generation predictions.
    """


    dataset = MultilingualMultiWoZDataset(config,language=current_language)

    data_dic = dataset.build_response_generation_dataset_with_db_results(db_result_cache_dic=db_result)

    prefix = "response generation: "

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

            delex_response = preds.get(i, "").strip()
            utt_list.append(
                {
                    "response_delex" : delex_response,
                    "state" : dst_result[dial_id][int(i/2)]["state"],
                }
            )
        prediction_dic[dial_id] = utt_list

    # Evaluation on the testing set.
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


            delex_response = preds.get(i, "").strip()
            utt_list.append({"response_delex" : delex_response,
                             "state" : dst_result[dial_id][int(i/2)]["state"],
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
# -*- coding: utf-8 -*-
"""
Dialogue State Tracking Model Training Script

This script is designed to train a sequence-to-sequence model for the task of dialogue state tracking in
a multilingual setting.

This code will print provisional results, such as joint goal accuracy (JGA), to assess model performance. However, please
use the test_dst.py script to produce your final reported results.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import shutil
from dataset.multi3woz_dataset import MultilingualMultiWoZDataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, \
    DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments, EarlyStoppingCallback

import configparser
import argparse
import json
import os
import evaluate
import numpy as np
from transformers import set_seed
from fuzzywuzzy import fuzz

from dataset.utils import slot_normalisation_mapping, from_string_to_state

result_dic = {}

def run_experiment():
    """
    Main function to run the training and evaluation experiment.
    It also handles saving the training results and the configuration file for future reference.
    """

    global result_dic

    parser = argparse.ArgumentParser(description="Config Loader")
    parser.add_argument("-C","-c", "--config", help="set config file", required=True, type=argparse.FileType('r'))

    # This argument will overwrite the value specified in the config file.
    parser.add_argument("-s", "--seed", help="set random seed", type=int)
    args = parser.parse_args()

    config = None

    config_file_path = args.config.name
    assert config_file_path is not None
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file_path)
    except Exception as inst:
        print('Failed to parse file', inst)

    config.set("project", "config_path", args.config.name)

    result_save_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"], "evaluation_result.json")

    train(config)

    with open(result_save_path, 'w', encoding='utf-8') as f:
        json.dump(result_dic, f, ensure_ascii=False, indent=4)

    config_save_path = os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"], "config.cfg")
    shutil.copyfile(config["project"]["config_path"], config_save_path)


def train(config):
    """
    Function to train the DST model.

    Args:
        config (ConfigParser object): Configuration settings for the training process.

    This function handles the entire training pipeline, including model initialization,
    dataset preparation, training, and (provisional!!!) evaluation. It also computes and saves the (provisional!!!) evaluation
    results for both the development and test sets.
    """

    global result_dic

    model_name = config["experiment"]["model_name"]
    set_seed(int(config["experiment"]["seed"]))

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        max_length = int(config["experiment"]["generation_max_length"])
    )

    dataset = MultilingualMultiWoZDataset(config)
    data_dic = dataset.load_data()

    prefix = "dialogue state tracking"

    model = AutoModelForSeq2SeqLM.from_pretrained(model_name,
          max_length=int(config["experiment"]["generation_max_length"])
    )

    def preprocess_function(examples):

        inputs = [prefix + " : " + example for example in examples["source"]]
        targets = [example for example in examples["target"]]

        model_inputs = tokenizer(inputs, text_target=targets, max_length=int(config["experiment"]["generation_max_length"]))

        return model_inputs

    tokenized_dataset = data_dic.map(preprocess_function, batched=True)

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    bleu = evaluate.load("sacrebleu")
    rouge = evaluate.load("rouge")
    meteor = evaluate.load("meteor")

    def postprocess_text(preds, labels):
        preds = [pred.strip() for pred in preds]
        labels = [[label.strip()] for label in labels]
        return preds, labels

    def get_state(preds, labels):
        pred_states = [from_string_to_state(pred) for pred in preds]
        label_states = [from_string_to_state(label[0]) for label in labels]
        return pred_states, label_states

    def state_jga(preds, labels):
        def flatten(state_dict):
            constraints = {}
            for domain, state in state_dict.items():
                for s, v in state.items():
                    constraints[(domain.lower(), slot_normalisation_mapping.get(s, s))] = v.lower()
            return constraints

        def is_matching(hyp, ref):
            hyp_k = hyp.keys()
            ref_k = ref.keys()
            if hyp_k != ref_k:
                return False
            for k in ref_k:
                if fuzz.partial_ratio(hyp[k], ref[k]) <= 95:
                    return False
            return True

        num_preds = 0
        num_hit = 0
        for pred_state, label_state in zip(preds, labels):
            is_match = is_matching(flatten(pred_state), flatten(label_state))
            num_preds += 1
            num_hit += is_match

        score = num_hit/num_preds
        return score


    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)

        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)
        pred_states, label_states = get_state(decoded_preds, decoded_labels)

        jga_score = state_jga(pred_states, label_states)

        result = bleu.compute(predictions=decoded_preds, references=decoded_labels)
        result = {"bleu": result["score"]}
        result["jga"] = jga_score

        rouge_result = rouge.compute(predictions=decoded_preds, references=decoded_labels)
        meteor_result = meteor.compute(predictions=decoded_preds, references=decoded_labels)

        for key, score in rouge_result.items():
            result[key] = score
        result["meteor"] = meteor_result["meteor"]


        prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
        result["gen_len"] = np.mean(prediction_lens)
        result = {k: round(v, 4) for k, v in result.items()}
        return result


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
        metric_for_best_model="jga",
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
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=int(config["experiment"]["early_stopping_patience"]))]
    )

    trainer.train()

    dev_result = trainer.evaluate(max_length = int(config["experiment"]["generation_max_length"]))
    result_dic["dev_result"] = dev_result
    print(dev_result)

    test_result = trainer.evaluate(tokenized_dataset["test"], max_length = int(config["experiment"]["generation_max_length"]))
    result_dic["test_result"] = test_result
    print(test_result)

    trainer.save_model(os.path.join(config["project"]["project_root_path"], config["experiment"]["output_dir"], "checkpoint-best"))


def main():
    """
    Main execution function.

    Calls the run_experiment function to start the training process.
    """
    run_experiment()

if __name__ == '__main__':
    main()
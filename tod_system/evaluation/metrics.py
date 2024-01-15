# -*- coding: utf-8 -*-
"""
Dialogue System Evaluation Metrics

This module provides a set of classes and functions to evaluate dialogue systems and their components on the MultiWOZ dataset.
It includes implementations of various metrics such as BLEU score for response quality, JGA for DST,
and Inform and Success Rates for the end-to-end task.

The implementation of Multi3WOZSuccess is adapted from the MultiWOZ_Evaluation project by Tomáš Nekvinda and Ondřej Dušek
(https://github.com/Tomiinek/MultiWOZ_Evaluation), which is released under the MIT License.
Modifications were made to suit specific requirements of the current project.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License (original source), MIT License (this file)
"""

import os
import json
from collections import Counter
from nltk.translate.meteor_score import single_meteor_score

from sacrebleu import corpus_bleu
from fuzzywuzzy import fuzz

from dataset.database import MultiWOZDatabase
from dataset.utils import generate_prediction_from_dialogue, lower_dic, slot_normalisation_mapping


class Metric():
    """
    An abstract base class for defining dialogue system evaluation metrics.

    This class serves as a foundation for specific metric implementations. It provides a common interface
    for all metrics, including methods for resetting states, validating evaluation data, computing scores,
    and evaluating a dataset.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def _validate_eval_data(self, eval_data):
        pass

    def compute(self, eval_data, reference_data):
        raise NotImplementedError()

    def eval(self, eval_data, split):
        raise NotImplementedError()


class Multi3WOZMetric(Metric):
    """
    A subclass of Metric for evaluating dialogue systems on the Multi3WOZ dataset.

    This class adds specific functionalities for handling the Multi3WOZ dataset, including loading the dataset,
    references, and user goals. It serves as a base for more specific Multi3WOZ-related metrics.

    Attributes:
	    config (dict): Configuration dictionary containing necessary paths and settings.
        language (str): Language of the dataset.
        data_path (str): Path to the dataset files.
        available_domains (list): List of domains available in the dataset.
        all_requestable_slots (list): List of all requestable slots in the dataset.
        raw_data_dic (dict): Raw dataset loaded from files.
        reference_dic (dict): Reference data loaded for evaluation.
        user_goal_dic (dict): User goals loaded from the dataset.
    """

    def __init__(self, config):
        super().__init__()

        self.reset()

        self.config = config
        self.language = self.config["experiment"]["language"].lower()
        assert self.language in ["arabic", "english", "french", "turkish"]
        self.data_path = os.path.join(self.config["project"]["project_root_path"], config["data"][self.language + "_data_path"])

        self.available_domains = ["attraction", "hospital", "hotel", "police", "restaurant", "train"]

        self.all_requestable_slots = ['stars', 'parking', 'id', 'area', 'internet', 'arriveby', 'post', 'food', 'pricerange', 'addr',
         'fee', 'leaveat', 'type', 'time', 'phone', 'ref']

        self.raw_data_dic = self._load_raw_dataset()
        self.reference_dic = self._load_references()
        self.user_goal_dic = self._load_user_goal()

    def eval(self, eval_data, split = "test", skip_check = False):
        assert split in ["train", "val", "test"]

        eval_references = self.reference_dic[split]

        if not skip_check:
            for dialID in eval_references:
                assert dialID in eval_data

        self._validate_eval_data(eval_data)

        eval_score = self.compute(eval_data, eval_references)
        return eval_score

    def compute(self, eval_data, reference_data):
        return NotImplementedError()

    def _load_raw_dataset(self):

        split_dic = {
            "train": {},
            "val": {},
            "test": {},
        }

        with open(os.path.join(self.data_path, "data.json"), "r", encoding="utf-8") as f:
            data = json.load(f)

        f = open(os.path.join(self.data_path, "valListFile.txt"))
        val_list = f.read().splitlines()
        f.close()
        f = open(os.path.join(self.data_path, "testListFile.txt"))
        test_list = f.read().splitlines()
        f.close()


        train_list = list(filter(lambda x: x not in test_list + val_list, data.keys()))
        for dial_id, dial in data.items():
            if dial_id in test_list:
                split_dic["test"][dial_id] = dial
            elif dial_id in val_list:
                split_dic["val"][dial_id] = dial
            elif dial_id in train_list:
                split_dic["train"][dial_id] = dial

        assert len(split_dic["train"]) + len(split_dic["val"]) + len(split_dic["test"]) == len(data)

        return split_dic

    def _load_references(self):

        reference_dic = {}

        for split in self.raw_data_dic:
            split_reference_dic = {}
            for dialID in self.raw_data_dic[split]:
                dial = self.raw_data_dic[split][dialID]
                reference = generate_prediction_from_dialogue(dial)
                split_reference_dic[dialID] = reference
            reference_dic[split] = split_reference_dic

        return reference_dic

    def _load_user_goal(self):

        goal_dic = {}

        def normalise_sv_pairs(sv_pairs):
            new_sv_pairs = {}

            for key, val in sv_pairs.items():
                new_sv_pairs[slot_normalisation_mapping[key]] = val

            return new_sv_pairs

        for split in self.raw_data_dic:
            for dialID in self.raw_data_dic[split]:

                dial = self.raw_data_dic[split][dialID]
                user_goal = dial["goal"]

                new_goal = {}

                for domain, value in user_goal.items():
                    if domain not in self.available_domains:
                        continue
                    if value:
                        new_value = {}

                        request = lower_dic(value.get("reqt", []))
                        inform = lower_dic(value.get("info", {}))
                        book = lower_dic(value.get("book", {}))
                        fail_info = lower_dic(value.get("fail_info", {}))
                        fail_book = lower_dic(value.get("fail_book", {}))

                        new_value["reqt"] = list(map(lambda x : slot_normalisation_mapping[x], request))
                        new_value["info"] = normalise_sv_pairs(inform)
                        new_value["book"] = book
                        new_value["fail_info"] = normalise_sv_pairs(fail_info)
                        new_value["fail_book"] = fail_book

                        new_goal[domain] = new_value

                goal_dic[dialID] = new_goal

        return goal_dic


class Multi3WOZCorpusBLEU(Multi3WOZMetric):
    """
    A class for computing the corpus BLEU score for dialogue system responses. Here, we calculate the BLEU score for the delexicalised utterances by defualt.
    """


    def __init__(self, config,  eval_mode = "delex"):
        super().__init__(config)
        self._bleu = None
        self._count = None
        self._hyp_list = None
        self._refs_list = None
        self._eval_mode = eval_mode
        assert self._eval_mode in ["delex", "lex"]

        self.reset()

    def reset(self):
        self._bleu = 0
        self._count = 0
        self._hyp_list = []
        self._refs_list = []
        super().reset()

    def _validate_eval_data(self, eval_data):
        for dialID, dial in eval_data.items():
            for utt in dial:
                if self._eval_mode == "lex":
                    assert "response_lex" in utt
                if self._eval_mode == "delex":
                    assert "response_delex" in utt

    def compute(self, eval_data, reference_data):

        for dialID in reference_data:
            if dialID not in eval_data:
                continue

            reference_dial = reference_data[dialID]
            eval_dial = eval_data[dialID]
            assert len(reference_dial) == len(eval_dial)
            for eval_utt, ref_utt in zip(reference_dial, eval_dial):

                hypothesis = eval_utt["response_delex"].strip().replace("_", "").replace("[", "").replace("]", "") if self._eval_mode == "delex" else eval_utt["response_lex"]
                reference = ref_utt["response_delex"].strip().replace("_", "").replace("[", "").replace("]", "") if self._eval_mode == "delex" else ref_utt["response_lex"]

                self._hyp_list.append(hypothesis)
                self._refs_list.append(reference)
                self._count += 1

        bleu_score = corpus_bleu(self._hyp_list, [self._refs_list])
        return bleu_score


class Multi3WOZMETEOR(Multi3WOZMetric):
    """
    A class for computing the METEOR score for dialogue system responses.
    """

    def __init__(self, config,  eval_mode = "delex"):
        super().__init__(config)
        self._meteor = None
        self._count = None
        self._eval_mode = eval_mode
        assert self._eval_mode in ["delex", "lex"]

        self.reset()

    def reset(self):
        self._meteor = 0
        self._count = 0
        super().reset()

    def _validate_eval_data(self, eval_data):
        for dialID, dial in eval_data.items():
            for utt in dial:
                if self._eval_mode == "lex":
                    assert "response_lex" in utt
                if self._eval_mode == "delex":
                    assert "response_delex" in utt

    def compute(self, eval_data, reference_data):

        for dialID in reference_data:
            if dialID not in eval_data:
                continue

            reference_dial = reference_data[dialID]
            eval_dial = eval_data[dialID]
            assert len(reference_dial) == len(eval_dial)
            for eval_utt, ref_utt in zip(reference_dial, eval_dial):
                hypothesis = eval_utt["response_delex"].strip().replace("_", "").replace("[", "").replace("]", "") if self._eval_mode == "delex" else eval_utt["response_lex"]
                reference = ref_utt["response_delex"].strip().replace("_", "").replace("[", "").replace("]", "") if self._eval_mode == "delex" else ref_utt["response_lex"]
                hyp_tokens = hypothesis.split()
                ref_tokens = reference.split()
                meteor = single_meteor_score(ref_tokens, hyp_tokens)
                self._meteor += meteor
                self._count += 1
        if self._count == 0:
            raise ValueError("METEOR must have at least one example before it can be computed!")
        return self._meteor / self._count

def my_lcs(string, sub):
    """
    Calculates longest common subsequence for a pair of tokenized strings
    :param string : list of str : tokens from a string split using whitespace
    :param sub : list of str : shorter string, also split using whitespace
    :returns: length (list of int): length of the longest common subsequence between the two strings
    Note: my_lcs only gives length of the longest common subsequence, not the actual LCS

    This function is copied from https://github.com/Maluuba/nlg-eval/blob/master/nlgeval/pycocoevalcap/rouge/rouge.py
    """
    if len(string) < len(sub):
        sub, string = string, sub

    lengths = [[0 for i in range(0, len(sub) + 1)] for j in range(0, len(string) + 1)]

    for j in range(1, len(sub) + 1):
        for i in range(1, len(string) + 1):
            if string[i - 1] == sub[j - 1]:
                lengths[i][j] = lengths[i - 1][j - 1] + 1
            else:
                lengths[i][j] = max(lengths[i - 1][j], lengths[i][j - 1])

    return lengths[len(string)][len(sub)]

class Rouge:
    """
    Class for computing ROUGE-L score for a set of candidate sentences

    This class is copied from https://github.com/Maluuba/nlg-eval/blob/master/nlgeval/pycocoevalcap/rouge/rouge.py
    with minor modifications
    """

    def __init__(self):
        self.beta = 1.2

    def calc_score(self, candidate, refs):
        """
        Compute ROUGE-L score given one candidate and references
        :param candidate: str : candidate sentence to be evaluated
        :param refs: list of str : reference sentences to be evaluated
        :returns score: float (ROUGE-L score for the candidate evaluated against references)
        """
        assert (len(refs) > 0)
        prec = []
        rec = []

        # split into tokens
        token_c = candidate.split()

        for reference in refs:
            # split into tokens
            token_r = reference.split()
            # compute the longest common subsequence
            lcs = my_lcs(token_r, token_c)
            prec.append(lcs / float(len(token_c)))
            rec.append(lcs / float(len(token_r)))

        prec_max = max(prec)
        rec_max = max(rec)

        if prec_max != 0 and rec_max != 0:
            score = ((1 + self.beta ** 2) * prec_max * rec_max) / float(rec_max + self.beta ** 2 * prec_max)
        else:
            score = 0.0
        return score

    def method(self):
        return "Rouge"


class Multi3WOZROUGE(Multi3WOZMetric):
    """
    A class for computing the ROUGE score for dialogue system responses.
    """


    def __init__(self, config,  eval_mode = "delex"):
        super().__init__(config)
        self.scorer = Rouge()
        self._rouge = None
        self._count = None
        self._eval_mode = eval_mode
        assert self._eval_mode in ["delex", "lex"]

        self.reset()

    def reset(self):
        self._rouge = 0
        self._count = 0
        super().reset()

    def _validate_eval_data(self, eval_data):
        for dialID, dial in eval_data.items():
            for utt in dial:
                if self._eval_mode == "lex":
                    assert "response_lex" in utt
                if self._eval_mode == "delex":
                    assert "response_delex" in utt

    def compute(self, eval_data, reference_data):

        for dialID in reference_data:
            if dialID not in eval_data:
                continue

            reference_dial = reference_data[dialID]
            eval_dial = eval_data[dialID]
            assert len(reference_dial) == len(eval_dial)
            for eval_utt, ref_utt in zip(reference_dial, eval_dial):
                hypothesis = eval_utt["response_delex"].strip().replace("_", "").replace("[", "").replace("]", "") if self._eval_mode == "delex" else eval_utt["response_lex"]
                reference = ref_utt["response_delex"].strip().replace("_", "").replace("[", "").replace("]", "") if self._eval_mode == "delex" else ref_utt["response_lex"]

                if reference == "":
                    rouge = 0
                else:
                    rouge = self.scorer.calc_score(hypothesis, [reference])
                self._rouge += rouge
                self._count += 1
        if self._count == 0:
            raise ValueError("ROUGE-L must have at least one example before it can be computed!")
        return self._rouge / self._count




class Multi3WOZDST(Multi3WOZMetric):
    """
    A class for evaluating DST metrics in the Multi3WOZ dataset.

    Attributes:
        fuzzy_ratio (int): The threshold for fuzzy string matching.
    """



    def __init__(self, config, fuzzy_ratio=95):
        super().__init__(config)
        self.fuzzy_ratio = fuzzy_ratio
        self.reset()

    def reset(self):
        super().reset()


    def _validate_eval_data(self, eval_data):
        for dialID, dial in eval_data.items():
            for utt in dial:
                    assert "state" in utt

    def compute(self, eval_data, reference_data):


        def flatten(state_dict):
            constraints = {}
            for domain, state in state_dict.items():

                if not (type(state) == type({})):
                    continue

                for s, v in state.items():
                    if s not in slot_normalisation_mapping:
                        continue
                    constraints[(domain.lower(), slot_normalisation_mapping[s])] = str(v).lower()
            return constraints

        def is_matching(hyp, ref):
            hyp_k = hyp.keys()
            ref_k = ref.keys()
            if hyp_k != ref_k:
                return False
            for k in ref_k:
                if fuzz.partial_ratio(hyp[k], ref[k]) <= self.fuzzy_ratio:
                    return False
            return True

        def compare(hyp, ref):

            tp, fp, fn = 0, 0, 0
            for slot, value in hyp.items():
                if slot in ref and fuzz.partial_ratio(value, ref[slot]) > self.fuzzy_ratio:
                    tp += 1
                else:
                    fp += 1
            for slot, value in ref.items():
                if slot not in hyp or fuzz.partial_ratio(hyp[slot], value) <= self.fuzzy_ratio:
                    fn += 1
            return tp, fp, fn

        joint_match, slot_f1, slot_p, slot_r = 0, 0, 0, 0

        total_tp, total_fp, total_fn = 0, 0, 0
        num_turns = 0

        for dialID in reference_data:
            if dialID not in eval_data:
                continue
            reference_dial = reference_data[dialID]
            eval_dial = eval_data[dialID]
            assert len(reference_dial) == len(eval_dial)
            for eval_utt, ref_utt in zip(reference_dial, eval_dial):
                ref = flatten(ref_utt["state"])
                hyp = flatten(eval_utt["state"])

                if is_matching(hyp, ref):
                    joint_match += 1

                tp, fp, fn = compare(hyp, ref)
                total_tp += tp
                total_fp += fp
                total_fn += fn

                num_turns += 1

        slot_p = total_tp / (total_tp + total_fp + 1e-10)
        slot_r = total_tp / (total_tp + total_fn + 1e-10)
        slot_f1 = 2 * slot_p * slot_r / (slot_p + slot_r + 1e-10) * 100
        joint_match = joint_match / (num_turns + 1e-10) * 100

        return {
            'joint_accuracy': joint_match,
            'slot_f1': slot_f1,
            'slot_precision': slot_p,
            'slot_recall': slot_r
        }


class Multi3WOZSuccess(Multi3WOZMetric):
    """
    A class for calculating the task Inform and Success rates in the Multi3WOZ dataset.
    """


    def __init__(self, config):
        super().__init__(config)

        self.database = MultiWOZDatabase(config)
        self.reset()

    def reset(self):
        super().reset()

    def _validate_eval_data(self, eval_data):
        for dialID, dial in eval_data.items():
            for utt in dial:
                    assert "state" in utt
                    assert "response_delex" in utt

    def compute(self, eval_data, reference_data):

        total = Counter()
        inform_rate = {}
        success_rate = {}

        for dialID in reference_data:
            if dialID not in eval_data:
                continue
            user_goal = self.user_goal_dic[dialID]
            reference_utts = reference_data[dialID]
            predict_utts = eval_data[dialID]
            inform, success = self.get_dialogue_success(predict_utts, reference_utts, user_goal)

            for domain in set(inform) | set(success):
                total[domain] += 1
                inform_rate[domain]   = inform.get(domain, 0)  + inform_rate.get(domain, 0)
                success_rate[domain] = success.get(domain, 0) + success_rate.get(domain, 0)


        match_rate = {domain: round(100 * inform_rate[domain] / total[domain], 1) for domain in inform_rate}
        success_rate = {domain: round(100 * success_rate[domain] / total[domain], 1) for domain in success_rate}

        return {
            'inform': match_rate,
            'success': success_rate,
        }



    def get_dialogue_success(self, predict_utts, reference_utts, user_goal):

        requestable_slots_in_goal = {domain: set(map(lambda x : slot_normalisation_mapping[x], user_goal[domain]['reqt'])) for domain in user_goal}
        offered_venues = {domain: [] for domain in user_goal}
        provided_requestable_slots = {domain: set() for domain in user_goal}

        for utt in predict_utts:
            response = utt["response_delex"]
            state = utt["state"]

            for domain in user_goal.keys():

                inform_slot_holder = None
                if domain in ['restaurant', 'hotel', 'attraction']:
                    inform_slot_holder = "[" + domain + "_name]"
                if domain in ["train"]:
                    inform_slot_holder = "[" + domain + "_id]"

                if inform_slot_holder in response:

                    matching_venues = self.database.query(domain, state.get(domain, {}))

                    if domain not in offered_venues or len(offered_venues[domain]) == 0:
                        offered_venues[domain] = matching_venues
                    elif not set(offered_venues[domain]).issubset(set(matching_venues)):
                        offered_venues[domain] = matching_venues

                for request_slot in self.all_requestable_slots:
                    request_slot_holder =  "[" + domain + "_" + request_slot + "]"
                    if (request_slot_holder) in response:
                        provided_requestable_slots[domain].add(request_slot)

        inform_result = {domain: False for domain in user_goal}

        for domain in user_goal.keys():

            if 'name' in user_goal[domain]['info'] or 'name' in user_goal[domain]['fail_info']:
                inform_result[domain] = True
            if domain in ['police', 'hospital']:
                inform_result[domain] = True
            if domain == "train" and not offered_venues['train'] and 'trainid' not in user_goal['train']['reqt']:
                inform_result[domain] = True

        for domain in user_goal:
            if domain in ['restaurant', 'hotel', 'attraction', 'train'] and len(offered_venues[domain]) > 0:

                # Get venues from the database that match all the information provided by the user
                goal_venues = self.database.query(domain, user_goal[domain]['info'])

                goal_fail_venues = self.database.query(domain, user_goal[domain]['fail_info'])
                # We are doing a bit different here. We also compare the fail_info.

                match_domain =  set(offered_venues[domain]).issubset(set(goal_venues)) or set(offered_venues[domain]).issubset(set(goal_fail_venues))
                inform_result[domain] = inform_result[domain] or match_domain

        inform_result["all"] = sum(inform_result.values()) == len(inform_result.keys())


        success_result = {domain: False for domain in user_goal}

        if inform_result["all"]:
            for domain in user_goal:
                # if values in sentences are super set of requestables
                provided_and_wanted_slots = provided_requestable_slots[domain] & requestable_slots_in_goal[domain]

                domain_success = len(provided_and_wanted_slots) == len(requestable_slots_in_goal[domain])
                success_result[domain] = domain_success

            success_result['all'] = (sum(success_result.values()) >= len(success_result.keys()))

        return inform_result, success_result

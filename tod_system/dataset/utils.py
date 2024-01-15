# -*- coding: utf-8 -*-
"""
MultiWOZ Data Utilities

This module contains utilities and functions to handle and normalize the MultiWOZ dataset. These functions are used in
both fine-tuning-based and in-context-learning based systems.

Author: Songbo Hu
Date: 20 November 2023
License: MIT License
"""
import json
import re

db_supported_domains = {"attraction", "hospital", "hotel", "police", "restaurant", "train"}

multiwoz_slots = {'addr', 'area', 'arriveby', 'bookday', 'bookpeople', 'bookstay', 'booktime', 'car', 'choice', 'day', 'department', 'departure', 'destination', 'fee', 'food', 'id', 'internet', 'leaveat', 'name', 'parking', 'people', 'phone', 'post', 'pricerange', 'ref', 'stars', 'stay', 'ticket', 'time', 'type'}

multiwoz_domains = {"attraction", "hospital", "hotel", "police", "restaurant", "train"}

dont_care_slot_values = {"", "dontcare", 'not mentioned', "don't care", "dont care", "do n't care", 'none'}

multiwoz_holders = {'[train_destination]', '[hospital_phone]', '[hotel_choice]', '[booking_people]', '[hospital_post]',
                     '[restaurant_name]', '[taxi_arriveby]', '[hotel_type]', '[booking_day]', '[restaurant_phone]',
                     '[taxi_departure]', '[train_ticket]', '[hotel_pricerange]', '[attraction_addr]',
                     '[attraction_phone]', '[train_departure]', '[hotel_day]', '[train_time]', '[booking_name]',
                     '[police_name]', '[attraction_area]', '[restaurant_ref]', '[hotel_area]', '[police_post]',
                     '[hotel_addr]', '[attraction_type]', '[restaurant_food]', '[taxi_destination]', '[hotel_stay]',
                     '[booking_time]', '[police_phone]', '[hotel_people]', '[restaurant_post]', '[train_ref]',
                     '[booking_ref]', '[train_choice]', '[hotel_stars]', '[train_leaveat]', '[booking_stay]',
                     '[restaurant_addr]', '[hotel_phone]', '[restaurant_area]', '[taxi_leaveat]', '[hotel_post]',
                     '[attraction_post]', '[train_people]', '[train_id]', '[taxi_phone]', '[hospital_addr]', '[restaurant_choice]',
                     '[attraction_name]', '[restaurant_people]', '[hotel_ref]', '[restaurant_day]', '[taxi_car]', '[police_addr]',
                    '[hospital_department]', '[restaurant_pricerange]', '[train_arriveby]',
                    '[attraction_choice]', '[attraction_fee]', '[train_day]', '[hotel_name]', '[hotel_parking]', '[hotel_internet]',
                    '[restaurant_time]'}


def get_slot_normalisation_mapping():
    slot_normalisation_mapping = {}
    slot_normalisation_mapping["addr"] = "addr"
    slot_normalisation_mapping["address"] = "addr"
    slot_normalisation_mapping["area"] = "area"
    slot_normalisation_mapping["arrive"] = "arriveby"
    slot_normalisation_mapping["arriveby"] = "arriveby"
    slot_normalisation_mapping["car"] = "car"
    slot_normalisation_mapping["car type"] = "car"
    slot_normalisation_mapping["choice"] = "choice"
    slot_normalisation_mapping["day"] = "day"
    slot_normalisation_mapping["depart"] = "departure"
    slot_normalisation_mapping["departure"] = "departure"
    slot_normalisation_mapping["department"] = "department"
    slot_normalisation_mapping["dest"] = "destination"
    slot_normalisation_mapping["destination"] = "destination"
    slot_normalisation_mapping["fee"] = "fee"
    slot_normalisation_mapping["entrance fee"] = "fee"
    slot_normalisation_mapping["food"] = "food"
    slot_normalisation_mapping["id"] = "id"
    slot_normalisation_mapping["trainid"] = "id"
    slot_normalisation_mapping["leave"] = "leaveat"
    slot_normalisation_mapping["leaveat"] = "leaveat"
    slot_normalisation_mapping["internet"] = "internet"
    slot_normalisation_mapping["name"] = "name"
    slot_normalisation_mapping["people"] = "people"
    slot_normalisation_mapping["phone"] = "phone"
    slot_normalisation_mapping["post"] = "post"
    slot_normalisation_mapping["postcode"] = "post"
    slot_normalisation_mapping["price"] = "pricerange"
    slot_normalisation_mapping["pricerange"] = "pricerange"
    slot_normalisation_mapping["ref"] = "ref"
    slot_normalisation_mapping["stars"] = "stars"
    slot_normalisation_mapping["stay"] = "stay"
    slot_normalisation_mapping["ticket"] = "ticket"
    slot_normalisation_mapping["time"] = "time"
    slot_normalisation_mapping["duration"] = "time"
    slot_normalisation_mapping["type"] = "type"
    slot_normalisation_mapping["parking"] = "parking"
    slot_normalisation_mapping["bookstay"] = "bookstay"
    slot_normalisation_mapping["bookday"] = "bookday"
    slot_normalisation_mapping["bookpeople"] = "bookpeople"
    slot_normalisation_mapping["booktime"] = "booktime"

    return slot_normalisation_mapping

slot_normalisation_mapping = get_slot_normalisation_mapping()

def lex_to_delex_utt(utt):
    lex_utt = utt["text"]
    delex_utt = ""
    span_info = sorted(utt["span_info"], key=(lambda x: x[-2]))
    current_idx = 0

    for span in span_info:
        domain, intent = span[0].split("-")
        slot = span[1].lower()
        slot = slot_normalisation_mapping[slot]
        value = span[2]
        start_idx, end_idx = span[3], span[4]

        if start_idx < current_idx or value == "dontcare":
            continue

        delex_utt += lex_utt[current_idx:start_idx]
        delex_utt += f"[{domain.lower()}_{slot}]"
        current_idx = end_idx
    delex_utt += lex_utt[current_idx:]
    return delex_utt


def metadata_to_state(metadata):
    new_state = {}

    for domain in metadata.keys():
        if domain == "bus":
            continue
        state_dic = metadata[domain]["semi"]

        new_state_dic = {}

        for slot, value in state_dic.items():

            if value not in dont_care_slot_values:
                # In the whole system, all slots are normalised and lowered. All the values are lower.
                new_state_dic[slot_normalisation_mapping[slot.lower()]] = value.lower()

        # We flatten those book slots in the meta data. So it will be composed to something like bookday.
        book_dic = metadata[domain]["book"]
        for slot, value in book_dic.items():
            if slot in ["booked"]:
                continue
            if value not in dont_care_slot_values:
                new_state_dic[slot_normalisation_mapping["book" + slot.lower()]] = value.lower()

        if new_state_dic:
            new_state[domain] = dict(sorted(new_state_dic.items()))
    return dict(sorted(new_state.items()))

def generate_prediction_from_dialogue(dial):
    logs = dial["log"]
    prediction_list = []
    for utt in logs[1::2]:
        delex_utt = lex_to_delex_utt(utt)
        state = metadata_to_state(utt["metadata"])
        prediction = {}
        prediction["response_delex"] = delex_utt
        prediction["response_lex"] = utt["text"]
        prediction["state"] = state
        prediction_list.append(prediction)
    return prediction_list

def lower_dic(obj):
    if hasattr(obj,'items'):
        ret = {}
        for k,v in obj.items():
            ret[lower_dic(k)] = lower_dic(v)
        return ret
    elif isinstance(obj,str):
        return obj.lower()
    elif hasattr(obj,'__iter__'):
        ret = []
        for item in obj:
            ret.append(lower_dic(item))
        return ret
    else:
        return obj

def from_state_to_string(state):

    state_string = ""
    dsv_strings = []
    for domain, sv_pairs in state.items():

        sv_strings = []
        for slot, value in sv_pairs.items():
            sv_strings.append(slot + " = " + value)

        dsv_string = domain + " # " + " ; ".join(sv_strings)
        dsv_strings.append(dsv_string)

    state_string = state_string + " | ".join(dsv_strings)

    return state_string

def from_string_to_state(state_string):
    def parse_dsv_tuple(dsv_tuple):
        domain = dsv_tuple.split("#")[0].strip()
        sv_pairs = dsv_tuple.split("#")[1].strip()
        sv_dic = {}
        for sv_pair in sv_pairs.split(";"):
            try:
                slot = sv_pair.split("=")[0].strip()
                value = sv_pair.split("=")[1].strip().lower()

                if value in dont_care_slot_values:
                    continue
                sv_dic[slot] = value
            except:
                continue

        return domain, sv_dic

    predicted_dic = {}

    for dsv_tuple in state_string.split(" | "):
        try:
            domain, sv_dic = parse_dsv_tuple(dsv_tuple)
        except:
            continue

        if len(sv_dic) == 0:
            continue

        predicted_dic[domain] = sv_dic

    return predicted_dic

def db_result_to_summary(db_result):
    summary = ""
    num_words = ["zero", "one", "two", "three", "four", "five"]

    for domain in db_supported_domains:

        num_of_result = len(db_result.get(domain, []))
        if num_of_result == 1:
            summary = summary + domain + " one result found. "
        elif num_of_result == 0:
            summary = summary + domain + " no result found. "
        elif num_of_result > 5:
            summary = summary + domain + " more than five results found. "
        else:
            summary = summary + domain + " " + num_words[num_of_result] + " results found. "

    return summary

def get_categorical_value_mapping():
    categorical_value_mapping = {}
    values = ["yes", "no", "free"]
    categorical_value_mapping["parking"] = values

    values = ['saturday', 'tuesday', 'thursday', 'friday', 'monday', 'sunday', 'wednesday']
    categorical_value_mapping["day"] = values

    values = ['japanese', 'asian oriental', 'thai', 'indian', 'chinese', 'seafood', 'french', 'international', 'british',  'portuguese', 'modern european', 'lebanese', 'turkish', 'arab', 'mexican', 'korean', 'european', 'mediterranean', 'spanish', 'vietnamese', 'north american', 'italian', 'african', 'gastropub']
    categorical_value_mapping["food"] = values

    values = ['expensive', 'moderate', 'cheap']
    categorical_value_mapping["pricerange"] = values

    values = ["yes", "no", "free"]
    categorical_value_mapping["internet"] = values

    values = ['multiple sports|theatre', 'swimming', 'multiple sports', 'concert hall', 'musuem', 'nightclub', 'concert', 'churchills college', 'club', 'guesthouse', 'hotel', 'sports', 'hotel|guesthouse', 'special', 'college', 'churchill college', 'architecture', 'museum.and', 'multiple', 'museum kettles yard', 'cinema', 'boat', 'concerthall|boat', 'museum', 'swimmingpool', 'theaters', 'concerthall', 'theatre', 'hiking|historical', 'swimming pool', 'gallery', 'waterpark', 'entertainment', 'park', 'entertainment|cinemas|museums|theatres', 'park or historical building', 'pool', 'theater', 'gastropub', 'sport', 'swiming pool']
    categorical_value_mapping["type"] = values

    values = ['neurosciences critical care unit', 'eurology', 'coronary care unit', 'itermediate deoendancy area', 'infusion', 'clinical research facility', 'haematology day unit', 'cardiology and coronary care unit', 'acute medicine', 'neonatal unit', 'medical decisions unit', "children 's oncology and haematology", 'infectious diseases', 'acute medicine for the elderly', 'medicine for the elderly', "children 's surgical and medicine", 'haematology', 'cardiology', 'truama and orthopaedics', 'psychiatry', 'surgery', 'neurology', 'plastic and vascular surgery', 'infusion service', 'teenage cancer trust unit', 'diabetes and endocrinology', 'gynecology', 'antenatal', 'gastroenterology', 'emergency department', 'haematology and haematological oncology', 'clinical decisions unit', 'neurosciences', 'intermediate dependancy area', 'acute medical assessment unit', 'paediatric intensive care unit', 'transitional care', 'hepatology', 'hepatobillary and gastrointestinal surgery regional referral centre', 'pediatric clinic', 'pediatric day unit', 'inpatient occupational therapy', 'neurology neurosurgery', 'respiratory medicine', 'paediatric clinic', 'john farman intensive care unit', 'urology', 'oral and maxillofacial surgery and ent', 'transplant high dependency unit', 'oncology', 'cambridge eye unit', 'trauma and orthopaedics', 'trauma high dependency unit']
    categorical_value_mapping["department"] = values

    values = ['monday', 'friday', 'saturday', 'sunday>monday', 'wednesday', 'wednesday|friday', 'tuesday', 'sunday|thursday',
     'saturday|thursday', 'sunday', 'friday>tuesday', 'thursday']
    categorical_value_mapping["bookday"] = values

    values = ['5', '4', '4|5', '0', '3|4', '3', '1', '2']
    categorical_value_mapping["stars"] = values

    values = ['west|centre', 'west', 'north', 'south', 'east', 'centre', 'east|south', 'centre|west']
    categorical_value_mapping["area"] = values

    return categorical_value_mapping

categorical_value_mapping = get_categorical_value_mapping()

def state_json_formatter(json_str):
    def is_json(json_str):
        try:
            json.loads(json_str)
        except ValueError as e:
            return False
        return True

    if is_json(json_str):
        old_json = json.loads(json_str)
        new_json = {}
        for domain, sv_pair in old_json.items():
            if type(sv_pair) == type({}):
                new_sv_pair = {}
                for s, v in sv_pair.items():
                    if s in slot_normalisation_mapping.keys():
                        new_sv_pair[s] = v

                new_json[domain] = new_sv_pair
            else:
                new_json[domain] = {}
        return new_json
    else:
        return {}

def find_placeholders(text):
    # Regular expression pattern to find [domain_slot]
    pattern = r'\[[^\]]*\]'
    # Find all occurrences of the pattern
    placeholders = re.findall(pattern, text)

    return placeholders


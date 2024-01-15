# -*- coding: utf-8 -*-
"""
Utterance Evaluation Model for Utterance-level Feedback

This module defines the 'UtteranceEvaluation' class, a Pydantic BaseModel, to represent the evaluation feedback of individual utterances.

It includes attributes for an overall evaluation score, a list of issues (such as 'ungrammatical', 'not engaging'), a proposed correction for the utterance, and an index to identify the utterance's position in the dialogue sequence.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License

Example JSON Data:
{
     "overall": 5,
     "issue": [
         "ungrammatical",
         "notengaging"
     ],
     "correction": "Hello, welcome to the digital assistant system. You can query information about attraction, restaurant, hotels, taxi, Good.",
     "index": 0
}
"""

from pydantic import BaseModel
from typing import List

class UtteranceEvaluation(BaseModel):
    """
    A Pydantic model for representing the evaluation of an utterance in a dialogue system.

    Attributes:
        overall (float): An overall rating given to the utterance.
        issue (List[str]): A list of identified issues with the utterance.
        correction (str): A proposed correction for the utterance.
        idx (int): The index of the utterance in the dialogue sequence.
    """

    overall: float
    issue: List[str]
    correction: str
    idx: int

    def __repr__(self):
        return f'{self.overall},{self.issue},{self.correction},{self.idx}'
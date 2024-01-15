# -*- coding: utf-8 -*-
"""
Utterance Model

This module defines the 'Utterance' class, a Pydantic BaseModel, for representing and analyzing individual utterances
within a dialogue system chat history. The class is designed to encapsulate detailed information about an utterance,
including the the utterance text, its index in the conversation, the speaker (e.g., 'system' or 'user'), and an optional
utterance level evaluation feedback of the utterance, which can include aspects like overall rating, issues identified,
and suggested corrections.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License

Example JSON Data:
[
    {
        "utterance": { "text": "Hello, welcome to the digital assistant...", "idx": 0 },
        "speaker": "system",
        "evaluation": { "overall": 5, "issue": ["ungrammatical", "notengaging"], "correction": "Hello, welcome to..." }
    },
    {
        "utterance": { "text": "Could you recommend an expensive hotel...", "idx": 1 },
        "speaker": "user",
        "evaluation": null
    },
    {
        "utterance": { "text": "Sure, which part of the town...", "idx": 2 },
        "speaker": "system"
    }
]
"""

from pydantic import BaseModel
from typing import Optional

from dao.UtteranceEvaluation import UtteranceEvaluation
from dao.UtteranceDetail import UtteranceDetail


class Utterance(BaseModel):
    """
    A Pydantic model for representing an utterance in a dialogue session.

    Attributes:
        utterance (UtteranceDetail): Detailed information about the utterance including text and index.
        speaker (str): The speaker of the utterance, e.g., 'system' or 'user'.
        evaluation (Optional[UtteranceEvaluation]): An optional evaluation feedback of the utterance.
    """

    utterance: UtteranceDetail
    speaker: str
    evaluation: Optional[UtteranceEvaluation] = None

    def __repr__(self):
        return f'{self.utterance},{self.speaker},{self.evaluation},{self.idx}'
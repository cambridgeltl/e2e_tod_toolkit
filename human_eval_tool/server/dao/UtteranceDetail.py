# -*- coding: utf-8 -*-
"""
Utterance Detail Model

This module defines the 'UtteranceDetail' class, a Pydantic BaseModel, for encapsulating detailed information about individual utterances in a dialogue chat history.

It includes attributes for the utterance text and an optional index indicating the utterance's position within a sequence of dialogue exchanges.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

from pydantic import BaseModel
from typing import Optional

class UtteranceDetail(BaseModel):
    """
    A Pydantic model for representing a textual utterance.

    Attributes:
        text (str): The text of the utterance.
        idx (Optional[int]): An optional index representing the position of the utterance in a sequence of dialogue exchanges.
    """
    text : str
    idx : Optional[int] = None
    def __repr__(self):
        return f'{self.text},{self.idx}'
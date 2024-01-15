# -*- coding: utf-8 -*-
"""
FeedBack Data Model for Dialogue System Evaluation Tool

This module defines the 'FeedBack' class, a Pydantic BaseModel, for handling feedback data in dialogue system evaluations.
The class encapsulates various attributes related to user feedback on dialogues, including an overall rating, an indicator
of whether the system assists the user in accomplishing their goals, a list of properties being evaluated, textual feedback,
the conversation history, the timestamp of feedback creation, and the email of the feedback provider.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License

Example Usage:
The following JSON structure demonstrates how to instantiate the FeedBack class:
{
  "overall": 4,
  "goal": 1,
  "property": [
    "coherence",
    "consistency",
    "understanding",
    "inquisitiveness"
  ],
  "feedback": "Sometimes, a little bit repetitive.",
  "history": [
    {
      "utterance": {
        "text": "Hello, welcome to the digital assistant system...",
        "idx": 0
      },
      "speaker": "system",
      "evaluation": null
    },
    {
      "utterance": {
        "text": "Hi! I want to visit Cambridge. Could you suggest...",
        "idx": null
      },
      "speaker": "user",
      "evaluation": null
    },
    {
      "utterance": {
        "text": "There are 2 expensive hotel in the centre of town...",
        "idx": 1
      },
      "speaker": "system",
      "evaluation": null
    },
    {
      "utterance": {
        "text": "I want one hotel with free parking.",
        "idx": null
      },
      "speaker": "user",
      "evaluation": null
    },
    {
      "utterance": {
        "text": "I have 2 hotel that meet your criteria...",
        "idx": 2
      },
      "speaker": "system",
      "evaluation": {
        "overall": 4,
        "issue": [
          "no"
        ],
        "correction": "I have 2 hotel that meet your criteria...",
        "idx": 2
      }
    }
  ],
  "create_time": {
    "$date": "2023-12-10T04:13:28.499Z"
  },
  "feedback_user": "sh2091@cam.ac.uk"
}
"""

from pydantic import BaseModel
from datetime import datetime
from typing import List
from dao.Utterance import Utterance

class FeedBack(BaseModel):
    """
    A Pydantic model for representing user feedback in dialogue systems.

    Attributes:
        overall (float): An overall rating given to the dialogue interaction.
        goal (float):including an overall rating, an indicator of whether the system assists the user in accomplishing their goals,
        property (List[str]): A list of binary of properties being achieved by the system.
        feedback (str): Textual feedback provided by the user.
        history (List[Utterance]): The conversation history as a list of utterances.
        create_time (datetime): The timestamp when the feedback was created.
        feedback_user (str): The email of the user providing the feedback.
    """

    overall: float
    goal: float
    property: List[str]
    feedback: str
    history: List[Utterance]
    create_time: datetime
    feedback_user: str

    def __repr__(self):
        return f'{self.overall},{self.goal},{self.property},{self.feedback}'
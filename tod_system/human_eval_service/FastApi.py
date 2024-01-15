# -*- coding: utf-8 -*-
"""
FastAPI Server with Celery Integration for System Development

This script creates a FastAPI application to handle requests for generating text based on chat inputs. It integrates with
Celery for asynchronous task processing, allowing tasks to be queued and processed in the background. The application defines
endpoints to initiate text generation tasks and retrieve their results once completed.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

import os
import sys
sys.path.append(os.path.abspath('..'))


from fastapi import FastAPI
from celery.result import AsyncResult
from human_eval_service.celery_worker import generate_text_task
import uvicorn
from pydantic import BaseModel
import os

app = FastAPI()
MODEL_NAME = os.getenv('MODEL_NAME', 'mt5')


class Item(BaseModel):
    """
    Pydantic model to validate request data for text generation.

    Attributes:
        chat (list[str]): Input string based on which text will be generated.
    """
    chat: list[tuple(str,str)]


@app.post("/generate/")
async def generate_text(item: Item) -> dict:
    """
    Endpoint to initiate a text generation task.

    This endpoint accepts a chat input and queues a text generation task in Celery.

    Args:
        item (Item): Input data containing the chat string.

    Returns:
        dict: A dictionary with the task ID of the queued task.
    """

    result = generate_text_task.apply_async(
        args=[item.chat],
        queue=MODEL_NAME+"_dst",
        routing_key=MODEL_NAME+"_dst"
    ).get()

    task2 = generate_text_task.apply_async(
        args=[result],
        queue=MODEL_NAME+"_rg",
        routing_key=MODEL_NAME+"_rg"
    )

    return {"task_id": task2.id}


@app.get("/task/{task_id}")
async def get_task(task_id) -> dict:
    """
    Endpoint to retrieve the result of a text generation task.

    This endpoint checks the status of a Celery task by its ID and returns the result if it's ready.

    Args:
        task_id (str): The ID of the Celery task.

    Returns:
        dict: A dictionary containing the task result or the status of the task.
    """

    result = AsyncResult(task_id)
    if result.ready():
        res = result.get()
        return {"result": res}
    else:
        return {"status": "Task not completed yet"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

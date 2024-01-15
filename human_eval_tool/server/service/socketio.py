# -*- coding: utf-8 -*-
"""
SocketIO Service

This module handles the message communication between the webserver and flask backend.
The socketio service is also used to communicate with the Celery worker and send the generated results 
message to the webserver.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

import logging
import os
from flask_socketio import SocketIO, ConnectionRefusedError
from service.LoginUser import LoginUser
from flask_jwt_extended import decode_token
from flask import request
from celery import chain

chat_histories = {}  # Stores chat history for each session
socket_clients = {}

def socketIO_init(app,celery):
    """
    Initializes a SocketIO instance and defines event handlers for connecting, disconnecting, and processing messages.
    
    Args:
        app: The Flask application object.
        celery: The Celery object for asynchronous task processing.
    
    Returns:
        socketio: The initialized SocketIO instance.
    """
    socketio: SocketIO = SocketIO(app, cors_allowed_origins = '*',logger=True, engineio_logger=True, async_mode = 'eventlet')
    
    @socketio.on('connect')
    def first_check(auth):
        logging.info('WS Client connecting-----------')
        print('WS Client connecting-----------')
        token = auth['token']
        logging.info(token)
        # socketio.emit('system_message','you are connected with sid {}'.format(request.sid),room=request.sid)
        user_id = decode_token(token)
        user_id = user_id['sub']
        logging.info(user_id)
        if user_id:
            user = LoginUser().check_user_with_id(id=user_id)
            logging.info(user.email + '     -----user_email')
            if user:
                socket_clients[user.email] = request.sid
                chat_histories[request.sid] = []
            else:
                raise ConnectionRefusedError('invalid token')
            
        else:
            raise ConnectionRefusedError('Please login first')

    @socketio.on('disconnect')
    def test_disconnect():
        """
        Event handler for when a socket client disconnects.

        This function is called when a socket client disconnects from the server. It logs the disconnection event,
        retrieves the session ID of the disconnected client, removes the client from the list of active socket clients,
        and deletes the chat history associated with the client.

        Parameters:
            None

        Returns:
            None
        """
        logging.info('WS Client disconnect-----------')
        SID = request.sid
        client = [k for k, v in socket_clients.items() if v == SID]
        print(client[0])
        if client:
            socket_clients.pop(client[0])
            chat_histories.pop(SID)

    @socketio.on('user_message')
    def process_message(message):
        """
        Process a user message received through a socket.
        Send the message to the appropriate model for processing.

        Args:
            message (str): The message sent by the user.

        Returns:
            None
        """
        logging.info('new message is {}'.format(message))
        logging.info(f'User message: {message}')
        sid = request.sid

        # Update chat history for this session
        if sid not in chat_histories:
            chat_histories[sid] = []
        chat_histories[sid].append((message,"user"))
        
        if os.getenv('system_type','microservice') == 'microservice':
            dst_queue = os.getenv('dst_model_id','mt5_dst')
            logging.info("dst_queue is {}".format(dst_queue))
            rg_queue = os.getenv('rg_model_id','mt5_rg')
            logging.info("rg_queue is {}".format(rg_queue))
            task_chain = chain(generate_text_task.s(chat_histories[sid]).set(queue = dst_queue )| generate_text_task.s().set(queue = rg_queue))
            task = task_chain.apply_async()
        else:
            e2e_queue = os.getenv('e2e_model_id','mt5_e2e')
            task = generate_text_task.apply_async(args=chat_histories[sid],queue=e2e_queue)
    
        def get_rg(sid):
            while not task.ready():
                socketio.sleep(1)
            res = task.result
            logging.info(res)
            result = res['utt_lex']
            # Update chat history for this session
            if sid in chat_histories:
                chat_histories[sid].append((result,"system"))
            socketio.emit('system_message', result,room=sid)
    
        socketio.start_background_task(target=get_rg, sid =sid)

    @socketio.on_error_default
    def default_error_handler(e):
        print(request.event["message"]) # "my error event"
        print(request.event["args"]) 


    @celery.task(name = 'generate_text_task')     
    def generate_text_task(history):
        """
        A task that generates text based on the provided history.
        It is use to called to send, it does not to be realized in this function
        as it is a celery task and it only need to be realized in the worker side

        Args:
            history (Any): The input history to generate text from.

        Returns:
            None: This function doesn't return anything.
        """
        logging.info('the message process start {}'.format(history))
        pass
    return socketio
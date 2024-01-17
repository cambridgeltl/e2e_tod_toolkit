# -*- coding: utf-8 -*-
"""
Flask App for Human Evaluation Tool, the entrence point of the backend.
"""

import json
import os
from datetime import datetime, timedelta
import logging
from logging.config import dictConfig

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, get_jwt, create_access_token, get_jwt_identity
from init import bcrypt, jwt, pymongo, cors, make_celery, adminpymongo
from service.LoginUser import LoginUser
from view.authentication import auth
from service.socketio import socketIO_init
from dotenv import load_dotenv


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

# load environment variables
load_dotenv()

# initalize flask app
app = Flask(__name__)
app.register_blueprint(auth, url_prefix='/api')

# config the app
app.config.update({
    'DEBUG': True,
    'JWT_SECRET_KEY': os.getenv('SECRET_KEY', 'THISWILLBECHANGELATERON'),
    'JWT_TOKEN_LOCATION': 'headers',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'SOCKETIOSECRETKEY'),
    'JWT_ACCESS_TOKEN_EXPIRES': timedelta(minutes=60),
    'MONGO_URI': os.getenv('MONGO_URI', 'mongodb://localhost:27017/human_eval_tool'),
    'CORS_HEADERS': 'Content-Type'
})


def page_not_found(e):
    """Custom error handling for 404"""
    return jsonify({"error": "page not found"})

# init all the service
bcrypt.init_app(app)
jwt.init_app(app)
adminpymongo.init_app(app,uri=os.getenv('MONGO_URI', 'mongodb://localhost:27017/human_eval_tool')+"/admin")
pymongo.init_app(app,uri=os.getenv('MONGO_URI', 'mongodb://localhost:27017/human_eval_tool')+"/"+os.getenv('MODEL_NAME','mt5'))
cors.init_app(app)

celery = make_celery(app)
# celery = make_celery("./config/config.cfg",app)
socketd = socketIO_init(app,celery)
app.register_error_handler(404, page_not_found)
adminpymongo.db.command("updateUser", "admin", pwd=os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'Humaneval12345'), roles=[{"role": "dbOwner", "db": os.getenv('MODEL_NAME','mt5')}])
logging.getLogger('flask_cors').level = logging.DEBUG

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        current_identity = get_jwt_identity()
        current_user = LoginUser().check_user_with_id(current_identity)

        now = datetime.now()
        target_timestamp = datetime.timestamp(now + timedelta(minutes=60))
        if target_timestamp > exp_timestamp:
            new_access_token = create_access_token(
                identity=current_identity,
                additional_claims={"role": current_user.role.model_dump()}
            )

            data = response.get_json()
            if isinstance(data, dict):
                data["access_token"] = new_access_token
                response = jsonify(data)

        return response
    except (RuntimeError, KeyError):
        return response

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    socketd.run(app, host='0.0.0.0', port=5000)
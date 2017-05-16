from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt import JWT, _default_jwt_payload_handler
from config import config

db = SQLAlchemy()


def authenticate(username, password):
    """ We will never authenticate a user from this sevice """
    return None


def identity(payload):
    return payload['identity']


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    db.create_all()
    from .api import api
    api.init_app(app)
    jwt = JWT(app, authenticate, identity)

    return app

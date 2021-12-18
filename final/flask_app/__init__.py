# 3rd-party packages
from flask import Flask, render_template, request, redirect, url_for
from flask_mongoengine import MongoEngine
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required,
)
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message

# stdlib
from datetime import datetime
import os

# local
from .client import PokeClient

MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "pokemonleague107@gmail.com"
MAIL_PASSWORD = "P0k3league"
MAIL_DEFAULT_SENDER = 'pokemonleague107@gmail.com'

db = MongoEngine()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
poke_client = PokeClient()
# might not need this 
# poke_client = PokeClient(os.environ.get("OMDB_API_KEY"))

from .users.routes import users
from .pokemon.routes import pokemon

def page_not_found(e):
    return render_template("404.html"), 404


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_pyfile("config.py", silent=False)
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    mail.init_app(app)

    app.register_blueprint(users)
    app.register_blueprint(pokemon)
    app.register_error_handler(404, page_not_found)

    login_manager.login_view = "users.login"

    return app

app = create_app()
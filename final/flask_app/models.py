from flask_login import UserMixin
from datetime import datetime
from . import db, login_manager
from . import config
from .utils import current_time
import base64


@login_manager.user_loader
def load_user(user_id):
    return User.objects(username=user_id).first()


class User(db.Document, UserMixin):
    username = db.StringField(required=True, unique=True)
    email = db.EmailField(required=True, unique=True)
    password = db.StringField(required=True)
    pfp = db.ImageField()

    team = db.ListField(
        base_field=db.StringField(),
        size=6,  # Maximum of 100 ids in list
    )

    # Returns unique string identifying our object
    def get_id(self):
        return self.username


class Review(db.Document):
    Trainer = db.ReferenceField(User, required=True)
    content = db.StringField(required=True, min_length=5, max_length=500)
    date = db.StringField(required=True)
    pokemon = db.StringField(required=True)

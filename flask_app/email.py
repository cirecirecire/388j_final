from flask_mail import Mail, Message
from flask_app import mail
from . import config


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender='pokemonleague107@gmail.com'
    )
    mail.send(msg)
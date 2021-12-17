from itsdangerous import URLSafeTimedSerializer, SignatureExpired

from . import config
import flask_app


def generate_confirmation_token(email):
    serial = URLSafeTimedSerializer('serialserialserial')
    return serial.dumps(email, salt='email_confirm')


def confirm_token(token, expiration=5000):
    serial = URLSafeTimedSerializer('serialserialserial')
    try:
        email = serial.loads(
            token,
            salt='email_confirm',
            max_age=expiration
        )
    except SignatureExpired:
        return False
    return email

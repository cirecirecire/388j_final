from flask import session, request
from mongoengine.errors import ValidationError
import pytest

from types import SimpleNamespace

from flask_app.forms import RegistrationForm, UpdateUsernameForm, LoginForm
from flask_app.models import User


def test_register(client, auth):
    """ Test that registration page opens up """
    resp = client.get("/register")
    assert resp.status_code == 200

    response = auth.register()

    assert response.status_code == 200
    user = User.objects(username="test").first()

    assert user is not None


@pytest.mark.parametrize(
    ("username", "email", "password", "confirm", "message"),
    (
        ("test", "test@email.com", "test", "test", b"Username is taken"),
        ("p" * 41, "test@email.com", "test", "test", b"Field must be between 1 and 40"),
        ("username", "test", "test", "test", b"Invalid email address."),
        ("username", "test@email.com", "test", "test2", b"Field must be equal to"),
    ),
)
def test_register_validate_input(auth, username, email, password, confirm, message):
    if message == b"Username is taken":
        auth.register()

    response = auth.register(username, email, password, confirm)

    assert message in response.data


def test_login(client, auth):
    """ Test that login page opens up """
    resp = client.get("/login")
    assert resp.status_code == 200

    auth.register()
    auth.login()

    with client:
        client.get("/")
        assert session["_user_id"] == "test"


@pytest.mark.parametrize(
    ("username", "password", "message"), 
    (
        ("", "test", b"This field is required"),
        ("test", "", b"This field is required"),
        ("yuh", "test", b"Login failed"),
        ("test", "yuh", b"Login failed")
    )
    )
def test_login_input_validation(auth, username, password, message):
    auth.register()
    assert message in auth.login(username=username, password=password).data


def test_logout(client, auth):
    auth.register()
    auth.login()

    response = client.get('/account', follow_redirects=True)
    assert response.status_code == 200

    auth.logout()
    resp = client.get('/account', follow_redirects=True)
    assert resp.status_code == 200 #check this


def test_change_username(client, auth):
    assert client.get("/account").status_code == 302

    user = SimpleNamespace(username = "test", submit="Update Username")
    form = UpdateUsernameForm(username = "ariana", submit="Update Username")
    client.post("/account", data=form.data, follow_redirects=True)
    assert "ariana" in form.username.data
    assert User.objects(username=user.username) is not None


def test_change_username_taken(client, auth):
    assert client.get("/account").status_code == 302

    user = SimpleNamespace(Username = "test", submit="Update Username")
    form = UpdateUsernameForm(formdata=None, obj=user)
    client.post("/account", data=form.data, follow_redirects=True)

    same_user = SimpleNamespace(Username = "test", submit="Update Username")
    form = UpdateUsernameForm(formdata=None, obj=same_user)

    try:
        client.post("/account", data=form.data, follow_redirects=True)
    except ValidationError as e:
        assert b"That username is already taken" == e.message


@pytest.mark.parametrize(
    ("new_username", "message"), 
    (
        ("", b"This field is required."),
        ("a" * 41, b"Field must be between 1 and 40 characters long")
    )
)
def test_change_username_input_validation(client, auth, new_username, message):
    assert client.get("/account").status_code == 302

    user = SimpleNamespace(Username = new_username, submit="Update Username")
    form = UpdateUsernameForm(formdata=None, obj=user)

    try:
        client.post("/account", data=form.data, follow_redirects=True)
    except ValueError as err:
        assert message == err.message

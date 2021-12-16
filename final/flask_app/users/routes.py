from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_required, login_user, logout_user
from flask_mongoengine import MongoEngine

from .. import bcrypt
from ..forms import RegistrationForm, LoginForm, UpdateUsernameForm, UpdateProfilePicForm, ValidationError, AddPokemonForm
from ..models import User, TeamMember

import io
import base64


users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("pokemon.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        user.save()

        return redirect(url_for("users.login"))

    return render_template("register.html", title="Register", form=form)

@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("pokemon.index"))

    form = LoginForm()
    try:
        if form.validate_on_submit():
            user = User.objects(username=form.username.data).first()

            if user is not None and bcrypt.check_password_hash(
                user.password, form.password.data
            ):
                login_user(user)
                return redirect(url_for("users.account"))
            else:
                flash("Login failed. Check your username and/or password")
                return redirect(url_for("users.login"))
    except (ValidationError, ValueError) as e:
        return redirect(url_for('login'), error=str(e))

    return render_template("login.html", title="Login", form=form)


def get_b64_img(username):
    user = User.objects(username=username).first()
    bytes_im = io.BytesIO(user.pfp.read())
    image = base64.b64encode(bytes_im.getvalue()).decode()
    return image

@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    update_user_form = UpdateUsernameForm()
    pfp_update_form = UpdateProfilePicForm() 

    try: 
        if update_user_form.validate_on_submit(): #I believe it will already validate username doesn't exist
            current_user.modify(username=update_user_form.username.data)
            current_user.save()
            return redirect(request.path)
        
        if pfp_update_form.validate_on_submit():
            img = pfp_update_form.pfp.data
            content_type = 'images/jpg'

            if current_user.pfp.get() is None:
                current_user.pfp.put(img.stream, content_type=content_type)
            else:
                current_user.pfp.replace(img.stream, content_type=content_type)
            current_user.save()

            return redirect(url_for('users.account'))
    except (ValidationError, ValueError) as e:
        return redirect(url_for('login'), error=str(e))

    image = get_b64_img(current_user.username)

    return render_template(
        "account.html",
        title="Account",
        username_form=update_user_form,
        pfp_update_form=pfp_update_form, 
        image=image
    )

@users.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("pokemon.index"))

@users.route("/user/<username>")
def user_detail(username):
    user = User.objects(username=username).first()
    team = user.team

    return render_template("user_detail.html", username=username, team=team, image=get_b64_img(username))

@users.route('/<username>/team', methods=['GET', 'POST'])
def team(username):
    form = AddPokemonForm()

    if form.validate_on_submit():
        team = TeamMember(
            trainer = current_user,
            pokemon = form.pokemon.data,
        )
        team.save()
        #current_user.modify(username=update_user_form.username.data)
        #    current_user.save()
        return redirect(request.path)

    members = TeamMember.objects(trainer=current_user)

    return render_template("team_detail.html", trainer=username, form=form, team=members)
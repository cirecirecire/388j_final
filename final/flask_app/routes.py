# 3rd-party packages
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Blueprint,
    session,
    g,
)
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

# stdlib
from datetime import datetime
import io
import base64

# local
from . import bcrypt, movie_client
from .forms import (
    SearchForm,
    MovieReviewForm,
    RegistrationForm,
    LoginForm,
    UpdateUsernameForm,
    UpdateProfilePicForm,
    ValidationError,
)
from .models import User, Review, load_user
from .utils import current_time


main = Blueprint("main", __name__)


""" ************ View functions ************ """


@main.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for("main.query_results", query=form.search_query.data))

    return render_template("index.html", form=form)


@main.route("/search-results/<query>", methods=["GET"])
def query_results(query):
    try:
        results = movie_client.search(query)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("main.index"))

    return render_template("query.html", results=results)


@main.route("/movies/<movie_id>", methods=["GET", "POST"])
def movie_detail(movie_id):
    try:
        result = movie_client.retrieve_movie_by_id(movie_id)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("main.login"))

    form = MovieReviewForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        review = Review(
            commenter=current_user._get_current_object(),
            content=form.text.data,
            date=current_time(),
            imdb_id=movie_id,
            movie_title=result.title,
        )
        review.save()

        return redirect(request.path)

    reviews = Review.objects(imdb_id=movie_id)
    review_pfps = {review.commenter.username : get_b64_img(review.commenter.username) for review in reviews}

    return render_template(
        "movie_detail.html", form=form, movie=result, reviews=reviews, review_pfps=review_pfps
    )

def get_b64_img(username):
    user = User.objects(username=username).first()
    bytes_im = io.BytesIO(user.pfp.read())
    image = base64.b64encode(bytes_im.getvalue()).decode()
    return image


@main.route("/user/<username>")
def user_detail(username):
    try:
        user = User.objects(username=username).first()
        reviews = Review.objects(commenter=user)
        image = get_b64_img(username)
    except AttributeError as e: #if username isn't there, get_b64_img 
        return redirect(url_for('index'))
    return render_template('user_detail.html', username=user, reviews=reviews, image=image)


""" ************ User Management views ************ """


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        user.save()

        return redirect(url_for("main.login"))

    return render_template("register.html", title="Register", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    try:
        if form.validate_on_submit():
            user = User.objects(username=form.username.data).first()

            if user is not None and bcrypt.check_password_hash(
                user.password, form.password.data
            ):
                login_user(user)
                return redirect(url_for("main.account"))
            else:
                flash("Login failed. Check your username and/or password")
                return redirect(url_for("main.login"))
    except (ValidationError, ValueError) as e:
        return redirect(url_for('login'), error=str(e))

    return render_template("login.html", title="Login", form=form)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/account", methods=["GET", "POST"])
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
            filename = secure_filename(img.filename)
            content_type = 'images/jpg'

            if current_user.pfp.get() is None:
                current_user.pfp.put(img.stream, content_type=content_type)
            else:
                current_user.pfp.replace(img.stream, content_type=content_type)
            current_user.save()

            return redirect(url_for('account'))
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

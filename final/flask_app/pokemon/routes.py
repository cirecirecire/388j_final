from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user

from .. import poke_client
from ..forms import PokemonReviewForm, SearchForm, AddPokemonForm, RemovePokemonForm
from ..models import User, Review
from ..utils import current_time

pokemon = Blueprint('pokemon', __name__)

@pokemon.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for("pokemon.pokemon_detail", pokemon=form.search_query.data))

    return render_template("index.html", form=form)


@pokemon.route("/search-results/<query>", methods=["GET"])
def query_results(query):
    try:
        results = poke_client.get_pokemon_info(query)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("pokemon.index"))

    return render_template("pokemon_detail.html", results=results)


@pokemon.route("/pokemon/<pokemon>", methods=["GET", "POST"])
def pokemon_detail(pokemon):
    try:
        result = poke_client.get_pokemon_info(pokemon)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("users.login"))

    addForm = AddPokemonForm()
    if addForm.validate_on_submit() and current_user.is_authenticated:
        user = User.objects.get(username=current_user.username)
        user.team = user.team.append(pokemon)
        user.save()

        return redirect(url_for("users.account"))

    form = PokemonReviewForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        if len(form.text.data) >= 5:
            review = Review(
                Trainer=current_user._get_current_object(),
                content=form.text.data,
                date=current_time(),
                pokemon=pokemon,
            )
            review.save()
            return redirect(request.path)

    reviews = Review.objects(pokemon=pokemon)
    return render_template(
        "pokemon_detail.html", pokemon=result, reviews=reviews, addForm = addForm, form=form)

@pokemon.route("/user/<username>")
def user_detail(username):
    user = User.objects(username=username).first()
    reviews = Review.objects(Trainer=user)

    team = user.team

    return render_template("user_detail.html", username=username, reviews=reviews, team=team)

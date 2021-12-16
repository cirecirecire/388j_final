from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user

from .. import poke_client
from ..forms import SearchForm, AddPokemonForm, RemovePokemonForm
from ..models import User, Team
from ..utils import current_time

teams = Blueprint('teams', __name__)

@teams.route('/teams/<username>', methods=['GET', 'POST'])
def team(trainer):
    form = AddPokemonForm()

    team = Team.objects(trainer=trainer)

    if form.validate_on_submit():
        return redirect(request.path)

    return render_template("team.html", trainer=trainer, form=form, team=team)


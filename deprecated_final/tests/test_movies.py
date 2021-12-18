import pytest

from types import SimpleNamespace
import random
import string

from flask_app.forms import SearchForm, MovieReviewForm
from flask_app.models import User, Review

def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200

    search = SimpleNamespace(search_query="guardians", submit="Search")
    form = SearchForm(formdata=None, obj=search)
    response = client.post("/", data=form.data, follow_redirects=True)

    assert b"Guardians of the Galaxy" in response.data

@pytest.mark.parametrize(
    ("query", "message"), 
    (
        ("", b"This field is required."),
        ("a", b"Too many results"),
        ("lkjhvtds34edfgujbik876rdcvbnmkjhg", b"Movie not found"),
        ("a"*150, b"Field must be between 1 and 100 characters long")
    )
)
def test_search_input_validation(client, query, message):
    assert client.get("/").status_code == 200

    search = SimpleNamespace(search_query=query, submit="Search")
    form = SearchForm(formdata=None, obj=search)
    response = client.post("/", data=form.data, follow_redirects=True)
    assert message in response.data

def test_movie_review(client, auth):
    guardians_id = "tt2015381"
    url = f"/movies/{guardians_id}"

    assert client.get(url).status_code == 200

    auth.register()
    auth.login()

    name = ''.join(random.choices(string.ascii_letters + string.digits, k= 50))
    review = SimpleNamespace(text=name, submit="Enter Comment")
    form = MovieReviewForm(formdata=None, obj=review)
    response = client.post(url, data=form.data)

    assert review.text in form.text.data
    assert Review.objects(imdb_id=guardians_id, review=review) is not None

@pytest.mark.parametrize(
    ("movie_id", "message"), 
    (
        ("", 404),
        ("bb", b"Incorrect IMDb ID"),
        ("bbbbbbbbb", b"Incorrect IMDb ID"),
        ("bbbbbbbbbb", b"Incorrect IMDb ID"),
    )
)
def test_movie_review_redirects(client, movie_id, message):
    url = f"/movies/{movie_id}"
    response = client.get(url) # might have to set follow_directs = false
    if movie_id == "":
        assert response.status_code == 404
    else:
        assert response.status_code == 302

@pytest.mark.parametrize(
    ("comment", "message"), 
    (
        ("", b"This field is required"),
        ("a"*1, b"Field must be between 5 and 500 characters long"),
        ("a"*501, b"Field must be between 5 and 500 characters long"),
    )
)

def test_movie_review_input_validation(client, auth, comment, message):
    guardians_id = "tt2015381"
    url = f"/movies/{guardians_id}"

    auth.register()
    auth.login()

    review = SimpleNamespace(text=comment, submit="Enter Comment")
    form = MovieReviewForm(formdata=None, obj=review)

    assert message in client.post(url, data=form.data, follow_redirects=True).data
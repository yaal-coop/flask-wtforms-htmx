from __future__ import annotations

import pytest
from flask import Flask
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import generate_csrf
from wtforms import ButtonField
from wtforms import FieldList
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms_htmx.mutations import list_add

from flask_wtforms_htmx import HtmxFlaskForm
from flask_wtforms_htmx import jinja_renderer


class TagsForm(HtmxFlaskForm):
    tags = FieldList(StringField(validators=[DataRequired()]), min_entries=1)
    add_tag = ButtonField("+").triggers("tags", list_add)
    save = SubmitField("Save")
    cancel = SubmitField("Cancel")


@pytest.fixture
def app():
    """App with a Flask-WTF style view that records each save."""
    app = Flask(__name__)
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test"
    app.saved = []  # type: ignore[attr-defined]

    @app.route("/tags", methods=["GET", "POST"])
    def tags():
        form = TagsForm()
        if form.validate_on_submit():
            app.saved.append([e.data for e in form.tags])  # type: ignore[attr-defined]
            return "saved"

        return "rendered"

    @app.post("/strict")
    def strict():
        form = TagsForm()
        if form.validate_on_submit(submitter=form.save):
            return "saved"

        return "rendered"

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_does_not_save(client):
    """A GET request does not save."""
    assert client.get("/tags").data == b"rendered"


def test_save_button_saves(client, app):
    """A click on a plain submit button saves the form."""
    resp = client.post("/tags", data={"tags-0": "python", "save": ""})
    assert resp.data == b"saved"
    assert app.saved == [["python"]]


def test_submit_without_button_saves(client):
    """A submit that names no button saves the form."""
    assert client.post("/tags", data={"tags-0": "python"}).data == b"saved"


def test_invalid_form_does_not_save(client):
    """An invalid form does not save."""
    assert client.post("/tags", data={"tags-0": "", "save": ""}).data == b"rendered"


def test_mutation_click_without_js_does_not_save(client, app):
    """A no-JS click on a button with triggers does not save."""
    resp = client.post("/tags", data={"tags-0": "python", "add_tag": ""})
    assert resp.data == b"rendered"
    assert app.saved == []


def test_mutation_click_with_htmx_sends_the_partial(client, app):
    """An htmx click on a button with triggers returns the partial response."""
    resp = client.post(
        "/tags",
        data={"tags-0": "python", "add_tag": ""},
        headers={"HX-Request": "true", "HX-Source": "button#add_tag"},
    )
    body = resp.get_data(as_text=True)
    assert 'id="tags-1"' in body
    assert app.saved == []


def test_inline_validation_sends_the_partial(client):
    """An htmx request from a field returns its inline validation."""
    resp = client.post(
        "/tags",
        data={"tags-0": ""},
        headers={"HX-Request": "true", "HX-Source": "input#tags-0"},
    )
    body = resp.get_data(as_text=True)
    assert body.startswith("<input")
    assert 'id="tags-0"' in body


def test_submitter_restricts_the_save_button(client):
    """With submitter=, another plain button does not save."""
    assert (
        client.post("/strict", data={"tags-0": "x", "cancel": ""}).data == b"rendered"
    )
    assert client.post("/strict", data={"tags-0": "x", "save": ""}).data == b"saved"


def test_form_outside_a_request_has_no_headers(app):
    """Outside a request, the form builds without htmx headers."""
    with app.app_context():
        form = TagsForm(meta={"csrf": False})

    assert form.partial() is None


def test_jinja_renderer_template(tmp_path):
    """jinja_renderer(template) renders the template with field and render_kw."""
    (tmp_path / "_field.html").write_text(
        "<div id=\"wrap-{{ field.id }}\">{{ render_kw['data-x'] }}</div>"
    )
    app = Flask(__name__, template_folder=str(tmp_path))

    class Form(HtmxFlaskForm):
        class Meta:
            csrf = False
            field_wrapper = staticmethod(jinja_renderer("_field.html"))

        name = StringField("Name")

    with app.test_request_context():
        out = str(Form().name(**{"data-x": "ok"}))

    assert 'id="wrap-name"' in out
    assert "ok" in out


def test_jinja_renderer_macro(tmp_path):
    """jinja_renderer(template, macro) calls the macro."""
    (tmp_path / "_macros.html").write_text(
        "{% macro render_field(field, render_kw) %}"
        '<section id="{{ field.id }}-section">{{ field.label.text }}</section>'
        "{% endmacro %}"
    )
    app = Flask(__name__, template_folder=str(tmp_path))

    class Form(HtmxFlaskForm):
        class Meta:
            csrf = False
            field_wrapper = staticmethod(jinja_renderer("_macros.html", "render_field"))

        title = StringField("My title")

    with app.test_request_context():
        out = str(Form().title())

    assert 'id="title-section"' in out
    assert "My title" in out


@pytest.fixture
def csrf_app():
    """App with CSRF on, a view that saves the form, and one that gives a token."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    app.saved = []  # type: ignore[attr-defined]

    @app.route("/tags", methods=["GET", "POST"])
    def tags():
        form = TagsForm()
        if form.validate_on_submit():
            app.saved.append([e.data for e in form.tags])  # type: ignore[attr-defined]
            return "saved"

        return f"rendered {form.errors}"

    @app.get("/token")
    def token():
        return generate_csrf()

    return app


def test_csrf_htmx_mutation_without_token_is_rejected(csrf_app):
    """An htmx mutation without a CSRF token gets a 400 and no partial."""
    resp = csrf_app.test_client().post(
        "/tags",
        data={"tags-0": "python", "add_tag": ""},
        headers={"HX-Request": "true", "HX-Source": "button#add_tag"},
    )
    assert resp.status_code == 400
    assert resp.headers["HX-Reswap"] == "none"
    assert 'id="tags-1"' not in resp.get_data(as_text=True)


def test_csrf_rejection_goes_through_the_app_error_handler(csrf_app):
    """The app's CSRFError handler answers a rejected htmx request."""

    @csrf_app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        return f"handled: {error.description}", 400

    resp = csrf_app.test_client().post(
        "/tags",
        data={"tags-0": "python", "add_tag": ""},
        headers={"HX-Request": "true", "HX-Source": "button#add_tag"},
    )
    assert resp.get_data(as_text=True) == "handled: The CSRF token is missing."


def test_csrf_inline_validation_without_token_is_rejected(csrf_app):
    """An htmx request from a field without a CSRF token gets a 400."""
    resp = csrf_app.test_client().post(
        "/tags",
        data={"tags-0": ""},
        headers={"HX-Request": "true", "HX-Source": "input#tags-0"},
    )
    assert resp.status_code == 400


def test_csrf_mutation_click_without_js_and_token_is_rejected(csrf_app):
    """A no-JS click on a button with triggers and no CSRF token gets a 400."""
    resp = csrf_app.test_client().post("/tags", data={"tags-0": "a", "add_tag": ""})
    assert resp.status_code == 400


def test_csrf_plain_submit_with_token_saves(csrf_app):
    """A plain submit with a valid CSRF token saves the form."""
    client = csrf_app.test_client()
    token = client.get("/token").get_data(as_text=True)
    resp = client.post(
        "/tags", data={"tags-0": "python", "save": "", "csrf_token": token}
    )
    assert resp.get_data(as_text=True) == "saved"
    assert csrf_app.saved == [["python"]]


def test_csrf_plain_submit_without_token_shows_the_error(csrf_app):
    """A plain submit without a CSRF token renders the form with the error."""
    resp = csrf_app.test_client().post("/tags", data={"tags-0": "python", "save": ""})
    assert resp.status_code == 200
    assert "The CSRF token is missing." in resp.get_data(as_text=True)
    assert csrf_app.saved == []


def test_csrf_htmx_mutation_with_token_sends_the_partial(csrf_app):
    """An htmx mutation with a valid CSRF token gets the partial."""
    client = csrf_app.test_client()
    token = client.get("/token").get_data(as_text=True)
    resp = client.post(
        "/tags",
        data={"tags-0": "python", "add_tag": "", "csrf_token": token},
        headers={"HX-Request": "true", "HX-Source": "button#add_tag"},
    )
    assert resp.status_code == 200
    assert 'id="tags-1"' in resp.get_data(as_text=True)


def test_csrf_boosted_submit_without_token_shows_the_error(csrf_app):
    """A boosted submit without a CSRF token renders the form with the error."""
    resp = csrf_app.test_client().post(
        "/tags",
        data={"tags-0": "python", "save": ""},
        headers={"HX-Request": "true", "HX-Boosted": "true"},
    )
    assert resp.status_code == 200
    assert "The CSRF token is missing." in resp.get_data(as_text=True)

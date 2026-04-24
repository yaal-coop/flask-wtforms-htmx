Quickstart
==========

This page is for Flask-WTF users who add htmx to their forms. It covers
what the Flask adapter adds to the core: :class:`~flask_wtforms_htmx.HtmxFlaskForm`
and :func:`~flask_wtforms_htmx.jinja_renderer`. It assumes you know
Flask-WTF. The htmx patterns themselves (inline validation, datalists,
mutations) are in the `wtforms-htmx guides`_.

.. _wtforms-htmx guides: https://wtforms-htmx.readthedocs.io/en/latest/how-to/

Install
-------

.. code-block:: shell

    pip install flask-wtforms-htmx

This also installs :external+wtforms:doc:`WTForms <index>`,
:external+flask-wtf:doc:`Flask-WTF <index>` and
:external+wtforms-htmx:doc:`wtforms-htmx <index>`.

Use ``HtmxFlaskForm``
---------------------

Inherit from :class:`~flask_wtforms_htmx.HtmxFlaskForm` instead of
:class:`~flask_wtf.FlaskForm`:

.. code-block:: python

    from flask_wtforms_htmx import HtmxFlaskForm
    from wtforms_htmx.mutations import list_add

    class TagsForm(HtmxFlaskForm):
        tags = FieldList(StringField(), min_entries=1)
        add_tag = ButtonField("+").triggers("tags", list_add)
        save = SubmitField("Save")

Write the view as with a plain :class:`~flask_wtf.FlaskForm`:

.. code-block:: python

    @app.route("/tags", methods=["GET", "POST"])
    def tags():
        form = TagsForm()
        if form.validate_on_submit():
            save(form.data)
            return redirect(url_for("tags"))

        return render_template("tags.html", form=form)

The form reads the htmx request headers itself.
:meth:`~flask_wtforms_htmx.HtmxFlaskForm.validate_on_submit` then
handles the htmx cases:

- On an htmx request with a partial response (inline validation, datalist
  refresh, mutation), it sends that response with :func:`flask.abort`. The
  rest of the view does not run.
- Without JavaScript, a click on a button with
  :meth:`.triggers() <wtforms.fields.core.UnboundField.triggers>` posts the
  whole form. The mutation runs, but the form is not saved: the method
  returns ``False`` and the view renders the page again.

Save with one button only
-------------------------

When the form has other plain submit buttons, pass the save button:

.. code-block:: python

    if form.validate_on_submit(submitter=form.save):
        save(form.data)

Any other button, such as a "Cancel" button, then returns ``False``.

CSRF protection
---------------

CSRF protection works as with Flask-WTF. The htmx requests send the
``csrf_token`` field with the rest of the form. With an invalid token:

- An htmx request, or a click on a button with
  :meth:`.triggers() <wtforms.fields.core.UnboundField.triggers>`, gets a
  400 response (:class:`~flask_wtf.csrf.CSRFError`). No callback runs,
  and htmx leaves the page as it is. An ``@app.errorhandler(CSRFError)``
  handler replaces this response.
- A plain submit returns ``False`` from
  :meth:`~flask_wtforms_htmx.HtmxFlaskForm.validate_on_submit`, and the
  form shows the error.

A token expires after one hour by default. On a page left open longer,
interactions then do nothing. To keep the token valid for the whole
session, set ``WTF_CSRF_TIME_LIMIT = None``.

Render fields with Jinja
------------------------

The core renders each field through ``Meta.field_wrapper``, a callable
``(field, render_kw) -> str``. :func:`~flask_wtforms_htmx.jinja_renderer`
builds this callable from a Jinja template or macro.

A template gets ``field`` and ``render_kw`` in its context:

.. code-block:: jinja

    {# templates/_field.html #}
    <div id="wrap-{{ field.id }}" class="field">
      {{ field.label() }}
      {{ field.widget(field, **render_kw) }}
      {% if field.errors %}
      <ul class="errors">
        {% for error in field.errors %}<li>{{ error }}</li>{% endfor %}
      </ul>
      {% endif %}
    </div>

.. code-block:: python

    from flask_wtforms_htmx import HtmxFlaskForm, jinja_renderer

    class ProfileForm(HtmxFlaskForm):
        class Meta:
            field_wrapper = staticmethod(jinja_renderer("_field.html"))

        name = StringField("Name", validators=[DataRequired()])

A macro gets ``(field, render_kw)`` as arguments, so one template can
hold several wrappers:

.. code-block:: python

    class ProfileForm(HtmxFlaskForm):
        class Meta:
            field_wrapper = staticmethod(
                jinja_renderer("_macros.html", "render_field")
            )

To use another wrapper for one field, pass it to the field with
``wrapper=``:

.. code-block:: python

    bio = TextAreaField("Bio", wrapper=jinja_renderer("_macros.html", "render_textarea"))

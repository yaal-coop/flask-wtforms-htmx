# flask-wtforms-htmx

A drop-in `FlaskForm` that brings
[wtforms-htmx](https://wtforms-htmx.readthedocs.io/) to
[Flask-WTF](https://flask-wtf.readthedocs.io/).

**Status: alpha, work in progress.**

`HtmxFlaskForm` replaces Flask-WTF's `FlaskForm`. The usual
`validate_on_submit()` view answers htmx requests, and a mutation click
without JavaScript does not save the form. CSRF protection and file
uploads work as with Flask-WTF.

## Installation

```sh
pip install flask-wtforms-htmx
```

## Example

```python
from flask import redirect, render_template, url_for
from wtforms import ButtonField, FieldList, StringField, SubmitField
from wtforms_htmx.mutations import list_add

from flask_wtforms_htmx import HtmxFlaskForm


class TagsForm(HtmxFlaskForm):
    tags = FieldList(StringField(), min_entries=1)
    add_tag = ButtonField("+").triggers("tags", list_add)
    save = SubmitField("Save")


@app.route("/tags", methods=["GET", "POST"])
def tags():
    form = TagsForm()
    if form.validate_on_submit():
        save(form.data)
        return redirect(url_for("tags"))

    return render_template("tags.html", form=form)
```

With htmx, a click on `+` adds a row without reloading the page. Without
JavaScript, it reloads the page with the new row, and the form is not
saved.

## Links

- Documentation: <https://flask-wtforms-htmx.readthedocs.io/>
- Source: <https://github.com/yaal-coop/flask-wtforms-htmx>
- Issues: <https://github.com/yaal-coop/flask-wtforms-htmx/issues>

## License

BSD-3-Clause. See `LICENSE.rst`.

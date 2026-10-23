"""A drop-in FlaskForm that brings wtforms-htmx to Flask-WTF."""

from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from flask import abort
from flask import current_app
from flask import has_request_context
from flask import render_template
from flask import request
from flask import Response
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFError
from markupsafe import Markup
from wtforms_htmx import HtmxFormMixin

if TYPE_CHECKING:
    from collections.abc import Callable


class HtmxFlaskForm(HtmxFormMixin, FlaskForm):
    """Drop-in replacement for :class:`~flask_wtf.FlaskForm` that answers htmx requests.

    The form reads the request headers itself, so the view does not pass
    ``headers=``.

    With an invalid CSRF token, htmx requests and clicks on a button with
    :meth:`.triggers() <wtforms.fields.core.UnboundField.triggers>` get a
    400 response (:class:`~flask_wtf.csrf.CSRFError`), and no callback runs.
    htmx leaves the page as it is. A plain submit shows the error in the
    form, as with Flask-WTF.
    """

    def __init__(self, *args, headers=None, **kwargs):
        if headers is None and has_request_context():
            headers = request.headers

        super().__init__(*args, headers=headers, **kwargs)

    def mutate(self) -> None:
        """Run the mutations, or abort with a 400 when the CSRF token blocks them."""
        super().mutate()
        if not self.meta.csrf:
            return

        errors = self[self.meta.csrf_field_name].errors
        if not errors or not self._is_interaction():
            return

        # htmx 4 swaps 4xx responses by default: keep the page as it is.
        response = Response(errors[0], status=400, headers={"HX-Reswap": "none"})
        raise CSRFError(errors[0], response=response)

    def _is_interaction(self) -> bool:
        """Return True for an htmx request or a click on a button with triggers."""
        if self.submitter is not None and self.htmx_submit_attrs(self.submitter):
            return True

        return "HX-Request" in request.headers and "HX-Boosted" not in request.headers

    def validate_on_submit(
        self, extra_validators=None, *, submitter: Any = None
    ) -> bool:
        """Validate the form when the user saves it.

        On an htmx request with a partial response, :func:`flask.abort` sends
        that response, so the rest of the view does not run.

        Returns ``False`` when the form was not submitted, or when a button
        with :meth:`.triggers() <wtforms.fields.core.UnboundField.triggers>`
        submitted it without JavaScript. With ``submitter=form.save``, only
        that button saves.
        """
        if result := self.partial():
            abort(Response(result.body, headers=result.headers))

        if not self.is_submitted():
            return False

        if submitter is not None and self.submitter is not submitter:
            return False

        if self.mutated:
            return False

        return self.validate(extra_validators)


def jinja_renderer(template: str, macro: str | None = None) -> Callable:
    """Build a field wrapper callable that renders a Jinja template or macro.

    ``jinja_renderer("_field.html")`` renders the template with ``field`` and
    ``render_kw`` in its context. ``jinja_renderer("_macros.html", "render_field")``
    calls the macro with ``(field, render_kw)``::

        class ProfileForm(HtmxFlaskForm):
            class Meta:
                field_wrapper = staticmethod(jinja_renderer("_field.html"))
    """
    if macro is None:

        def render_template_fn(field, render_kw):
            return render_template(template, field=field, render_kw=render_kw)

        return render_template_fn

    def render_macro_fn(field, render_kw):
        module = current_app.jinja_env.get_template(template).module
        return Markup(getattr(module, macro)(field, render_kw))

    return render_macro_fn


__all__ = [
    "HtmxFlaskForm",
    "jinja_renderer",
]

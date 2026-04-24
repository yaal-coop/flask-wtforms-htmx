flask-wtforms-htmx
==================

Flask adapter for :external+wtforms-htmx:doc:`wtforms-htmx <index>`.
:class:`~flask_wtforms_htmx.HtmxFlaskForm` replaces
:class:`~flask_wtf.FlaskForm`: the usual ``validate_on_submit()`` view
answers htmx requests, and a mutation click without JavaScript does not
save the form. CSRF protection and file uploads work as with Flask-WTF.

.. toctree::
    :caption: Quickstart
    :maxdepth: 2

    tutorial

.. toctree::
    :caption: Reference
    :maxdepth: 2

    reference/api

.. toctree::
    :caption: Changelog
    :maxdepth: 1
    :hidden:

    changes

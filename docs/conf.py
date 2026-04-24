from __future__ import annotations

from importlib.metadata import version as _version

from pallets_sphinx_themes import ProjectLink

project = "flask-wtforms-htmx"
author = "Éloi Rivard"
release = _version("flask-wtforms-htmx")
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_issues",
    "pallets_sphinx_themes",
]

# Intersphinx is used to cross-link into the wtforms-htmx core docs.
# Cross-refs resolve once both projects publish to RTD; during local
# development, unresolved refs emit warnings but don't fail the build.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "flask-wtf": ("https://flask-wtf.readthedocs.io/en/latest/", None),
    "wtforms": ("https://wtforms.readthedocs.io/en/stable/", None),
    "wtforms-htmx": ("https://wtforms-htmx.readthedocs.io/en/latest/", None),
}

# Same shortcuts as wtforms-htmx: htmx has no objects.inv, so we
# fall back to its stable URL scheme via extlinks.
extlinks = {
    "htmx-attr": (
        "https://htmx.org/attributes/%s/",
        "%s",
    ),
    "htmx-header": (
        "https://htmx.org/reference/?h=%s#headers",
        "%s",
    ),
    "mdn-tag": (
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Element/%s",
        "<%s>",
    ),
    "mdn-global-attr": (
        "https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/%s",
        "%s",
    ),
    "mdn-role": (
        "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/%s_role",
        'role="%s"',
    ),
}

issues_github_path = "yaal-coop/flask-wtforms-htmx"

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "flask"
html_static_path: list[str] = []

html_context = {
    "project_links": [
        ProjectLink("PyPI Releases", "https://pypi.org/project/flask-wtforms-htmx/"),
        ProjectLink("Source Code", "https://github.com/yaal-coop/flask-wtforms-htmx/"),
        ProjectLink(
            "Issue Tracker",
            "https://github.com/yaal-coop/flask-wtforms-htmx/issues/",
        ),
        ProjectLink("wtforms-htmx (core)", "https://wtforms-htmx.readthedocs.io/"),
    ],
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["home.html", "localtoc.html", "relations.html", "searchbox.html"],
}
html_show_sourcelink = False

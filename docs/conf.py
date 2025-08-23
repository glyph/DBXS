# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "DBXS"
copyright = "2023, Glyph"
author = "Glyph"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.intersphinx",
    # "pydoctor.sphinx_ext.build_apidocs",
    "sphinx.ext.autosectionlabel",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = []

linkcheck_ignore = [
    # r"https://docs.sqlalchemy.org/.*"
]

# extension options

intersphinx_mapping = {
    "py3": ("https://docs.python.org/3", None),
    "zopeinterface": ("https://zopeinterface.readthedocs.io/en/latest", None),
    "twisted": ("https://docs.twisted.org/en/twisted-22.1.0/api", None),
}

import os
import sys

# 2 levels up from docs/: first_login_password_totp -> addons_config_defaults.
# Every automodule directive below refers to the package as
# `first_login_password_totp.models.xxx`, matching how the rest of this addon's own code
# imports it, so `first_login_password_totp` itself has to resolve as a top-level import here.
sys.path.insert(0, os.path.abspath('../..'))

project = 'first_login_password_totp'
copyright = '2026, Méthode - Progiciel sur Mesure'
author = 'Méthode - Progiciel sur Mesure'

extensions = ['sphinx.ext.autodoc']

# Every module documented here imports from `odoo`, which only exists inside
# a running Odoo installation, not in a plain docs-build environment -- so
# there is nothing to really import. autodoc still needs something
# importable to read docstrings and signatures off, hence the mock: it lets
# `from odoo import fields, models` (and everything similarly rooted at
# `odoo`) succeed with stand-in objects instead of failing the whole build.
autodoc_mock_imports = ['odoo']

html_theme = 'alabaster'

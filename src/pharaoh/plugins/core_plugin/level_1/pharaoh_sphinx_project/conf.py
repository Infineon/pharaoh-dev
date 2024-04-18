"""
Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from pharaoh.api import PharaohProject

THISDIR = Path(__file__).parent
proj = PharaohProject(project_root=THISDIR.parent)
extensions: list[str] = []

# Dynamic updates of local Sphinx configuration with defaults from Pharaoh project.
locals().update(proj.get_default_sphinx_configuration(THISDIR))

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# Your own extensions if you like
extensions.extend([])

# A list of template lookup directories relative to this file's parent directory
pharaoh_jinja_templates = ["user_templates"]

# The default user context that may be used in all templates by accessing via {{ ctx.user.XYZ }}
# E.g. pharaoh_jinja_context = dict(a=1, b=dict(c=2))  -->  {{ ctx.user.a }} or {{ ctx.user.b.c }}
pharaoh_jinja_context: dict[str, Any] = {}

# Add your custom Jinja filters here. Maps filter names to filter functions.
# See https://jinja.palletsprojects.com/en/3.1.x/templates/#filters
pharaoh_jinja_filters: dict[str, Callable] = {}

# Add your custom Jinja globals here. Maps global names to global functions.
pharaoh_jinja_globals: dict[str, Callable] = {}

# Add your custom Jinja tests here. Maps test names to test functions.
# See https://jinja.palletsprojects.com/en/3.1.x/templates/#tests
pharaoh_jinja_tests: dict[str, Callable] = {}

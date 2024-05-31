from __future__ import annotations

from typing import TYPE_CHECKING

import pharaoh
from pharaoh.templating.second_level.template_env import PharaohTemplateEnv

if TYPE_CHECKING:
    from pharaoh.sphinx_app import PharaohSphinx


def setup(app: PharaohSphinx):
    app.add_config_value("pharaoh_jinja_templates", None, "env")
    app.add_config_value("pharaoh_jinja_context", None, "env")
    app.add_config_value("pharaoh_jinja_filters", None, "env")
    app.add_config_value("pharaoh_jinja_tests", None, "env")
    app.add_config_value("pharaoh_jinja_globals", None, "env")

    app.pharaoh_te = PharaohTemplateEnv()
    app.connect("config-inited", app.pharaoh_te.sphinx_config_inited_hook)
    app.connect("builder-inited", app.pharaoh_te.sphinx_builder_inited_hook)
    app.connect("source-read", app.pharaoh_te.sphinx_source_read_hook)
    app.connect("include-read", app.pharaoh_te.sphinx_include_read_hook)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": pharaoh.__version__,
    }

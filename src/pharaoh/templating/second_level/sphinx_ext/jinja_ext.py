from pharaoh.sphinx_app import PharaohSphinx
from pharaoh.templating.second_level.template_env import PharaohTemplateEnv


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

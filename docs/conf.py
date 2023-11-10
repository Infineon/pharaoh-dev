import datetime

import sphinx

from pharaoh.assetlib.resource import collect_resources
from pharaoh.cli import cli
from pharaoh.templating.second_level import env_filters, env_globals, env_tests

assert sphinx.version_info[0] == 7

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.jquery",
    "sphinx_jinja",
    "sphinx_design",
    "sphinx_copybutton",
]

# mocking imports so docs can be built with a lightweight python environment.
# unable to mock: numpy, six
autodoc_mock_imports = [
    "bokeh",
    "matplotlib",
    "holoviews",
    "plotly",
    "pandas",
    "selenium",
    "kaleido",
    # The next packages have circular imports that are hit when sphinx.autodoc extension imports those with
    # typing.TYPE_HINTING set to True. So just ignore them.
    "omegaconf",
    "setuptools",
]

source_suffix = ".rst"
master_doc = "index"
project = "Pharaoh"
year = str(datetime.datetime.now(tz=datetime.timezone.utc).year)

version = release = "Pharaoh v0.1.1"

add_function_parentheses = True
add_module_names = False
toc_object_entries_show_parents = "hide"

pygments_style = "default"
templates_path = ["."]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_logo = "_static/icon.png"
# html_favicon = "_static/favicon.ico"
html_style = "sphinx_rtd_theme_overrides.css"
html_theme_options = {
    "logo_only": True,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "#ededed",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 7,
    "includehidden": True,
}

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_short_title = f"{project}-{version}"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
intersphinx_timeout = 5

rst_epilog = """
.. |Sphinx| replace:: `Sphinx <https://www.sphinx-doc.org/en/master/usage/quickstart.html>`__
.. |Jinja| replace:: `Jinja <https://jinja.palletsprojects.com/en/3.1.x/intro/>`__
.. |asset| replace:: :ref:`asset <reference/assets:Assets>`
.. |assets| replace:: :ref:`assets <reference/assets:Assets>`
"""

linkcheck_workers = 25

# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
extlinks = {}

# https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = None  # 1,2,3

# https://pypi.org/project/sphinx-jinja/
jinja_contexts = {}
jinja_contexts["default"] = {
    # Filter out resources provided by plugins
    "resources": {k: v for k, v in collect_resources().items() if v.__module__.startswith("pharaoh.")},
    "env_filters": env_filters,
    "env_globals": env_globals,
    "env_tests": env_tests,
    "cli_commands": list(cli.commands.keys()),
}
assert len(jinja_contexts["default"]["cli_commands"]) > 0

jinja_env_kwargs = {
    "trim_blocks": True,
    "lstrip_blocks": True,
    "keep_trailing_newline": True,
}
jinja_filters = {"set": set}
jinja_tests = {}
jinja_globals = {}

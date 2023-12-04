import datetime
import os

import sphinx

from pharaoh.cli import cli
from pharaoh.plugins.core_plugin.plugin import DEFAULT_ASSET_TEMPLATE_MAPPING
from pharaoh.plugins.plugin_manager import PM
from pharaoh.templating.second_level import env_filters, env_globals, env_tests
from pharaoh.version import __version__

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

release, version = __version__, "Pharaoh v" + ".".join(__version__.split(".")[:3])

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

# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
extlinks = {
    "issue": ("https://github.com/Infineon/pharaoh-dev/issues/%s", "#%s"),
    "pull": ("https://github.com/Infineon/pharaoh-dev/pull/%s", "PR #%s"),
    "discussion": ("https://github.com/Infineon/pharaoh-dev/discussions/%s", "#%s"),
    "user": ("https://github.com/%s", "@%s"),
    "gh_repo": ("https://github.com/%s", "%s"),
    "gh": ("https://github.com/%s", "%s"),
    "pypi": ("https://pypi.org/project/%s", "%s"),
}
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

if "SPHINX_NO_LINKCHECK" in os.environ:
    linkcheck_ignore = [".*"]
else:
    linkcheck_workers = 25
    linkcheck_timeout = 2

# https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = None  # 1,2,3

# https://pypi.org/project/sphinx-jinja/
jinja_contexts = {}
jinja_contexts["default"] = {
    # Filter out resources provided by plugins
    "resources": {k: v for k, v in PM.pharaoh_collect_resource_types().items() if v.__module__.startswith("pharaoh.")},
    "env_filters": env_filters,
    "env_globals": env_globals,
    "env_tests": env_tests,
    "cli_commands": list(cli.commands.keys()),
    "default_asset_template_mapping": DEFAULT_ASSET_TEMPLATE_MAPPING,
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

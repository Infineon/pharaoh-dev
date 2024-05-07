Release History
===============

v0.7.0
------

-   Performance improvements for Sphinx build, by removing unnecessary deepcopy operations

v0.6.2
------

-   Lazy load patch modules (``pharaoh/assetlib/patches/_*.py``) to improve import speed


v0.6.1
------

-   Fixed :issue:`7`: Tests fail for Jinja 3.1.3

v0.6.0
------

-   Added support for Python 3.12
-   Added new :ref:`extension points <plugins/plugin:Hookspec Markers>` ``pharaoh_find_asset_render_template`` and
    ``pharaoh_get_asset_render_template_mappings``.
-   Changed supported suffix for Jinja templates from ``.jinja`` to ``.jinja2``, since IDE integration is much better
    with later.
-   Updated documentation

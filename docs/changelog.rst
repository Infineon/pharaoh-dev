Release History
===============

v0.6.0
------

-   Added support for Python 3.12
-   Added new :ref:`extension points <plugins/plugin:Hookspec Markers>` ``pharaoh_find_asset_render_template`` and
    ``pharaoh_get_asset_render_template_mappings``.
-   Change supported suffix for Jinja templates from ``.jinja`` to ``.jinja2``, since IDE integration is much better
    with later.

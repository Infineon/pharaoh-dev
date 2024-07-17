Release History
===============

v0.7.3
------

-   Fixed :issue:`20`: Matplotlib savefig wrong signature after patching by Pharaoh

v0.7.2
------

-   Fixed an ``InterpolationKeyError`` when dynamically resolving variables inside the components
    section of ``pharaoh.yaml``.

v0.7.1
------

-   Migrated to hatch-based workflow
-   Fix some deprecations

v0.7.0
------

-   Major performance improvements for Sphinx build, by removing unnecessary deepcopy operations
-   Added support for ``.yml`` suffix for YAML files
-   Added reference docs for class :class:`pharaoh.assetlib.finder.Asset`
-   Removed Python upper version constraint
-   Unpinned pyyaml dependency, but ignoring version ``5.3.0``
-   Removed ``numpy<2.0`` version constraint


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

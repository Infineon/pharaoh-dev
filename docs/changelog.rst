Release History
===============

0.9.3
-----

-   Fixed an issue where the Pharaoh asset directive was adding assets in the wrong order,
    instead of the order they were generated in.


0.9.2
-----

-   Pinned plotly to <6.1. See [Plotly #5187](https://github.com/plotly/plotly.py/issues/5187).

0.9.1
-----

-   Pinned click to <8.2 for now, since it drops support for Python 3.9

0.9.0
-----

-   Adds possibility to filter components on an existing pharaoh project.
    This can be used to create several variants of the same report which contain a subset of the full reports components.
    To increase ease of use, the ``pharaoh.api.project.archive_project`` method got new options to disable `compression`
    and add an additional `suffix` to the archives name to create meaningful report names for their specific purpose.
    Ideally you build your reports via a small script and not the CLI to leverage this flexibility.

    .. code-block:: python

        from pharaoh.api import PharaohProject

        if __name__ == "__main__":
            proj = PharaohProject(project_root="./pharaoh-report")
            proj.generate_assets()
            proj.build_report()  # this report contains all components
            proj.archive_report(compression=False, suffix="-full")

            proj.filter_components(exclude="3DPieChart.*|MultiStackedBarChart.*")
            proj.build_report()  # this report contains just a subset of the full report
            proj.archive_report(compression=False, suffix="-light")

0.8.3
-----

-   Fix encoding issue when dumping Juptyer notebook outputs


0.8.2
-----

-   Fixed an issue when using Jupyter notebooks as asset scripts, where the
    calls to ``pharaoh.assetlib.api.get_current_component`` resulted in an error.
-   Tracebacks occurring during asset generation in Jupyter notebooks are now
    printed to console with filtered ANSI control characters to improve readability.
-   Fixed :issue:`32`: Image assets with whitespace in path are not rendered correctly
-   Pinned ``kaleido`` dependency to 0.2.0/0.2.1 for Linux environments,
    since there are no wheels available for newer versions.

0.8.1
-----

-   Pinned kaleido dependency to <0.4 for Linux environments.
    See [Kaleido-223](https://github.com/plotly/Kaleido/issues/223).

0.8.0
-----

-   Removed logging all environment variables in case of an error
-   Added functionality to catch errors during asset generation and render them
    in the final report. More info here: :ref:`Catching Errors <reference/assets:Catching Errors>`
-   The built-in default Pharaoh project template now also includes a short error admonition on the index page,
    that shows which components have exported :ref:`error assets <reference/assets:Catching Errors>`
    during asset generation.
-   If errors during asset generation are :ref:`caught <reference/assets:Catching Errors>` and rendered
    in the final report, the Sphinx build will now also output a warning
    (and therefore fail), to make sure the user notices the errors.

0.7.4
-----

-   Constrain sphinx-rtd-theme to <3.0 to keep support for ``display_version`` theme option.


0.7.3
-----

-   Fixed :issue:`20`: Matplotlib savefig wrong signature after patching by Pharaoh

0.7.2
-----

-   Fixed an ``InterpolationKeyError`` when dynamically resolving variables inside the components
    section of ``pharaoh.yaml``.

0.7.1
-----

-   Migrated to hatch-based workflow
-   Fix some deprecations

0.7.0
-----

-   Major performance improvements for Sphinx build, by removing unnecessary deepcopy operations
-   Added support for ``.yml`` suffix for YAML files
-   Added reference docs for class :class:`pharaoh.assetlib.finder.Asset`
-   Removed Python upper version constraint
-   Unpinned pyyaml dependency, but ignoring version ``5.3.0``
-   Removed ``numpy<2.0`` version constraint


0.6.2
-----

-   Lazy load patch modules (``pharaoh/assetlib/patches/_*.py``) to improve import speed


0.6.1
-----

-   Fixed :issue:`7`: Tests fail for Jinja 3.1.3

0.6.0
-----

-   Added support for Python 3.12
-   Added new :ref:`extension points <plugins/plugin:Hookspec Markers>` ``pharaoh_find_asset_render_template`` and
    ``pharaoh_get_asset_render_template_mappings``.
-   Changed supported suffix for Jinja templates from ``.jinja`` to ``.jinja2``, since IDE integration is much better
    with later.
-   Updated documentation

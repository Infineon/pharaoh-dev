Plugin Architecture
===================

Pharaoh may be extended using `pluggy <https://pluggy.readthedocs.io/en/latest/>`_.
Just import the ``impl`` decorator from ``pharaoh.plugins.api`` and implement one of the specs documented
:ref:`below <plugins/plugin:Hookspec Markers>`.

If you like to extend other parts of the library please open up a
`discussion on GitHub <https://github.com/Infineon/pharaoh-dev/discussions>`_ or raise a PR directly.

Here an example on how to extend the Sphinx configuration programmatically::

    from pharaoh.plugins.api import impl

    @impl
    def pharaoh_configure_sphinx(project: PharaohProject, config: dict, confdir: Path):
        config["extensions"].append("sphinxcontrib.confluencebuilder")
        config["html_style"] = "sphinx_rtd_theme_overrides.css"


Custom project class
--------------------

Implement ``pharaoh_get_project_class`` to select a ``PharaohProject`` subclass
for CLI project creation, project discovery, asset generation, and Sphinx builds::

    from pharaoh.plugins.api import impl

    @impl
    def pharaoh_get_project_class():
        from my_plugin.project import CustomProject
        return CustomProject

Define ``CustomProject`` in your plugin package as a subclass of
``pharaoh.project.PharaohProject``. Keep the import inside the hook: plugins are
discovered while Pharaoh's modules are being imported. Use the normal project
constructor arguments so that the CLI can instantiate the subclass.

The first non-``None`` hook result is used, following pluggy's hook ordering;
``@impl(tryfirst=True)`` can give an implementation priority. Without a result,
the standard class is used. Returning an unrelated class or an instance raises
``TypeError``. Direct calls to ``PharaohProject(...)`` still construct that class.

Use ``get_project(path)`` to discover an existing project with the selected class.
The no-argument ``get_project()`` still returns the most recently created instance.
For worker processes and notebooks, install the plugin through the existing plugin
entry point or ``PHARAOH_PLUGINS`` discovery mechanism; in-memory registrations
made only in the parent process are not inherited by a fresh Python interpreter.


Hookspec Markers
----------------

.. automodule:: pharaoh.plugins.spec
    :members:

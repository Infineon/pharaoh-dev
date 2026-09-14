Settings
========

The Pharaoh settings file ``pharaoh.yaml`` is used for three main purposes:

-   Configuration of Pharaoh functionality like asset generation, report build, archiving, RDDL upload, notifications...
-   Hold info about all added components
-   User-defined settings (accessible from templates)

The settings file is loaded using the `OmegaConf library <https://omegaconf.readthedocs.io/>`_.

    *OmegaConf is a YAML based hierarchical configuration system, with support for merging configurations*
    *from multiple sources (files, CLI argument, environment variables) providing a consistent API regardless*
    *of how the configuration was created. OmegaConf also offers runtime type safety via Structured Configs.*

    The library offers lots of features like
    `Variable interpolation <https://omegaconf.readthedocs.io/en/2.3_branch/usage.html#variable-interpolation>`_ and
    `Resolvers <https://omegaconf.readthedocs.io/en/2.3_branch/custom_resolvers.html#built-in-resolvers>`_.
    So if you want to get the best out of your configuration file, have a look in the OmegaConf documentation on the
    mentioned topics above.


Default Settings
----------------

A Pharaoh project is generated with following default settings, if not specified otherwise:

.. literalinclude:: ../../src/pharaoh/plugins/core_plugin/default_settings.yaml
    :language: yaml


Custom Settings
---------------

Since default settings are very likely to not fit everyone's needs, they can be modified by the user in several ways:

.. important:: Make sure all keys in your settings are lowercase, otherwise putting/getting settings might
    not work as expected since settings are all treated lowercase internally!

-   Pass a custom settings file on project creation via the keyword argument ``custom_settings``.
    The file is merged with the default settings, so it's enough to overwrite only the divergent settings::

        from pharaoh.api import PharaohProject

        proj = PharaohProject(project_root="some-path", custom_settings="mysettings.yaml")

    .. note:: If ``custom_settings`` is a relative path, then the current working directory is used as anchor

-   Put settings via the settings API
    :func:`put_setting(key: str, value: Any) <pharaoh.project.PharaohProject.put_setting>`::

        from pharaoh.api import PharaohProject

        proj = PharaohProject(project_root="some-path")
        proj.put_setting("report.title", "My own title")
        proj.put_setting("toolkits.bokeh.export_png", dict(width=720, height=480))
        proj.save_settings()  # Optional

    .. important:: Defining settings like this only changes the settings for the project instance in memory but does
        not persist them to ``pharaoh.yaml``.

        To do so call :func:`save_settings() <pharaoh.project.PharaohProject.save_settings>` manually if
        you don't plan to modify components/resources right after (those functions do an auto-safe).

-   Put settings via environment variables

    Same example as with settings API, but with environment variables::

        import os
        from pharaoh.api import PharaohProject

        # Env variables have to be prefixed with "pharaoh." and are always treated lowercase
        os.environ["pharaoh.report.title"] = "My own title"
        os.environ["pharaoh.toolkits.bokeh.export_png"] = "{'width': 720, 'height': 480}"

        proj = PharaohProject(project_root="some-path")
        proj.save_settings(include_env=True)

    .. note:: Double-underscore ``__`` also acts as a valid separator for keys, since some shell environments don't
        allow dots inside variable names. E.g. ``PHARAOH__a.B__c___d`` will resolve to ``pharaoh.a.b.c___d``.

    .. important:: Environment variables are only persisted to ``pharaoh.yaml`` when saving like this:
        :func:`save_settings(include_env=True) <pharaoh.project.PharaohProject.save_settings>`

    .. important:: If Pharaoh environment variables are changed while the project is already instantiated,
        you can reload settings using
        :func:`load_settings(namespace="env") <pharaoh.project.PharaohProject.load_settings>`::

            import os
            from pharaoh.api import PharaohProject

            proj = PharaohProject(project_root="some-path")
            os.environ["pharaoh.report.title"] = "My Title"
            proj.load_settings(namespace="env")
            proj.save_settings(include_env=True)

Accessing Settings
------------------

Setting values can be accessed in various places throughout the Pharaoh project using
:func:`PharaohProject.get_setting() <pharaoh.project.PharaohProject.get_setting>`:

-   in Python scripts, e.g. |asset|- or local context-scripts::

        from pharaoh.api import get_project
        pharaoh_project = get_project(__file__)  # Get a project instance location of this file in project directory
        title = project.get_setting("report.title")

-   in templates::

        {{ heading(get_setting("report.title"), 1) }}
        {% set static_export = get_setting("asset_gen.force_static", False) -%}


Custom Resolvers
----------------

`OmegaConf <https://omegaconf.readthedocs.io/>`_ offers already some
`builtin resolvers <https://omegaconf.readthedocs.io/en/2.3_branch/custom_resolvers.html#built-in-resolvers>`_
like ``oc.env``: :code:`author: "${oc.env:USERNAME,unknown}"`
but Pharaoh adds additional ones for your convenience:

- ``utcnow.strf``: Formats UTC time.

    Usage: :code:`archive_name: "pharaoh_report_${utcnow.strf:%Y%m%d_%H%M%S}.zip"`

- ``now.strf``: Same as above, but with timestamp of local timezone.

- ``pharaoh.project_dir``: Returns the Pharaoh project directory with ``/`` as path separator.

    Usage: :code:`key: "${pharaoh.project_dir:}/somepath"` (note the trailing ``:``, without, it would be a reference).

If you need additional resolvers just register them
`like this <https://omegaconf.readthedocs.io/en/2.3_branch/custom_resolvers.html#custom-resolvers>`_.

If you think others might benefit too, please add them to ``pharaoh.util.oc_resolvers`` and raise a PR.

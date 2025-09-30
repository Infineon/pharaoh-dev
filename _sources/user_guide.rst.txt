==========
User Guide
==========

Preface
=======

This user guide targets **end-users**.

If you're about to **create** templates for end users,
please refer to our :ref:`template_designer_guide:Template Designer Guide`.

End-users usually will:

-   Generate Pharaoh projects based on the templates the template designers provided
-   Update project settings
-   Manage project components (update, add, remove)
-   Modify/add asset scripts
-   Overwrite certain pre-defined blocks inside provided templates

.. important:: The following guide only shows the API provided by Pharaoh. Keep in mind that the template designers
    of your project might provide an additional or different API to create Pharaoh projects.


Project Generation
==================

The first thing to do is generating a Pharaoh project.

.. note:: This step may be skipped if you already created a project and manage it via GIT for example.


.. tab-set::

    .. tab-item:: API

        Create a Python script with following example content to create a new Pharaoh project:

        .. code-block::

            from pharaoh.api import PharaohProject

            # Create a project with a default template optimized for HTML output inside current working directory
            proj = PharaohProject(project_root="./pharaoh-report")

            # For overwriting an existing project
            proj = PharaohProject(project_root="path-to-existing-project", overwrite=True)

            # Passing a custom template to extend the default project template "pharaoh.default_project"
            proj = PharaohProject(
                ".",
                templates=("pharaoh.default_project", r"C:\...\my-extension-template"),
                template_context=dict(some_variable_in_extension_template="abc")
            )

            # Passing a custom settings YAML file
            proj = PharaohProject(".", custom_settings=r"C:\...\my_custom_settings.yaml")


    .. tab-item:: CLI

        In a terminal with activated virtual environment that has pharaoh installed, type following commands:

        .. code-block:: none

            # Create a project with a default template optimized for HTML output inside current working directory
            pharaoh new

            # For overwriting an existing project
            pharaoh -p "path/to/existing/project" new --force

            # Passing a custom template to extend the default project template "pharaoh.default_project"
            pharaoh new -t pharaoh.default_project -t "C:\...\my-extension-template"
                -c "{'some_variable_in_extension_template': 'abc'}"

            # Passing a custom settings YAML file
            pharaoh -p . new --settings "C:\...\my_custom_settings.yaml"


Update Settings
===============

.. seealso:: :ref:`Settings Reference <reference/settings:Settings>`

Single settings may be updated during project generation (API & CLI) or afterwards (API or manually).

.. tab-set::

    .. tab-item:: During Generation

        .. tab-set::

            .. tab-item:: API

                This is done via the settings API function
                :func:`put_setting(key: str, value: Any) <pharaoh.project.PharaohProject.put_setting>`
                or via environment variables. Refer to the :ref:`reference/settings:Custom Settings` section
                for examples.

            .. tab-item:: CLI

                Besides passing an entire settings YAML file to the project generation,
                settings can be set using environment variables during project generation.
                Those will be automatically persisted in the settings file.

                .. code-block:: none

                    # CMD syntax:
                    set PHARAOH.LOGGING.LEVEL=INFO
                    set PHARAOH.FOO=bar
                    set PHARAOH.bla="{'blubb': 123}"

                    # PowerShell syntax:
                    Set-Variable -Name PHARAOH.LOGGING.LEVEL -Value INFO
                    Set-Variable -Name PHARAOH.FOO -Value bar
                    Set-Variable -Name PHARAOH.bla -Value "{'blubb': 123}"

                    # Bash syntax:
                    env "PHARAOH.LOGGING.LEVEL=INFO" bash
                    env "PHARAOH.FOO=bar" bash
                    env "PHARAOH.bla={'blubb': 123}" bash

                    pharaoh new


    .. tab-item:: After Generation

        .. tab-set::

            .. tab-item:: API

                This is done via the settings API function
                :func:`put_setting(key: str, value: Any) <pharaoh.project.PharaohProject.put_setting>`
                or via environment variables. Refer to the :ref:`reference/settings:Custom Settings` section
                for examples.

                .. code-block::

                    from pharaoh.api import PharaohProject

                    proj = PharaohProject(project_root="some-path")
                    proj.put_setting("report.title", "My own title")
                    proj.put_setting("toolkits.bokeh.export_png", dict(width=720, height=480))

            .. tab-item:: CLI

                Updating settings via CLI may be done via the :ref:`env command <reference/cli:env>`:

                .. code-block:: none

                    cd "path/to/project"
                    pharaoh env report.title "My own title"

                    # or
                    pharaoh -p "path/to/project" env toolkits.bokeh.export_png "{'width':720, 'height':480}"

            .. tab-item:: Manually

                Just open the file ``pharaoh.yaml`` in your project root and modify its content according to
                `YAML Coding Guidelines
                <https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/CodingGuidelines/CglYaml.html>`_
                and the `OmegaConf library specification <https://omegaconf.readthedocs.io/>`_.


Manage Components
=================

The main content of a Pharaoh report is determined by components.

.. seealso:: :ref:`What's a Component? <reference/components:what's a component?>` in the
    :ref:`Components Reference <reference/components:Components>`

Components may be added or updated using following API/CLI:

.. tab-set::

    .. tab-item:: API

        This is done via the component API functions for managing components
        :ref:`documented here <reference/components:Managing Components>`.

        Please refer to the component API functions for managing components
        :ref:`here <reference/components:Managing Components>`. Relevant sections are:

        -   :ref:`reference/components:adding components`
        -   :ref:`reference/components:updating components`
        -   :ref:`reference/components:removing components`

    .. tab-item:: CLI

        Please refer to the CLI reference :ref:`here <reference/cli:CLI>`. Relevant commands are:

        -   :ref:`reference/cli:add`
        -   :ref:`reference/cli:update-resource`
        -   :ref:`reference/cli:add-template`
        -   :ref:`reference/cli:remove`

        Here some examples:

        .. code-block:: none

            pharaoh add -n dummy1 -t pharaoh_testing.simple -c "{'test_name':'dummy'}"
            pharaoh add -n dummy1 -t pharaoh_testing.simple -r "FileResource(alias='foo', pattern='.*')"

            pharaoh update-resource -n dummy1 -a foo -r "FileResource(alias='baz', pattern='.*')"

            pharaoh add-template -n dummy1 -t pharaoh_testing.simple -c "{'test_name':'dummy'}"

            pharaoh remove -f dummy.*


Manage Asset Scripts
====================

Once components are added, users may add or modify existing asset scripts.

.. seealso:: :ref:`What's an Asset? <reference/assets:what's an asset?>` in the
    :ref:`Assets Reference <reference/assets:Assets>` and
    :ref:`Example Asset Scripts <examples/asset_scripts:asset scripts>`.




Modify Templates
================

If assets scripts are added or modified the templates might need to be updated to include potentially
modified or added assets.

.. seealso:: :ref:`reference/directive:Pharaoh Directive` on how to include generated assets into your templates
    and the :ref:`reference/templating:Build-time Templating` section.

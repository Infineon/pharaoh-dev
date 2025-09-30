
Building
========

Configuration
-------------

Following steps have to be done for configuring a Sphinx build:

#.  Choose a Sphinx build target via the ``report.target`` setting.
    Currently supported are:

    -   **html** and all other `Sphinx default builders
        <https://www.sphinx-doc.org/en/master/usage/builders/index.html>`_ like latex.
    -   `confluence, singleconfluence <https://sphinxcontrib-confluencebuilder.readthedocs.io/en/stable/builders/>`_.

    .. note:: For other builders than ``html`` and ``*confluence``, you might need to install additional dependencies.

#.  Configure the selected builder

    -   Via :ref:`settings <reference/settings:Settings>` sections like ``report.html`` and ``report.confluence``
    -   Via the `Sphinx configuration <https://www.sphinx-doc.org/en/master/usage/configuration.html>`_
        ``report_project/conf.py``.

        This file loads a default Sphinx configuration variables (also partially from :ref:`settings
        <reference/settings:Settings>`) and assigns them to the local namespace.

        To modify just overwrite or alter them::

            # The list "html_css_files" is already defined from the default config,
            # but this is not the case for all variables.
            # To be sure inspect the local namespace via the debugger or print it
            # like this ``print(", ".join(locals().keys()))``
            html_css_files.append("css/mystyle.css")

    .. note:: The HTML builder already contains a reasonable default config, so no change needed in most cases.


Build API
---------

A Pharaoh report may be built using the method :func:`PharaohProject.build_report()
<pharaoh.project.PharaohProject.build_report>`.

.. important::
    If your templates are accessing assets, make sure you call :func:`PharaohProject.generate_assets()
    <pharaoh.project.PharaohProject.generate_assets>` every time your asset scripts or resources changed.

You can call the API within a Python script, as for example in the included ``report-project/debug.py`` script.

    .. code-block::

        from pharaoh.api import PharaohProject

        if __name__ == "__main__":  # This guard is needed because Pharaoh is using multiprocessing
            proj = PharaohProject(project_root="..")
            proj.generate_assets()
            proj.build_report()

Or you just double-click the CLI scripts ``report-project/pharaoh-generate-assets.cmd`` and
``report-project/pharaoh-build.cmd``.

Or with the Pharaoh venv activated, inside the project directory use the CLI directly: ``pharaoh build``

Log output should be displayed in the console, but are also written to ``log.txt`` and ``log_warnings.txt``
(only warnings or errors).


Archiving
---------

After building a report, it may be archived using :func:`PharaohProject.archive_report()
<pharaoh.project.PharaohProject.archive_report>`.

.. automethod:: pharaoh.project.PharaohProject.archive_report
    :noindex:

Alternatively just double-click the CLI script ``report-project/pharaoh-archive.cmd``.

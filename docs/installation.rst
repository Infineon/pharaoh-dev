============
Installation
============

Requirements
============

Any of the following Python versions are compatible.
If you don't have any installed, please download and execute a version by clicking the links below.

    -   **Python 3.11 (recommended)**
        [`Download Python 3.11.4 <https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe>`_]
    -   **Python 3.10**
        [`Download Python 3.10.11 <https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe>`_]
    -   **Python 3.9** (min. 3.9.2)
        [`Download Python 3.9.13 <https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe>`_]


Installation via Pip
====================

Create a virtual environment
----------------------------

A virtual environment has its own Python binary (which matches the version of the binary that was
used to create this environment) and can have its own independent set of installed Python packages
in its site directories.

The easiest way to create a virtual environment, is to let the IDE PyCharm (recommended) create one for you.
`Configure a virtual environment <https://www.jetbrains.com/help/pycharm/creating-virtual-
environment.html#python_create_virtual_env>`_ shows how to do that.

The other option is to create it via command line like follows and then configure PyCharm to use this as
project interpreter.

.. seealso:: `venv — Creation of virtual environments <https://docs.python.org/3/library/venv.html>`_

#.  Open a shell (e.g. an Inicio shell or PowerShell)
#.  Change into your workspace: :code:`cd C:\\temp`
#.  Create a virtual environment: :code:`C:\\Python311\\python.exe -m venv pharaoh_venv`
#.  Activate it:

    -   Powershell :code:`.\\pharaoh_venv\\Scripts\\Activate.ps1`
    -   Bash: :code:`source ./pharaoh_venv/Scripts/activate`
    -   Cmd/Bat: :code:`.\\pharaoh_venv\\Scripts\\activate.bat`
#.  You should be getting a prefix to your command line like this: :code:`(pharaoh_venv) PS C:\\temp>`
#.  Ensure you use binary packages where possible by installing `wheel` first :code:`pip install wheel`

You can find more information about `virtual environments here
<https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/>`_.


Install
-------

After the virtual environment has been created, activate it and install ifx-pharaoh via pip::

    pip install pharaoh-report[<extras>]

.. note:: Refer to section :ref:`Extras <section_extras>` to install additional dependencies.

.. note:: For updating Pharaoh to the latest version, append the ``-U`` flag to the pip command

Then you would be able to run::

    pip install pharaoh-report[<extras>]


.. _section_extras:

Extras
------

The ``extras`` field is a comma-separated list of additional dependency groups.

Following extra dependencies may be installed, depending on your use case:

-   ``bokeh``: Installs the Bokeh plotting framework and exporters
-   ``holoview``: Installs the Holoviews plotting framework
-   ``plotly``: Installs the Plotly plotting framework and exporters
-   ``matplotlib``: Installs the Matplotlib plotting framework
-   ``jupyter``: Installs Jupyter for asset script implementation
-   ``pandas``: Installs Pandas Data Analysis Library
-   ``pdf``: Installs an SVG to PDF converter for the LaTeX builder
-   ``all-plotting``: Installs all supported plotting frameworks

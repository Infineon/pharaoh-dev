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


Hookspec Markers
----------------

.. automodule:: pharaoh.plugins.spec
    :members:

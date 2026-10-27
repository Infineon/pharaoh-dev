============
Introduction
============

Pharaoh is a |Sphinx|-based Python framework for
generating reports in various formats (HTML, Confluence, PDF) by combining the power of configurable
|Jinja| templates and Python scripts for asset (tables, plots, pictures, etc...) generation.

.. image:: _static/overview.png
    :scale: 75%
    :target: _static/showcase_slides.pptx


Click the PowerPoint icon to download the latest presentation slides:

    .. image:: _static/pptx.png
        :scale: 50%
        :target: _static/showcase_slides.pptx


.. _example_report:

.. seealso:: :ref:`examples/demo_reports:Demo Reports` (might not reflect latest development version)


Pharaoh mainly serves two user groups:

**Template Designers**
    They are creating pre-defined configurable templates & data post-processing methods and for your project and
    therefore provide a simplification layer for the end user.

**End-Users**
    They will build reports based on the templates the template designers created.
    They provide the final content (assets like plots, table, etc...) and configuration
    (context to fill template variables) for the templates.


Working Principle
=================

The standard Pharaoh workflow consists of following major steps:

#.  **Project Generation**

    Generates a Pharaoh project with one or multiple components based on predefined templates.
    Its core is a fully-preconfigured |Sphinx| documentation project.

    This generation is called **first-level templating** or **generation-time templating**
    further on in the documentation.

    It may be checked into GIT for incremental modifications or generated each time, depending on your project setup.

    Now the templates and asset scripts in the generated components as well as the project settings
    can be modified by the user.

    .. image:: _static/generation_time_templating.svg

#.  **Asset Generation**

    During asset generation, the asset scripts of each component are executed.

    By using the resources files of its own and/or other components,
    asset scripts are producing dynamic content assets for the later report,
    like plots, images, tables and additional data (e.g. json) used for rendering the templates.

    Those assets are then registered with metadata, so that they can be searched/included by the templates.

    Each asset script may produce any amount of assets.

#.  **Project Build**

    Translates an existing Pharaoh project to a configured target format (e.g. HTML, Confluence, LaTeX),
    while performing an additional templating step via |Jinja|.

    This is called **second-level templating** or **build-time templating** further on in the documentation.

    Templates may inherit and extend existing or user-defined base-templates (for reuse purposes).

    Templates may dynamically include other templates.

    Templates are rendered using a rendering context (variables that can be used in template),
    that contains following data:

    -   Project Settings
    -   Static/manually entered context data
    -   Dynamic context data, that is created by executing a Python script (potentially accessing generated assets)

    .. image:: _static/build_flow.svg

Project Structure
=================

A generated and built Pharaoh project has following directory structure:

.. code-block:: none

    📁 <project-name>
    ├── 📄 pharaoh.yaml
    │       Contains all settings and component definitions.
    ├── 📄 log.txt
    │       Build logs for all logging levels.
    ├── 📄 log_warnings.txt
    │       Build logs for logging levels WARNING and higher.
    ├── 📄 pharaoh_report_<timestamp>.zip
    │       A ZIP archive of the built report.
    ├── 📄 .gitignore
    │       A file for GIT to ignore all transient files.
    ├── 📁 report-build
    │       Contains the build output, e.g. HTML pages or LaTeX input files.
    │       For HTML output the main page is called index.html.
    └── 📁 report-project
        ├── 📁 .resource_cache
        │       Contains temporary/cached resources
        ├── 📁 _static
        │       Contains the CSS overrides and the HTML logo for the report.
        ├── 📁 _templates
        │       Contains HTML templates that override the defaults of the selected Sphinx theme.
        │       In the case layout.html and footer.html. Only change if you really need to.
        ├── 📁 .asset_build
        │       All registered assets from asset generation will be stored here for each component separately.
        ├── 📁 components
        │       This is where components get created when added via the project API.
        ├── 📁 user_templates
        │       Stores user-defined templates for the build-time templating step.
        ├── 📄 conf.py
        │       The Sphinx configuration file (https://www.sphinx-doc.org/en/master/usage/configuration.html)
        │       It loads a default configuration from the Pharaoh project into local variables.
        │       Used to overwrite or add additional configuration.
        ├── 📄 debug.py
        │       For debugging the asset/report generation. Modify for your needs.
        │       Per default it executes asset generation and report build.
        ├── 📄 index.rst
        │       The default template to control how the title page looks like.
        │       It includes all components into the TOC (table of content) tree.
        ├── 📄 index.rst.rendered
        │       *.rendered files are generated during build-time templating step and allow to see the
        │       actual rST content Sphinx is using for generating the report.
        │       This helps for debugging your templates since you see the result after the templating step.
        └── 📄 \*.cmd
                Scripts to execute asset generation, report build or upload to R&D Datalake with a single double-click.

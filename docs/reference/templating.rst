Templating
==========

As you may have noticed, templating is a dominating core functionality of Pharaoh.

The foundation for all templating in Pharaoh is **reStructuredText** and **Jinja**.
You might make yourself familiar once you encounter related questions in the rest of the section.

    **reStructuredText**

        reStructuredText is an easy-to-read, what-you-see-is-what-you-get plaintext markup syntax and parser system.
        It is useful for in-line program documentation (such as Python docstrings), for quickly creating simple web pages,
        and for standalone documents.

        reStructuredText is designed for extensibility for specific application domains.

        The primary goal of reStructuredText is to define and implement a markup syntax for use in Python docstrings
        and other documentation domains, that is readable and simple, yet powerful enough for non-trivial use.

        Refer to the `reStructuredText Reference <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
        for learning the basics.

    **Jinja**

        Jinja is a fast, expressive and extensible templating engine.

        A Jinja template is simply a text file.
        Jinja can generate any text-based format (HTML, XML, CSV, LaTeX, etc.), in Pharaoh's case mostly rST files.
        A Jinja template does not need to have a specific extension: .html, .xml, or any other extension is just fine.

        A template contains **variables** and/or **expressions**, which get replaced with values when a
        template is *rendered*; and **tags**, which control the logic of the template.
        The template syntax is heavily inspired by Python.

        Refer to the `Jinja Template Reference <https://jinja.palletsprojects.com/en/3.1.x/templates/>`_
        for learning the basics.

        See :ref:`Templating Builtins <reference/api:Templating Builtins>` for a complete list of globals, filters and
        tests you can use in your templates.


Like described in the :ref:`introduction <intro:Working Principle>`, Pharaoh's workflow distinguishes
two major stages where template rendering is performed.
Please refer to the corresponding sections by following the links:

    -   :ref:`reference/templating:Generation-time Templating`
    -   :ref:`reference/templating:Build-time Templating`



Generation-time Templating
--------------------------

Alias: **first-level templating**

Generation-time templating is used while generating a new Pharaoh project or adding new components to an
existing project, and is inspired by `copier <https://copier.readthedocs.io/en/stable/>`_,
a |Jinja|-based library for rendering project templates.

Basics
++++++

In Pharaoh, we need first-level templates for two different purposes:

    **Project Templates**

        These are the templates that may be specified when creating a new Pharaoh project.
        The composition of all templates in this case must always generate a Sphinx project that contains at
        least a ``conf.py`` and an index source file, like ``index.rst``.

        If you're interested in maintaining your own project template please contact us for support,
        but for most use cases our default template ``pharaoh.default_project`` should be flexible enough.

        It is also possible to extend or overwrite parts of the default project, so please also get in touch
        if you try to do so.

    **Component Templates**

        Component templates are used to render new components into a Pharaoh project.

        The minimal requirement is basically an ``index.rst`` file that can be included by the project
        (at least what our default Pharaoh template concerns) or a
        :ref:`Template File <reference/templating:Single-file Templates>`

Like described :ref:`here <reference/components:Templates>`, templates can come in different styles.

While for **Project Templates** only *registered templates* and *template directories* are allowed/useful,
**Component Templates** can, in addition to it, be generated using
:ref:`Template Files/Single-file templates <reference/templating:Single-file Templates>`.

Let's have a look on how a component template directory may look like:

    .. code-block:: none

        📁 my_template
        ├── 📄 index.rst.jinja2            # reST file with templated content
        ├── 📄 test_context.py.jinja2      # Python file with templated content
        ├── 📁 asset_scripts               # folder copied as-is
        │   └── 📄 default_plots.py        # file copied as-is
        └── 📁 [[foo]]                     # folder with a templated name
            └── 📄 [[ bar ]]_script.py     # file with a templated name

    -   ``📁 my_template``

        The top-level directory. The name is arbitrary, it will be replaced by the name of the component during coyping.
    -   ``📁 asset_scripts`` and ``📄 default_plots.py`` are copied as-is without modifications.
    -   ``📄 *.jinja``

        The content of all files with suffix ``.jinja2`` are rendered using Jinja.
    -   ``📁 [[foo]]`` and ``📄 [[ bar ]]_script.py``

        File or directory names using ``[[ <context-variable> ]]`` are rendered using Jinja while copying.

After rendering like this ``proj.add_component("dummy", [".../my_template"], render_context={"foo": "a", "bar": "b"}``
a file structure like this is created:

    .. code-block:: none

        📁 dummy
        ├── 📄 index.rst
        ├── 📄 test_context.py
        ├── 📁 asset_scripts
        │   └── 📄 default_plots.py
        └── 📁 a
            └── 📄 b_script.py

You see the ``render_context`` passed to
:func:`PharaohProject.add_component() <pharaoh.project.PharaohProject.add_component>`
or ``template_context`` passed to :func:`PharaohProject() <pharaoh.project.PharaohProject.__init__>` are used to
render file- or folder name as well as file content.

.. important::
    For Generation-time Templating, Jinja is configured to use brackets for blocks ``[% %]`` and statements ``[[ ]]``
    to not interfere with :ref:`reference/templating:Build-time Templating`, where Jinja will render the same
    files (only reST) again before passing it to
    Sphinx using curly-braces for blocks ``{% %}`` and statements ``{{ }}``.

    So imagine an extreme case of a file ``index.rst.jinja2`` with following content::

        {{ h1("[[heading_prefix]]%s"|format(ctx.project.component_name)) }}

    After :ref:`reference/templating:Generation-time Templating`
    (component named ``Test_1`` with render context ``heading_prefix="PREFIX - "``)
    it results in a file ``index.rst`` with content::

        {{ h1("PREFIX - %s"|format(ctx.project.component_name)) }}

    After :ref:`reference/templating:Build-time Templating` it results in content::

        PREFIX - Test_1
        ###############


Single-file Templates
+++++++++++++++++++++

Single-file templates, or also called template files, are smallest and most compact form of a template, but also
limited.

They are mainly designed to deliver template code **and** asset script in a single file and contribute content to
an existing component.

Template files are Python files with suffix ``.pharaoh.py`` those Python code creates |assets| and
those module level docstring represents the reST content.

Here an example::

    """
    {{ heading("My Plots", 2) }}

    .. pharaoh-asset:: label == "my_plot"
    """
    from pharaoh.assetlib.api import metadata_context

    import plotly.express as px


    df = px.data.iris()
    fig = px.scatter(
        df,
        x="sepal_width",
        y="sepal_length",
        color="species",
        symbol="species",
        title=r"A title",
    )

    with metadata_context(label="my_plot"):
        fig.write_html(file="iris_scatter.html")


This file will be internally converted to a template directory::

    my_template.pharaoh.py -> index_my_template.rst
                              asset_scripts/my_template.py


In order to automatically include all ``index_*.rst`` files in your components index file ``index.rst``, you
must add following code:

    .. code-block::

        {% for index_rst in fglob("index_*.rst") %}
        .. include:: {{ index_rst }}

        {% endfor %}


Build-time Templating
---------------------

Build-time templating is the step where Pharaoh hooks into Sphinx's build process and renders each documentation
source file before it gets consumed by Sphinx.

For example the source file ``index.rst`` will be read in, rendered, and finally passed to Sphinx for
further processing. Additionally for debugging purposes the output from rendering will be stored in the same
directory as the source file with a ``.rendered`` suffix (e.g. ``index.rst.rendered``),
in case the Sphinx build raises errors.

.. dropdown:: Show Example
    :animate: fade-in-slide-down

    .. tab-set::

        .. tab-item:: Source File

            .. code-block::

                {{ heading(ctx.local.test.test_name|req, 1) }}

                {{ h2("Some plots") }}


        .. tab-item:: Rendered Source File

            .. code-block::

                Dummy 1
                #######

                Some plots
                **********

Like mentionen in the :ref:`Introduction <intro:Introduction>`, the main user groups of Pharaoh are
**Template Designers** and **End-Users**.

**Template Designers** are responsible for creating templates for the **End-Users** of Pharaoh.
In order to make report generation as easy as possible for the end users, following template design guidelines
have to be considered:

-   **Tradeoff between flexibility and complexity for end-users**

    If the designer hides much of the template code (e.g. through :ref:`reference/templating:Template Inheritance`)
    and leaves the end user with just template extensions and configurations,
    the reports will gain a lot of maintainability (report can be just re-build with updated base templates).

    If the designer just provides component templates with less abstraction, a lot of template code will
    reside in the user's report projects. This template code can only be updated by re-generating the
    report project with updated component templates.

    So the general rule-of-thumb is to put all static template content or content that just needs configuration
    in a base template and let the user just overwrite certain sections that are meant for it.

-   **Provide an abstraction library**

    Provide a small Python library to further standardize and reduce the amount of code users have to write in
    their asset scripts.

-   Build smaller modular templates that can be composed together



Template Inheritance
++++++++++++++++++++

Pharaoh templates support `Template Inheritance through Jinja
<https://jinja.palletsprojects.com/en/3.1.x/templates/#template-inheritance>`_,
which is one of the most powerful and useful features of any template engine.
It means one template can inherit from another template.

Generally, many report pages require the same or a similar layout and content for different pages,
so we use template inheritance to not repeat the same code in each template.

A base template contains the basic layout which is common to all the other templates,
and it is from this base template we extend or derive the layout for other pages.

In order to use inherit from base templates, those base templates must be discoverable via lookup paths.
Those lookup paths can be declared through:

    -   :ref:`Pharaoh plugins <plugins/plugin:Plugin Architecture>`
    -   a Sphinx configuration variable ``pharaoh_jinja_templates`` in ``report-project/conf.py``.

        This is a list of absolute or relative (to conf.py parent directory) lookup paths for base templates.

        Per default this is set to ``["user_templates"]``, which is an emtpy directory created by the default
        Pharaoh Sphinx project template.

        Base template inside those lookup paths can be referenced via their relative path to the lookup directory,
        so if we take this example:

            .. code-block:: none

                ...
                📁 user_templates
                ├── 📄 baseA.rst
                └── 📁 others
                    └── 📄 baseB.rst

        Then your templates could inherit from those templates like this:

            .. code-block:: none

                {% extends "baseA.rst" %}
                {% block xyz %}
                {# Insert block xyz content from baseA.rst #}
                {{ super() }}
                Some additional content
                {% endblock %}

            or

            .. code-block:: none

                {% extends "others/baseB.rst" %}
                {% block xyz %}
                {# Overwrites block xyz content from others/baseB.rst #}
                Some additional content
                {% endblock %}



.. dropdown:: Example
    :open:

    .. tab-set::

        .. tab-item:: Base Template ``base.rst``

            The following base template defines an immutable page title and three sections with
            immutable titles and a block declaration:

            .. code-block:: none

                {{ h1("Standardized Report Title") }}

                {{ h2("Prologue") }}
                {% block prologue %}
                This is a default content that may be overwritten by the child template
                {% endblock %}

                {{ h2("Test Description") }}
                {% block test_description %}
                {% endblock %}

                {{ h2("Plots") }}
                {% block plots %}
                {% endblock %}

        .. tab-item:: Child Template ``index.rst``

            The following child template inherits from ``base.rst`` and overwrites two of the the declared blocks with
            custom content, and extends block ``prologue``:

            .. code-block:: none

                {% extends "base.rst" %}

                {% block prologue %}
                {{ super() }}

                Additional content...
                {% endblock %}

                {% block test_description %}
                Some descriptive text...
                {% endblock %}

                {% block plots %}
                .. pharaoh-asset:: plot_name == "bla"

                {% endblock %}



Rendering Context
+++++++++++++++++

During build-time templating you have access to a variety of context variables via Jinja variable ``ctx``.
``ctx`` is a nested dictionary that allows dotted-access (``{{ ctx.project.component_name }}`` or
``{{ ctx["project"]["component_name"] }}``) to all static or dynamic rendering context defined by Pharaoh or the user.

.. code-block::

    ctx                             # The root variable for accessing rendering context
       .project                     # Project related context - set by Pharaoh
               .instance            # The Pharaoh project instance itself
               .component_name      # The name of the current component the template resides in
       .config                      # The content of Sphinx's `conf.py`, e.g. `ctx.config.copyright`
       .user                        # User defined context of dict variable `pharaoh_jinja_context` in `conf.py`
       .local                       # Component's local static & dynamically generated context - see below


``ctx.local`` is a special local context that may be different for each component or even each source file
(but that's rarely a use-case) of a component.
It is composed by reading in so-called "local context files", that reside next to the file that is
currently rendered.
Those files can be:

    -   YAML files with the naming scheme ``<contextname>_context.yaml``.
        So the content of a YAML file called ``default_context.yaml`` would be available via ``ctx.local.default``.

        .. note:: YAML files are loaded using the `OmegaConf library <https://omegaconf.readthedocs.io/>`_.

    -   Python files with the naming scheme ``<contextname>_context.py``.

        Those Python scripts are executed and must create a dict variable called ``context``.

        Since asset generation has already been executed, these scripts can also access the
        :class:`AssetFinder <pharaoh.assetlib.finder.AssetFinder>` instance to find and read assets
        to extend the render context.

        .. dropdown:: Show Example ``test_context.py``
            :animate: fade-in-slide-down

            .. code-block::

                """
                This script searches all JSON assets that have "context_name" metadata set,
                loads them and exports their content as context for rendering via
                variable `ctx.local.<context_name>`
                """
                import json
                from pharaoh.assetlib.api import get_asset_finder, get_current_component

                finder = get_asset_finder()
                component_name = get_current_component()

                # Find all assets of type JSON that have a "context_name" meta data set.
                # Collect the content of those files in a dict using the "context_name" meta data as key.
                context = {
                    asset.context.context_name: asset.read_json()
                    for asset in finder.search_assets(
                        'asset.suffix == ".json" and "context_name" in asset.context',
                        [component_name]
                    )
                }

    -   Data context that is registered via the :func:`pharaoh.assetlib.api.register_templating_context` function.


Extending Template Syntax
+++++++++++++++++++++++++

See :ref:`Templating Builtins <reference/api:Templating Builtins>` for a complete list of builtin globals, filters and
tests you can use in your templates.

If you like to add you own, Pharaoh provides some entrypoints in ``report-project/conf.py``:

``pharaoh_jinja_filters``
    A dict that maps names to filter functions::

        pharaoh_jinja_filters = {
            "angry": lambda text: text + " 😠"    # Usage: {{ "error"|angry }}
        }


``pharaoh_jinja_globals``
    A dict that maps names to global functions::

        pharaoh_jinja_globals = {
            "angry": lambda text: text + " 😠"    # Usage: {{ angry("error") }}
        }

``pharaoh_jinja_tests``
    A dict that maps names to tests::

        pharaoh_jinja_tests = {
            "angry_text": lambda text: "😠" in text    # Usage: {% if "😠" is angry %}Someone is angry!{% endif %}
        }

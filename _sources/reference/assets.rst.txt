Assets
======

What's an Asset?
----------------

Each Pharaoh components has a directory called ``asset_scripts``, that contain scripts Python scripts or
Jupyter Notebooks, that extract information from resources (local result files like HDF5, databases or other sources)
and transform this information into plot, tables and any other kind of types.

The generated files are called **Assets** and may be directly referenced/embedded by a template
(like a picture, plot or table) or indirectly referenced by a template to provide context values for template rendering.

The component's templates then *consume* these assets while Sphinx renders the template to HTML.
*Consume* means that some of the assets are directly included in the template via the
:ref:`Pharaoh asset directive <reference/directive:Pharaoh Directive>` and others are read by
:ref:`local context scripts <reference/templating:Rendering Context>` to use their content during templating.



Executing Asset Generation
--------------------------

Asset generation is executed before the actual Sphinx build via
:func:`generate_assets() <pharaoh.project.PharaohProject.generate_assets>`.

.. automethod:: pharaoh.project.PharaohProject.generate_assets
    :noindex:

Besides calling the API function, also the CLI can be used:

-   From within PyCharm or wherever you have the **venv** activated that has Pharaoh installed, you can use the
    :ref:`Pharaoh CLI <reference/cli:cli>`::

        cd <your Pharaoh project directory>
        pharaoh generate  # for generating assets of all components
        pharaoh generate -f "dummy_.*"  # for generating assets of all components starting with "dummy_"
        pharaoh generate -f dummy_1  -f dummy_2  # only for dummy_1 and dummy_2

-   Via a terminal (PS or CMD) from within the project directory, where CMD scripts are generated for your convenience::

    .\pharaoh-generate-assets.cmd  # for generating assets of all components
    .\pharaoh.cmd generate -f dummy_1

.. placeholder line, otherwise PyCharm does not show the next heading outline in the structure viewer :)

Debugging Asset Scripts
-----------------------

Asset scripts can be debugged in two different ways:

-   Via Pharaoh Asset Generation

    Generated Pharaoh project ship a debug script ``debug.py``.
    Just open your generated project in an IDE with an interpreter/venv that has Pharaoh installed and start a debug
    session on ``debug.py``.

    The script should be modified to your current needs, e.g. if you just want to debug asset generation,
    comment out the ``proj.build_report()`` line. If you like to debug asset scripts of a single component,
    pass the component name like this ``proj.generate_assets(component_filters=("dummy_1",))``.

    .. important:: If the setting ``asset_gen.worker_processes`` is set to a non-zero integer or ``"auto"``,
        then asset scripts are executed as child processes.

        Make sure you have the PyCharm debugger option
        ``File | Settings | Build, Execution, Deployment | Python Debugger ->
        Attach to subprocess automatically while debugging`` enabled.

-   Directly debug your script

    You can execute your asset scripts directly via your IDE of choice. Any functions you import from
    :ref:`pharaoh.api <reference/api:Pharaoh API Module>` or
    :ref:`pharaoh.assetlib.api <reference/api:Asset Generation API Module>` are built in a way to support
    being executed outside of a Pharaoh asset generation.

    The main difference is, that Pharaoh is not monkey-patching any toolkit (Plotly, Bokeh, Pandas) function,
    so the functions are behaving according to their official documentation.
    So statements like ```fig.write_image("myplot.png")`` are storing the plot in the current working directory
    (this is the same directory your asset script is in), instead of ``report-project\.asset_build``.

    .. seealso:: :ref:`reference/assets:Patched Frameworks`


Implementing Asset Scripts
--------------------------

This section shows how asset scripts are developed.

For simplicity we will show first how to generate assets without the use of resources.
An example on how to access resources can be found in the :ref:`Resources Reference <reference/components:Resources>`.

Refresher: A components asset scripts are always located in the component's subdirectory ``asset_scripts``.

The script names do not matter but certain names may be ignored
(see :func:`generate_assets() <pharaoh.project.PharaohProject.generate_assets>`).

Let's assume we want to make a plot as our first asset in a script called ``my_plot.py``::

    import plotly.express as px

    from pharaoh.assetlib.api import metadata_context

    fig = px.scatter(
        data_frame=px.data.iris(),  # Famous example IRIS data set
        x="sepal_width",
        y="sepal_length",
        color="species",
        symbol="species",
        title="IRIS Example",
    )

    with metadata_context(label="my_plot"):
        fig.write_html(file="iris_scatter.html")

Now let's analyse what we got:

#.  ``import plotly.express as px``

    Import a plotting framework of choice. Some frameworks are better supported by Pharaoh than others, we'll see this
    later also in the :ref:`reference/assets:Patched Frameworks` section.

#.  ``from pharaoh.assetlib.api import metadata_context``

    Any API function you will need can be imported from the ``pharaoh.assetlib.api`` module.
    The purpose of ``metadata_context`` is explained later.

#.  ``fig = px.scatter(...)``

    Create a Plotly figure with some example data.
    Your own scripts would actually read the resources specified with the component and create plots, tables etc.

#.  ``with metadata_context(label="my_plot"):``

    This context manager determines the metadata the asset will be stored with.
    This metadata is then used to include assets in a template, in this case this would look like this:

    .. code-block:: none

        .. pharaoh-asset::
            :filter: label == "my_plot"
            :template: iframe
            :iframe-width: 500px
            :iframe-height: 500px

    This so-called `Sphinx directive <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html>`_
    is a custom Sphinx directive (:ref:`click here for docs <reference/directive:Pharaoh Directive>`)
    Pharaoh adds via the plugin system of Sphinx.

    ``metadata_context`` is explained in more detail in the :ref:`next section <reference/assets:Metadata Stack>`.

#.  ``fig.write_html(file="iris_scatter.html")``

    This is where Pharaoh is doing it's *magic*.

    ``plotly.graph_objects.Figure.write_html`` is one of many function which is
    `monkey-patched <https://medium.com/@chipiga86/python-monkey-patching-like-a-boss-87d7ddb8098e>`_
    by Pharaoh. More info about the other patched frameworks you can find :ref:`here <reference/assets:Patched Frameworks>`.

    If the asset script is executed via Pharaoh, the patched ``write_html`` function will not store the plot to
    ``"iris_scatter.html"`` in the current working directory, but rather in a predefined location for assets inside
    your Pharaoh project ``report_project/.asset_build/<component-name>`` with a unique suffix, for example
    ``iris_scatter_9c30799b.html``.

    Next to the actual asset, an **asset-info** file ``iris_scatter_9c30799b.assetinfo``
    is stored that holds the metadata for the asset.
    Here is a (shortened) content example:

    .. _example_asset_info:

    .. code-block:: json

        {
            "asset": {
                "script_name": "my_plot.py",
                "script_path": "C:\\...\\project\\report-project\\components\\dummy_1\\asset_scripts\\my_plot.py",
                "index": 1,
                "component_name": "dummy_1",
                "user_filepath": "iris_scatter.html",
                "file": "C:\\...\\project\\report-project\\.asset_build\\dummy_1\\iris_scatter_9c30799b.html",
                "name": "iris_scatter_9c30799b.html",
                "stem": "iris_scatter_9c30799b",
                "suffix": ".html",
                "template": "raw_html"
            },
            "label": "my_plot"
        }

    This has following advantages:

    -   Finding names for assets is completely unnecessary, since they get a unique name assigned and are included in
        templating through their metadata rather than their file name.
        You could basically name all your assets ``asset.<suffix>``.

        So for example if you would create a single plot of a signal for 100 operating conditions like Vdd,
        you would not add the value of Vdd to the file name, but rather put it in the metadata
        (see :ref:`here <reference/assets:Metadata Stack>`) and name the file always ``"<signal-name>.png"``.

        .. note:: Though the assets name does not matter, its suffix does.
            It is used internally so make sure you add it.

    -   If the script is directly executed by the user, ``write_html`` is not patched and saves the plot to
        ``"iris_scatter.html"`` in the current working directory.

.. seealso:: :ref:`Asset Script Examples <examples/asset_scripts:Asset Scripts>`

Metadata Stack
++++++++++++++

The metadata stack is a construct that helps assigning metadata to generated assets.

Use the context manager returned by
:func:`metadata_context() <pharaoh.assetlib.api.metadata_context>` in your asset scripts
to dynamically add/remove/update metadata that is added to your assets.

Let's explained based on an example::

    from pharaoh.assetlib.api import metadata_context, register_asset

    # Will have no metadata (except the default ones added by Pharaoh)
    register_asset("<some-file>")

    # Will have metadata: {"foo": "bar"} only
    register_asset("<some-file>", dict(foo="bar"))

    with metadata_context(a=1):
        register_asset("<some-file>")  # Will have metadata: {"a": 1} only

        with metadata_context(a=2, b=3):
            register_asset("<some-file>")  # Will have metadata: {"a": 2, "b": 3}

        with metadata_context(c=4):
            register_asset("<some-file>")  # Will have metadata: {"a": 1, "c": 4}

        for i in range(10):
            with metadata_context(e=i):
                register_asset("<some-file>")  # Will have metadata: {"a": 1, "e": i}


.. note:: If you don't want to use the context manager, because the metadata should be set globally in the script anyway
    or you're asset script is a Jupyter Notebook (no context manager over multiple cells possible),
    you can also use the :func:`activate()` and :func:`deactivate()` method::

        metadata_context(...).activate()
        register_asset("<some-file>")

    Or if you want to deactivate the context again::

        mc = metadata_context(...).activate()
        register_asset("<some-file>")
        mc.deactivate()


The function :func:`register_asset() <pharaoh.assetlib.api.register_asset>` is explained in the next section.

Manually Registering Assets
+++++++++++++++++++++++++++

The function :func:`register_asset() <pharaoh.assetlib.api.register_asset>` may be used to manually register
assets of any type.

This is mainly used if you like to create assets that are not generated via
:ref:`patched framework functions <reference/assets:Patched Frameworks>`, like txt, json, rst files or
generated via frameworks not yet supported, like *seaborn*.

Here some examples::

    register_asset("some-path.html", dict(label="my_html_snippet"), template="raw_html")

    data = b"""<div><p>This HTML text was generated by an asset script!</p></div>"""
    register_asset("raw.html", dict(label="my_html_snippet"), template="raw_html", data=io.BytesIO(data))

    data = b""".. important:: This reStructuredText text was generated by an asset script!"""
    register_asset("raw.rst", dict(label="my_rst_snippet"), template="raw_rst", data=io.BytesIO(data))

    data = b'This text was generated by an asset script and will be included via "literalinclude"'
    register_asset("raw.txt", dict(label="my_txt_snippet"), template="raw_txt", data=io.BytesIO(data))


Patched Frameworks
++++++++++++++++++

Pharaoh `monkey-patches <https://medium.com/@chipiga86/python-monkey-patching-like-a-boss-87d7ddb8098e>`_
plot/table export functions of popular tools like Pandas, Plotly etc.

This has the advantage, that users can work with the official plotting APIs of the respective frameworks
without having to take care about :ref:`reference/assets:manually registering assets`.

The following APIs are patched by Pharaoh:

Pandas
    -   `pandas.DataFrame.to_html() <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_html.html>`_

        Automatically sets metadata ``template="datatable"`` (see :ref:`reference/directive:Asset Templates`) .
    -   but NOT `pandas.io.formats.style.Styler.to_html()
        <https://pandas.pydata.org/docs/reference/api/pandas.io.formats.style.Styler.to_html.html#
        pandas-io-formats-style-styler-to-html>`_

        Styler instances have to be exported manually::

            html_file_name = "styled_table.html"
            styler.to_html(buf=html_file_name)
            register_asset(html_file_name, template="datatable")

    Examples::

        import pandas as pd

        df = pd.DataFrame(
            {
                "blabla": ["a", "b", "c"],
                "ints": [1, 2, 3],
                "float": [1.5, 2.5, 3.5],
                "hex": ["0x11", "0x12", "0x13"],
            }
        )
        df.to_html(buf="table.html")

Plotly
    -   `plotly.io.show() <https://plotly.github.io/plotly.py-docs/generated/plotly.io.show.html>`_

        When running in Pharaoh asset generation, this function is patched to prevent showing the plot in the browser.
    -   `plotly.io.write_image() <https://plotly.github.io/plotly.py-docs/generated/plotly.io.write_image.html>`_

    -   `plotly.io.write_html() <https://plotly.github.io/plotly.py-docs/generated/plotly.io.write_html.html>`_

        Supports :ref:`reference/assets:Force Static Exports`.

    Examples::

        import plotly.express as px

        fig = px.scatter(
            data_frame=px.data.iris(), x="sepal_width", y="sepal_length",
            color="species", symbol="species", title=r"A title",
        )

        fig.write_image(file="iris_scatter1.svg")
        fig.write_html(file="iris_scatter2.html")
        fig.write_image(file="iris_scatter3.png", width=500, height=500)

Bokeh

    -   `bokeh.io.show() <https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.show>`_

        When running in Pharaoh asset generation, this function is patched to prevent showing the plot in the browser.
    -   `bokeh.io.saving.save() <https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.save>`_

        Supports :ref:`reference/assets:Force Static Exports`.

    -   `bokeh.io.export_png() <https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.export_png>`_
    -   `bokeh.io.export.export_png()
        <https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.export.export_png>`_
    -   `bokeh.io.export_svg() <https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.export_svg>`_
    -   `bokeh.io.export.export_svg()
        <https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.export.export_svg>`_

    Examples::

        from bokeh.io import save
        from bokeh.plotting import figure
        from bokeh.sampledata.iris import flowers

        colormap = {"setosa": "red", "versicolor": "green", "virginica": "blue"}
        colors = [colormap[x] for x in flowers["species"]]

        p = figure(title=f"Iris Morphology", width=400, height=400)
        p.xaxis.axis_label = "Petal Length"
        p.yaxis.axis_label = "Petal Width"
        p.scatter(flowers["petal_length"], flowers["petal_width"], color=colors, fill_alpha=0.2, size=10)

        save(p, filename="iris_scatter.html")

Matplotlib

    -   `matplotlib.pyplot.show() <https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.show.html>`_

        When running in Pharaoh asset generation, this function is patched to prevent showing the plot in the browser.
    -   `matplotlib.figure.Figure.show()
        <https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure.show>`_

        When running in Pharaoh asset generation, this function is patched to prevent showing the plot in the browser.
    -   `matplotlib.figure.Figure.savefig()
        <https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure.savefig>`_

    Examples::

        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots()
        ax.plot(np.arange(0.0, 2.0, 0.01), 1 + np.sin(2 * np.pi * t))
        ax.set(xlabel='time (s)', ylabel='voltage (mV)', title='About as simple as it gets, folks')
        ax.grid()

        fig.savefig("test.png")
        plt.show()

Holoviews
    -   `holoviews.util.save() <https://holoviews.org/reference_manual/holoviews.util.html#holoviews.util.save>`_
        with backends Bokeh, Plotly and Matplotlib.

        Supports :ref:`reference/assets:Force Static Exports`.

    Examples::

        import holoviews as hv
        data = [(i, chr(97 + j), i * j) for i in range(5) for j in range(5) if i != j]

        with metadata_context(ext="plotly"):
            hv.extension("plotly")
            model = hv.HeatMap(data).opts(cmap="RdBu_r", width=400, height=400)
            hv.save(model, "heatmap_holo_plotly.html")
            hv.save(model, "heatmap_holo_plotly.svg")
            hv.save(model, "heatmap_holo_plotly.png")

        with metadata_context(ext="bokeh"):
            hv.extension("bokeh")
            model = hv.HeatMap(data).opts(cmap="RdBu_r", width=400, height=400)
            hv.save(model, "heatmap_holo_bokeh.html")
            hv.save(model, "heatmap_holo_bokeh.png")

        with metadata_context(ext="matplotlib"):
            hv.extension("matplotlib")
            model = hv.HeatMap(data).opts(cmap="RdBu_r")
            hv.save(model, "heatmap_holo_mpl.svg")
            hv.save(model, "heatmap_holo_mpl.png")


``plotly.graph_objects.Figure.write_html`` is one of many function which is

by Pharaoh. More info about the other patched frameworks you can find :ref:`here <reference/assets:Patched Frameworks>`.

If the asset script is executed via Pharaoh, the patched ``write_html`` function will not store the plot to
``"iris_scatter.html"`` in the current working directory, but rather in a predefined location for assets inside
your Pharaoh project ``report_project/.asset_build/<component-name>`` with a unique suffix, for example
``iris_scatter_9c30799b.html``.


Force Static Exports
++++++++++++++++++++

While for debugging and interactive review it's nice to have all plots rendered as dynamic elements in HTML,
other build targets might be used for export purposes like Confluence or LaTeX.

Since those targets don't support embedding dynamic HTML elements you would have to tweak your asset generation scripts
to export different formats for different report output formats, which is suboptimal.

Pharaoh therefore provides a setting ``asset_gen.force_static`` which can be used to signal asset scripts
to export static assets instead of HTML.

For all patched plotting APIs, if ``asset_gen.force_static`` is set to ``true``,
Pharaoh takes care and exports static images instead of HTML when plotting APIs like
`plotly.io.write_html() <https://plotly.github.io/plotly.py-docs/generated/plotly.io.write_html.html>`_ is used.

Since not all frameworks are patched, you might have to add support by yourself inside asset scripts like this::

    import altair as alt  # altair not supported at the moment

    from pharaoh.api import get_project
    from pharaoh.assetlib.api import register_asset

    pharaoh_project = get_project(__file__)
    force_static = project.get_setting("asset_gen.force_static")

    chart = alt.Chart(...)

    if force_static:
        filename = "chart.png"
    else:
        filename = "chart.html"

    chart.save(filename)
    register_asset(filename, dict(plotting_framework="altair"))


.. seealso:: :ref:`reference/settings:Accessing Settings`


Matlab Integration
++++++++++++++++++

Pharaoh supports generating assets via Matlab scripts/function through the
Matlab API :class:`pharaoh.assetlib.api.Matlab`.

The asset scripts still have to be Python scripts and any asset the Matlab scripts generate, have to be
manually registered using :func:`register_asset() <pharaoh.assetlib.api.register_asset>`.

Here an example::

    from pharaoh.assetlib.api import Matlab, register_asset, FileResource, get_resource

    resource: FileResource = get_resource(alias="<resource_alias>")
    some_resource_path: Path = resource.locate()

    with Matlab() as matlab:
        plot_path, out, err = matlab.execute_function("generate_plot", [str(some_resource_path)], nargout=1)

    register_asset(plot_path, dict(from_matlab=True, foo="bar"))

To use the Matlab API you have to install an additional dependency, depending on your Matlab version:

    -   R2020B: ``pip install matlabengine==9.9.*``
    -   R2021A: ``pip install matlabengine==9.10.*``
    -   R2021B: ``pip install matlabengine==9.11.*``
    -   R2022A: ``pip install matlabengine==9.12.*``
    -   R2022B: ``pip install matlabengine==9.13.*``
    -   R2023A: ``pip install matlabengine==9.14.*``
    -   R2023B: ``pip install matlabengine==9.15.*``


Asset Lookup
------------

This section deals with how to access assets in :ref:`local context scripts
<reference/templating:Rendering Context>` and :ref:`build-time templates <reference/templating:Build-time Templating>`.

Asset Finder
++++++++++++

The :class:`AssetFinder <pharaoh.assetlib.finder.AssetFinder>` is responsible for discovering and searching assets
based on filters using :func:`AssetFinder.search_assets() <pharaoh.assetlib.finder.AssetFinder.search_assets>`.

This function is available in various places:

-   In :ref:`local context scripts <reference/templating:Rendering Context>`.

    The following script searches all JSON files that have ``"context_name"`` set,
    loads them and exports their content as context for :ref:`build-time templating <reference/templating:Build-time Templating>`::

        import json
        from pharaoh.assetlib.api import get_asset_finder, get_current_component

        finder = get_asset_finder()
        component_name = get_current_component()

        context = {
            asset.context.context_name: json.loads(asset.read_text())
            for asset in finder.search_assets(
                'asset.suffix == ".json" and "context_name" in asset.context',
                [component_name]
            )
        }
        context["component_name"] = component_name
        return context

    In some use cases this is used to make measurement information available during templating
    to render the information in a table.

-   In templates inside `Jinja statements
    <https://jinja.palletsprojects.com/en/3.0.x/templates/#list-of-control-structures>`_.

    The following snippet searches all image assets of the **current** component
    (the component the template is rendered in) and stores the list of assets in a variable::

        {% set image_assets = search_assets("asset.suffix in ['.png', '.svg']") %}

    The following snippet searches all image assets of the **all** components in the project.
    This can be used to create components that summarize information from other components.

    ::

        {% set all_image_assets = search_assets_global("asset.suffix in ['.png', '.svg']") %}

    The used functions ``search_assets`` and ``search_assets_global`` are
    `partial functions <https://www.learnpython.org/en/Partial_functions>`_ where the ``component`` argument is preset.



Manual Include
++++++++++++++

If you like to include some of your assets manually, the template environment provides
two functions for your convenience, that return the (relative) path of an asset to the including template:

``asset_rel_path_from_project(asset)``
    Returns the relative path from the Sphinx source directory to the passed asset.
    This path is needed for Sphinx directives that themselves take care to copy the asset into the build directory,
    like directives ``literalinclude``, ``image`` and ``figure``.

    Here's an example:

    .. code-block:: none

        {% set matches = search_assets("<some condition>") %}

        .. figure:: {{ asset_rel_path_from_project(matches[0]) }}
           :scale: 50 %

           This is the caption of the figure (a simple paragraph).

    where ``{{ asset_rel_path_from_project(matches[0]) }}`` would render something like this:
    ``/.asset_build/dummy/mytxt_f65223c4.txt``


``asset_rel_path_from_build(asset)``
    Returns the relative path from the Sphinx build directory to the passed asset.
    This path is needed for Sphinx directives that themselves do **NOT** take care to copy the asset into the
    build directory, like when using the ``raw_html`` directive and including a picture or HTMl file using an iframe.

    In this case calling ``asset_rel_path_from_build`` will automatically copy the asset from the asset build folder
    to the build directory and return it's relative path from the including template.

    Here's an example:

    .. code-block:: none

        {% set matches = search_assets("<some condition>") %}

        .. raw:: html

            <iframe src="{{ asset_rel_path_from_build(matches[0]) }}"
                loading="lazy"
            ></iframe><br>

    where ``{{ asset_rel_path_from_build(matches[0]) }}`` would render something like this:
    ``../../pharaoh_assets/iris_scatter_3e7d7ab7.html``

.. note:: Another way to include assets with a custom template is to use the ``template``
    :ref:`option <reference/directive:Directive Options>` of the
    :ref:`Pharaoh asset directive <reference/directive:Pharaoh Directive>` with a path to your custom template.


Grouping Assets By Metadata
+++++++++++++++++++++++++++

Imaging in your asset scripts you are creating a plot for a measured signal for many different operating conditions:

.. code-block:: none

    from pharaoh.assetlib.api import metadata_context

    for vdd in (8.0, 10.0, 12.0):
        for iout in (1.0, 2.0, 5.0):
            with metadata_context(vdd=vdd, iout=iout, signal_name="idd"):
                fig = ...
                fig.write_image(file="idd_plot.png")


Now in your report you may like to have all those plots added separately each with it's own title containing the
values of either ``vdd`` or ``iout``.

Defining the template like this is not really viable, since in the template you usually have no idea about what values
were iterated over in the asset script. But let's assume you know, then this would be the template:

.. code-block:: none

    {% for vdd in (8.0, 10.0, 12.0) %}
    {{ heading("Plots for Vdd:%.1fV, Iout:%.1fA" % vout, 2 }}

    {% for iout in (1.0, 2.0, 5.0) %}
    {{ heading("Plots for Iout:%.1fA" % iout, 3 }}

    .. pharaoh-asset:: vdd == {{ vdd }} and iout == {{ iout }} and signal_name == 'idd'

    {% endfor %}
    {% endfor %}

But luckily there is a better option using :func:`asset_groupby <pharaoh.assetlib.finder.asset_groupby>` to
group assets first by ``vdd`` and then by ``iout``:

.. code-block:: none

    {% set idd_plots = search_assets("signal_name == 'idd'") %}
    {% for vdd, assets_grby_vdd in agroupby(idd_plots, key="vdd").items() %}
    {{ heading("Plots for Vdd:%.1fV" % vout, 2 }}

        {% for iout, assets_grby_iout in agroupby(assets_grby_vdd, key="iout").items() %}
    {{ heading("Plots for Iout:%.1fA" % iout, 3 }}

            {% for asset in assets_grby_iout %}
    .. pharaoh-asset:: {{ asset.id }}

            {% endfor %}
        {% endfor %}
    {% endfor %}

.. note:: ``agroupby`` is an alias for ``asset_groupby``. Both are available as global function during templating.

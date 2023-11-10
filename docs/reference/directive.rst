
Pharaoh Directive
=================


A `Sphinx Directive <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html>`_
is a generic block of explicit markup.
Along with roles, directives are one of the extension mechanism, a way of adding support for new constructs
without adding new primary syntax (directives may support additional syntax locally).
And Sphinx makes heavy use of it.

All `standard directives <https://docutils.sourceforge.io/docs/ref/rst/directives.html>`_ are always available,
whereas any other directives are domain-specific
(see `Writing Sphinx Extensions <https://www.sphinx-doc.org/en/master/development/index.html>`_)
and may require special action to make them available when processing the document,
like the **Pharaoh Asset** directive.

The **Pharaoh Asset** directive ``pharaoh-asset`` is added via the Pharaoh Sphinx extension and allows users
to include assets in the document, based on one or multiple filter conditions.

The matched assets are then rendered using :ref:`predefined templates <reference/directive:Asset Templates>`
that can be specified in the asset metadata.

The ``pharaoh-asset`` directive consists of a name, arguments, options and content, e.g:

    .. code-block:: none

        .. pharaoh-asset:: key1 == "A" or
                           key2 == "B"
            :filter: key3 == "C"
            :index: 0

            key4 == "D";
            key5 == "E"

    -   ``pharaoh-asset`` is the name
    -   ``key1 == "A" or key2 == "B"`` is an argument
    -   ``:filter: key3 == "C"`` and ``:index: 0`` are options
    -   ``key4 == "D";key5 == "E"`` is the content

    .. note::

        The directive supports 3 ways to define an asset filter, all of them can be used in parallel and are **AND**-ed:
        the argument, the ``:filter:`` option and the content.

        The filters are treated as multiline statements and are split only on unescaped ``;`` characters.
        This means ``key4 == "D";key5 == "E"`` is effectively the same as ``key4 == "D" and key5 == "E"``

        The directive internally uses the :func:`AssetFinder.search_assets()
        <pharaoh.assetlib.finder.AssetFinder.search_assets>` function, so the same rules apply to the filter strings.

If your filter matches multiple assets, all matches will be rendered one after another.
This can look quite messy very fast, so there is another option to add some more information to each rendered asset
by the combined use with the :func:`AssetFinder.search_assets()
<pharaoh.assetlib.finder.AssetFinder.search_assets>` function,
where the directive simply gets the ID of the asset to include.

    Following template example will search for all images. If at least one exists a new section will be created and the
    images are added, each under its own `rubric <https://www.sphinx-doc.org/en/master/usage/restructuredtext/
    directives.html#directive-rubric>`_:

    .. code-block:: none

        {% set image_assets = search_assets("asset.suffix in ['.png', '.svg']") %}

        {% if image_assets|length %}
        {{ h2("Images") }}

         {% for asset in image_assets %}
        .. rubric:: {{ asset.context.caption }}

        .. pharaoh-asset:: {{ asset.id }}

         {% endfor %}
        {% endif %}

    .. important:: In this case the asset's ID must be the one-and-only filter that is given!


Directive Options
-----------------

Following options may be used for the ``pharaoh-asset`` directive:

``:filter:``
    The filter (multiline string, ``;``-separated) to select assets by metadata. See example above.

``:optional:``
    If false (default), the asset filter MUST match any asset, otherwise an exception is raised.

    Valid values: ``true/yes/1``, ``false/no/0``

``:index:``
    If the filters match multiple assets, only render the assets with specified index (0-based).

    Following style is possible: ``1,2,4-8,9`` (like selecting pages to print). Whitespace is ignored.

``:components:``
    A comma-separated string of component names to look for assets (see :func:`AssetFinder.search_assets()
    <pharaoh.assetlib.finder.AssetFinder.search_assets>`).

    Special values:

    -   ``_this_`` (default): Searches only the current component the template is rendered in
    -   ``_all_``: Searches all components

``:template:``
    The template to use to embed the asset into the document.
    It may be a template name as described in :ref:`reference/directive:Asset Templates` or
    a file path to your own template. Please note that relative paths are resolved with the Pharaoh project directory
    as root directory).

    If not specified as option to the directive, the asset metadata ``asset.template`` is looked up
    (which maybe gets a default template automatically determined by the asset's file suffix).

    If the template is set neither via option nor asset metadata, an error will be raised.

    .. note:: Another way to include assets manually is described :ref:`here <reference/assets:Manual Include>`.


``:image-(alt,height,width,scale,align):``
    Passed to the ``image`` directive, if the asset is rendered as image.

``:iframe-width:``
    The width of the HTML `iframe <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe>`_.

    The default value is determined by setting ``asset_gen.default_iframe_width``.

``:iframe-height:``
    The height of the HTML `iframe <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe>`_.

    The default value is determined by setting ``asset_gen.default_iframe_height``.

``:ignore-title:``
    If asset metadata ``asset.title`` is set, the asset will be rendered under a unique
    `rubric <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-rubric>`_.
    The rubric title is a unique cross-reference.

    If this option is true, this behavior is skipped.

    Valid values: ``true/yes/1``, ``false/no/0``

``:ignore-description:``
    If asset metadata ``asset.description`` is set, the description will be inserted directly before the asset
    as raw string (so you could add reST as well).

    If this option is true, this behavior is skipped.


``:datatable-extended-search:``
    If true, assets rendered as interactive `datatable <https://datatables.net/>`_ will include an
    `interactive search builder <https://datatables.net/extensions/searchbuilder/>`_

    The default value is determined by setting ``asset_gen.default_datatable_extended_search``.

    Valid values: ``false/no/0``, ``true/yes/1``



Asset Templates
---------------

This section describes the templates used to include assets into your documents.

There are 2 options how to specify the used template:

    -   Via the :func:`register_asset() <pharaoh.assetlib.api.register_asset>` function::

            data = b'This text was generated by an asset script and will be included via "literalinclude"'
            register_asset("raw.txt", dict(label="my_txt_snippet"), template="raw_txt", data=io.BytesIO(data))

        As fallback, if ``template`` is not specified, a default template is chosen depending on the asset's file suffix:

        - ``".html"``: **iframe**
        - ``".rst"``: **raw_rst**
        - ``".txt"``: **raw_txt**
        - ``".svg"``: **image**
        - ``".png"``: **image**
        - ``".jpg"``: **image**
        - ``".jpeg"``: **image**
        - ``".gif"``: **image**
        - ``".md"``: **markdown**

    -   Via the ``:template:`` option of the Pharaoh asset directive (has priority over setting in metadata).

Following asset templates are currently supported:

    image
        The asset file will be included via the `image <https://docutils.sourceforge.io/docs/ref/rst/
        directives.html#image>`_ directive. Options on the ``pharaoh-asset`` directive starting with ``image-`` are
        passed to the image directive.

    raw_html
        The asset file will be included via the `raw:: html <https://docutils.sourceforge.io/docs/ref/rst/
        directives.html#raw-data-pass-through>`_ directive.
        The only modification is that the HTML content is pasted into a separate ``div``-tag with a unique,
        autogenerated ID and a linebreak at the end.

    markdown
        The asset file will be included via the `raw:: html <https://docutils.sourceforge.io/docs/ref/rst/
        directives.html#raw-data-pass-through>`_ directive after converting the Markdown text to HTML.

    raw_rst
        The content of the asset file will be pasted into the document without modification and no extra indentation.

    raw_txt
        The asset file will be included via the `literalinclude <https://www.sphinx-doc.org/en/master/usage/
        restructuredtext/directives.html#directive-literalinclude>`_ directive. Language highlighting is disabled.

    iframe
        The asset file will be included via the `raw <https://docutils.sourceforge.io/docs/ref/rst/
        directives.html#raw-data-pass-through>`_ directive, wrapped in an ``iframe``-tag.
        Options on the ``pharaoh-asset`` directive starting with ``iframe-`` are added to the iframe options.
        The iframe will be lazy-loaded by the browser.

    datatable
        This template can only be used in combination with HTML tables produced by
        `pandas.DataFrame.to_html() <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_html.html>`_ or
        `pandas.io.formats.style.Styler.to_html() <https://pandas.pydata.org/docs/reference/api/pandas.io.formats.style.
        Styler.to_html.html#pandas-io-formats-style-styler-to-html>`_.

        It transforms those tables into interactive JS-powered tables (see `DataTables <https://datatables.net/>`_).

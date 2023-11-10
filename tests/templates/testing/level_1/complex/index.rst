{% set static_export = get_setting("asset_gen.force_static", False) -%}

{{ heading(ctx.local.test.test_name|req, 1) }}

{{ heading("Demo Assets By Framework", 2) }}

{{ heading("Pandas", 3) }}


.. card::  Table (simple search)

    .. pharaoh-asset::
        :filter: label == "PANDAS" and foo == "styled"

.. card::  Table (extended search)

    .. pharaoh-asset::
        :filter: label == "PANDAS" and conditions.foo == 2
        :datatable-extended-search: yes

.. card::  Table (big)

    .. pharaoh-asset::
        :filter: label == "PANDAS" and huge
        :datatable-extended-search: yes


{{ heading("Bokeh", 3) }}

.. card-carousel:: 2

    {% for i in range(1, 5) %}
    .. card:: Bokeh plot where condition bar == {{ i }}

        .. pharaoh-asset::
            :filter: label == "BOKEH" and conditions.bar == {{ i }}

    {% endfor %}

{{ heading("Plotly", 3) }}

.. dropdown:: SVG
    :open:

    .. pharaoh-asset::
        :filter: label == "PLOTLY"
        :index: 0

.. dropdown:: HTML
    :open:

    .. pharaoh-asset::
        :filter: label == "PLOTLY"
        :index: 1

.. tab-set::

    .. tab-item:: PNG as figure directive (300 x 300, set by options)

        .. pharaoh-asset::
            :filter: label == "PLOTLY"
            :index: 2
            :image-width: 300
            :image-height: 300

    .. tab-item:: PNG as figure directive (500 x 500, set by asset script)

        .. pharaoh-asset::
            :filter: label == "PLOTLY"
            :index: 2


{{ heading("Matplotlib", 3) }}

.. card-carousel:: 2

    .. card:: PNG

        .. pharaoh-asset::
            :filter: label == "MPL" and asset.suffix == ".png"

    .. card:: SVG

        .. pharaoh-asset::
            :filter: label == "MPL" and asset.suffix == ".svg"


{{ heading("Holoviews", 3) }}


.. tab-set::

    .. tab-item:: Plotly

        .. grid:: 3

            .. grid-item-card:: HTML

                .. pharaoh-asset::
                    {% if static_export %}
                    :filter: label == "HOLOVIEWS" and ext == "plotly" and asset.suffix == ".png"
                    {% else %}
                    :filter: label == "HOLOVIEWS" and ext == "plotly" and asset.suffix == ".html"
                    {% endif %}
                    :iframe-width: 450
                    :iframe-height: 450

            .. grid-item-card:: SVG

                .. pharaoh-asset::
                    :filter: label == "HOLOVIEWS" and ext == "plotly" and asset.suffix == ".svg"

            .. grid-item-card:: PNG

                .. pharaoh-asset::
                    :filter: label == "HOLOVIEWS" and ext == "plotly" and asset.suffix == ".png"


    .. tab-item:: Bokeh

        .. grid:: 2

            .. grid-item-card:: HTML

                .. pharaoh-asset::
                    {% if static_export %}
                    :filter: label == "HOLOVIEWS" and ext == "bokeh" and asset.suffix == ".png"
                    {% else %}
                    :filter: label == "HOLOVIEWS" and ext == "bokeh" and asset.suffix == ".html"
                    {% endif %}
                    :iframe-width: 450
                    :iframe-height: 450

            .. grid-item-card:: PNG

                .. pharaoh-asset::
                    :filter: label == "HOLOVIEWS" and ext == "bokeh" and asset.suffix == ".png"

    .. tab-item:: Matplotlib

        .. grid:: 2

            .. grid-item-card:: SVG

                .. pharaoh-asset::
                    :filter: label == "HOLOVIEWS" and ext == "matplotlib" and asset.suffix == ".svg"

            .. grid-item-card:: PNG

                .. pharaoh-asset::
                    :filter: label == "HOLOVIEWS" and ext == "matplotlib" and asset.suffix == ".png"



{{ heading("Manual Registration", 3) }}

.. pharaoh-asset::
    :filter: label == "MANUAL_REGISTRY"

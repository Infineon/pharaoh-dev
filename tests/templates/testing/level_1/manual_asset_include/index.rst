{{ heading("Title", 1) }}

{% set plot_asset = search_assets("label == 'plot'")[0] %}
{% set txt_asset = search_assets("label == 'txt'")[0] %}

{{ assert_true(asset_rel_path_from_build(plot_asset).startswith("../../")) }}
{{ assert_true(asset_rel_path_from_project(plot_asset).startswith("/.asset_build/")) }}

.. raw:: html

    <iframe src="{{ asset_rel_path_from_build(plot_asset) }}"
        loading="lazy"
        id="iframe123"
    ></iframe><br>

.. literalinclude:: {{ asset_rel_path_from_project(txt_asset) }}

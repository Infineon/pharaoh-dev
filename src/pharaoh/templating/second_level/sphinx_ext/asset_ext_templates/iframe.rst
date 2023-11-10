{% set uuid = rand_id() %}

.. raw:: html

    <iframe src="{{ asset_rel_path_from_build(asset) }}"
        {% if opts.iframe_width %}        width="{{ opts.iframe_width }}"{% endif +%}
        {% if opts.iframe_height %}        height="{{ opts.iframe_height }}"{% endif +%}
        loading="lazy"
        id="iframe{{ uuid }}"
        style="border:none;"
    ></iframe><br>

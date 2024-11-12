{% set proj = ctx.project.instance %}
{% set component_rst_path_template = proj.sphinx_report_project_components.stem + "/{}/index" %}
{% set error_assets = search_error_assets_global() %}

{% if error_assets %}
.. error::

    :octicon:`bug;2em;sd-text-danger` Errors occurred during report generation in following components:

    **{{ error_assets.keys()|join(",") }}**

{% endif %}

{{ h1(get_setting("report.title")) }}

.. toctree::
    :maxdepth: 2

    {% for component in proj.find_components() %}
    {{ component_rst_path_template.format(component.name) }}
    {% endfor %}

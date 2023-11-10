{% set proj = ctx.project.instance %}
{% set component_rst_path_template = proj.sphinx_report_project_components.stem + "/{}/index" %}

{{ h1(get_setting("report.title")) }}

.. toctree::
    :maxdepth: 2

    {% for component in proj.find_components() %}
    {{ component_rst_path_template.format(component.name) }}
    {% endfor %}

{% set title = asset.context|oc_get("title", None) %}
{% set uuid = rand_id() %}
{% set description = asset.context|oc_get("description", None) %}
{% if title and not opts.ignore_title|d(False) %}
.. _asset_{{ uuid }}:

.. rubric:: :ref:`{{ title }} <asset_{{ uuid }}>`

{% endif %}
{% if description and not opts.ignore_description|d(False) %}
{{ description }}

{% endif %}
{{ content }}

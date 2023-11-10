=============
API Reference
=============


Pharaoh API Module
==================

Lists all items that can be imported from ``pharaoh.api``.

.. automodule:: pharaoh.api
    :members: get_project

.. autoclass:: pharaoh.project.PharaohProject
    :members:
    :undoc-members:
    :special-members: __init__


Asset Generation API Module
===========================

Lists all items that can be imported from ``pharaoh.assetlib.api``.

.. automodule:: pharaoh.assetlib.api
    :members: register_asset,metadata_context,get_resource,find_components,
        get_current_component,get_asset_finder,register_templating_context

.. autoclass:: pharaoh.assetlib.finder.AssetFinder
    :members:
    :special-members: __init__

.. autoclass:: pharaoh.assetlib.finder.Asset

.. autofunction:: pharaoh.assetlib.finder.asset_groupby


Resources
=========

.. jinja:: default

    {% for resource in resources.values() %}
    .. autoclass:: {{ resource.__module__ }}.{{ resource.__name__ }}
        :show-inheritance:
        :members:

    {% endfor %}

**Bases:**

    .. autoclass:: pharaoh.assetlib.resource.Resource
        :show-inheritance:
        :members:

    .. autoclass:: pharaoh.assetlib.resource.LocalResource
        :show-inheritance:
        :members:

    .. autoclass:: pharaoh.assetlib.resource.TransformedResource
        :show-inheritance:
        :members:



Matlab Integration API
======================

.. autoclass:: pharaoh.assetlib.api.Matlab
    :members:
    :special-members: __init__,__enter__,__exit__



Templating Builtins
===================

Following globals, filters and tests are available during build-time templating.

Jinja2 Builtins
---------------

All Jinja2 builtins are available of course:

-   `List of builtin filters <https://jinja.palletsprojects.com/en/3.1.x/templates/#list-of-builtin-filters>`_
-   `List of builtin tests <https://jinja.palletsprojects.com/en/3.1.x/templates/#list-of-builtin-tests>`_
-   `List of global functions <https://jinja.palletsprojects.com/en/3.1.x/templates/#list-of-global-functions>`_

Pharaoh Extension
-----------------

Pharaoh extends the template environment by additional globals and filters, which are described in following chapters.

Globals
+++++++

Following functions are available in the global templating scope, and can be used like variable, but all callable, e.g.
``{{ h1("Title") }}``.

.. jinja:: default

    {% for func in env_globals.to_document.values()|set %}
    .. autofunction:: {{ func.__module__ }}.{{ func.__name__ }}
    {% endfor %}

Filters
+++++++

Variables can be modified by **filters**. Filters are separated from the variable by a pipe symbol (``|``)
and may have optional arguments in parentheses.
Multiple filters can be chained. The output of one filter is applied to the next.

For example, ``{{ name|trim|title }}`` will trim whitespace from the variable *name* and title-case the output.

Filters that accept arguments have parentheses around the arguments, just like a function call.
For example: ``{{ listx|join(', ') }}`` will join a list with commas.

.. jinja:: default

    {% for func in env_filters.to_document.values()|set %}
    .. autofunction:: {{ func.__module__ }}.{{ func.__name__ }}
    {% endfor %}


Ansible Filters
---------------

Jinja2 Ansible Filters is a port of the ansible filters provided by Ansible's templating engine.

See `pypi project page <https://pypi.org/project/jinja2-ansible-filters/>`_ for a listing of all filters.

The filters are useful, but unfortunately not documented. You may refer to the
`docstrings in the source code <https://gitlab.com/dreamer-labs/libraries/jinja2-ansible-filters/-/blob/master/
jinja2_ansible_filters/core_filters.py>`_.


Plugin API
==========

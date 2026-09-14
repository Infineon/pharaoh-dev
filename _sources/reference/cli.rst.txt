CLI
===

Preface
-------

    .. literalinclude:: /cli/default.txt
        :language: none

The CLI may be used in different ways:

-   Through the PIP entrypoint ``pharaoh``

    When you install Pharaoh via PIP, it will install a ``pharaoh.exe``
    into your environment (``<installdir>/Scripts``).

    Once your environment is activated you can use the CLI via the ``pharaoh`` command.
    Some examples using CMD:

    .. code-block:: none

        cd "C:/projects/my_pharaoh_report"

        set PHARAOH.REPORT.TITLE="Some Title"

        pharaoh new
        pharaoh add --name dummy1 -t pharaoh_testing.simple --context "{'test_name':'dummy1'}"
        pharaoh add --name dummy2 -t pharaoh_testing.simple --context "{'test_name':'dummy2'}"
        pharaoh generate
        pharaoh build

    If you current working directory is not inside the Pharaoh project, add the absolute or relative (to CWD) path
    to the project as first argument like this:

    .. code-block:: none

        cd "C:/projects"

        pharaoh -p "my_pharaoh_report" new
        pharaoh -p "my_pharaoh_report" generate
        cd "my_pharaoh_report"
        pharaoh build


-   Through the generated CMD scripts ``report-project/*.cmd``

    The advantage of those scripts is, that they are working regardless of your Pharaoh Python environment being
    activated or not, since they contain the absolute path to the Python interpreter used to generate them as a
    fallback .

    Thus they are checking if ``pharaoh.exe`` is on the system path (e.g. when executing inside an
    activated virtual env - like the terminal in PyCharm), but falling back to the absolute path.

    .. important:: If you rename or move the Python environment that was used to generate the Pharaoh project,
        those CMD script won't work anymore (unless ``pharaoh.exe`` is on the system path).

    So you can just double click ``pharaoh-*.cmd`` to perform the corresponding action with default arguments.

    .. note::
        This way is just used to managed an already existing Pharaoh project, so commands like
        ``pharaoh.cmd new`` does not really make sense.

    If you like to use them via the terminal, the syntax is similar to the above examples:

        -   ``pharaoh.cmd generate`` or ``pharaoh-generate-assets.cmd``
        -   ``pharaoh.cmd build`` or ``pharaoh-build.cmd``
        -   ``pharaoh.cmd archive`` or ``pharaoh-archive.cmd``



Commands
--------

.. jinja:: default

    {% for command in cli_commands %}
    {{ command|capitalize }}
    +++++++++++++++++++++++++++++++++++++++++++++++

        .. literalinclude:: /cli/{{ command }}.txt
            :language: none

    {% endfor %}

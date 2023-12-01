{% set div_id = rand_id(6) -%}
{% set table_id = "T_%s"|format(div_id) -%}
{% set table_id_sel = "#%s"|format(table_id) -%}
.. raw:: html

    <script>
        $(document).ready(function () {
        const divItem = document.getElementById("{{ div_id }}");

        var datatable = $("{{ table_id_sel }}").DataTable({
            ordering: true,
            colReorder: true,
            keys: true,
            responsive: false,
            {% if opts.datatable_extended_search %}
            dom: 'QBlfrtip',
            {%- else %}
            dom: 'Blfrtip',
            {% endif %}
            select: {
                blurable: true,
                items: 'row',
                style: 'os',
                cells: {
                    _: "Selected %d cells",
                    0: "Click a cell to select it",
                    1: "Selected 1 cell"
                }
            },
            sScrollXInner: "100%",
            fixedHeader: true,
            scrollX: true,
            buttons: [
                'colvis',
                'excel',
                'print',
                'bulma',
                'foundation',
                'semanticui'
            ]
        });

        function isInTabContent(item) {
            try {
                const classNames = item.parentElement.className
                // if the parent element contains the class "sd-tab-content" the datatable is inside a tab element
                return classNames.includes("sd-tab-content")
            } catch (e) {
                return False
            }
        }

        if (isInTabContent(divItem)) {
            // console.log("is in tab content: " + isInTabContent(divItem))
            new ResizeObserver(() => datatable.columns.adjust()).observe(divItem.parentElement)
        }

    });
    </script>
    <style>
    {% if opts.datatable_style_override %}
    {# fixme: find a better solution here to handle multiple CSS rules #}
    #{{ div_id }} {{ opts.datatable_style_override|replace("\n", "") }}
    {% endif %}
    </style>
    <div id="{{ div_id }}">
    {{ asset.read_text() | regex_replace("(?<=[#\"'])T_[0-9a-fA-F]{5}", table_id) | indent(4) }}
    </div>
    <br>

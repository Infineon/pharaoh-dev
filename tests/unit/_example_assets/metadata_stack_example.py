from __future__ import annotations

from bokeh.io import save
from bokeh.plotting import figure
from bokeh.sampledata.iris import flowers

from pharaoh.assetlib.api import metadata_context

colormap = {"setosa": "red", "versicolor": "green", "virginica": "blue"}
colors = [colormap[x] for x in flowers["species"]]
p = figure()
p.scatter(flowers["petal_length"], flowers["petal_width"], color=colors, fill_alpha=0.2, size=10)

with metadata_context(a=1):
    save(p, filename="context_1.html")

    with metadata_context(b=2):
        save(p, filename="context_2.html")
    save(p, filename="context_3.html")

    metadata_context(c=3).activate()
    save(p, filename="context_4.html")

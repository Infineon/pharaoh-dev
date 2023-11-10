from bokeh.io import save
from bokeh.plotting import figure
from bokeh.sampledata.iris import flowers

from pharaoh.assetlib.api import metadata_context

colormap = {"setosa": "red", "versicolor": "green", "virginica": "blue"}
colors = [colormap[x] for x in flowers["species"]]


for x in range(1, 5):
    with metadata_context(conditions={"bar": x}, label="BOKEH"):
        p = figure(title=f"Iris Morphology {x}", width=400, height=400)
        p.xaxis.axis_label = "Petal Length"
        p.yaxis.axis_label = "Petal Width"
        p.scatter(flowers["petal_length"], flowers["petal_width"], color=colors, fill_alpha=0.2, size=10)

        save(p, filename="iris_scatter.html")

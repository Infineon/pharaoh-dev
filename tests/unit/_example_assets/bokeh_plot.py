from bokeh.io import export_png, export_svg, save, show
from bokeh.plotting import figure
from bokeh.sampledata.iris import flowers

colormap = {"setosa": "red", "versicolor": "green", "virginica": "blue"}
colors = [colormap[x] for x in flowers["species"]]

p = figure(title="Iris Morphology")
p.xaxis.axis_label = "Petal Length"
p.yaxis.axis_label = "Petal Width"

p.scatter(flowers["petal_length"], flowers["petal_width"], color=colors, fill_alpha=0.2, size=10)

show(p)
save(p, "iris_scatter_bokeh_1.html")
export_png(p, filename="iris_scatter_bokeh_2.png")
export_svg(p, filename="iris_scatter_bokeh_3.svg")

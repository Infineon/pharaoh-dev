# source: https://holoviews.org/reference/elements/plotly/HeatMap.html

import holoviews as hv

data = [(i, chr(97 + j), i * j) for i in range(5) for j in range(5) if i != j]

hv.extension("plotly")
model = hv.HeatMap(data).opts(cmap="RdBu_r", width=400, height=400)
hv.save(model, filename="heatmap_holo_plotly.html")
hv.save(model, filename="heatmap_holo_plotly.svg")
hv.save(model, filename="heatmap_holo_plotly.png")

hv.extension("bokeh")
model = hv.HeatMap(data).opts(cmap="RdBu_r", width=400, height=400)
hv.save(model, filename="heatmap_holo_bokeh.html")
hv.save(model, filename="heatmap_holo_bokeh.png")

hv.extension("matplotlib")
model = hv.HeatMap(data).opts(cmap="RdBu_r")
hv.save(model, filename="heatmap_holo_mpl.svg")
hv.save(model, filename="heatmap_holo_mpl.png")

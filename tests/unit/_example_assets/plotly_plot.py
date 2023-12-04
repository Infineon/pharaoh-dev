# source: https://plotly.com/python/line-and-scatter/
from __future__ import annotations

import plotly.express as px

df = px.data.iris()
fig = px.scatter(
    df,
    x="sepal_width",
    y="sepal_length",
    color="species",
    symbol="species",
    title=r"$\alpha_{1c} = 352 \pm 11 \text{ km s}^{-1} - tex, no matter what$",
)
fig.show()

fig.write_image(file="iris_scatter1.svg")
fig.write_html(file="iris_scatter2.html")

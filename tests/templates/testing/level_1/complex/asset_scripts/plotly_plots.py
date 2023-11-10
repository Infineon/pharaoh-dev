import plotly.express as px

from pharaoh.assetlib.api import metadata_context

df = px.data.iris()
fig = px.scatter(
    data_frame=df,
    x="sepal_width",
    y="sepal_length",
    color="species",
    symbol="species",
    title=r"A title",
)

with metadata_context(label="PLOTLY"):
    fig.write_image(file="iris_scatter1.svg")
    fig.write_html(file="iris_scatter2.html")
    fig.write_image(file="iris_scatter3.png", width=500, height=500)

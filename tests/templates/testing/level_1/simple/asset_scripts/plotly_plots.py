import plotly.express as px

from pharaoh.assetlib.api import metadata_context

df = px.data.iris()
fig = px.scatter(
    data_frame=df,
    x="sepal_width",
    y="sepal_length",
    color="species",
    symbol="species",
    title="A title",
)

with metadata_context(label="PLOTLY"):
    fig.write_html(file="iris_scatter.html")

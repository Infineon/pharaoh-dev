import plotly.express as px

from pharaoh.assetlib.api import metadata_context

df = px.data.iris()
fig = px.scatter(
    df,
    x="sepal_width",
    y="sepal_length",
    color="species",
    symbol="species",
    title=r"A title",
)

with metadata_context(label="PLOTLY2"):
    fig.write_html(file="iris_scatter.html")

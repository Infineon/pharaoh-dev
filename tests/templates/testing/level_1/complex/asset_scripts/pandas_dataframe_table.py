import random
import string

import numpy as np
import pandas as pd
from pandas.io.formats.style import Styler

from pharaoh.assetlib.api import metadata_context
from pharaoh.assetlib.generation import register_asset

style_df = pd.DataFrame(
    {
        "Encounter": ("Zombie Soldier", "Imp", "Cacodemon", "Hell Knight", "Cyberdemon"),
        "Challenge Rating": (1, 2, 3, 4, 5),
        "Challenge Rating Explained": (1, 2, 3, 4, 5),
        "Challenge Rating Formatted": (1, 2, 3, 4, 5),
    }
)

cell_hover = {"selector": "td:hover", "props": [("background-color", "#ffffb3")]}


def challenge_condition(value):
    if value < 2:
        return "Easy"
    if value <= 4:
        return "Medium"
    return "Hard"


def style_negative(value, color="red"):
    return f"color: {color}" if value > 3 else None


def format_table(styler: Styler):
    # styler.set_caption("Conditions")
    styler.format(challenge_condition, subset="Challenge Rating Explained")
    if hasattr(styler, "map"):
        styler = styler.map(style_negative, color="blue", subset="Challenge Rating Formatted")
    else:
        styler = styler.applymap(style_negative, color="blue", subset="Challenge Rating Formatted")
    # styler.background_gradient(axis=None, vmin=1, vmax=5, cmap="YlGnBu")
    return styler


styler = style_df.style.pipe(format_table)
styler.set_table_styles([cell_hover])

html_file_name = "dummy_styled_table.html"
styler.to_html(buf=html_file_name)

register_asset(html_file_name, {"label": "PANDAS", "foo": "styled"}, template="datatable")


def get_random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


for i in range(1, 4):
    with metadata_context(conditions={"foo": i}, label="PANDAS"):
        style_df = pd.DataFrame(
            {
                "Encounter": ("Zombie Soldier", "Imp", "Cacodemon", "Hell Knight", "Cyberdemon"),
                "Challenge Rating": (1 * i, 4 * i, 8 * i, 12 * i, None),
            }
        )
        style_df.to_html("dummy_table.html")


with metadata_context(label="PANDAS", huge=True):
    rows = 50
    style_df = pd.DataFrame(
        {
            "blabla": [get_random_string(5) for _ in range(rows)],
            "ints": np.random.randint(0, 100, rows),
            "float": np.random.random(rows) * 100,
            "hex": map(hex, np.random.randint(0, 100, rows)),
            **{f"col{k}": np.random.random(rows) for k in range(30)},
        }
    )

    style_df.to_html(buf="big_dummy_table.html")

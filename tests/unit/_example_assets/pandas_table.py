import pandas as pd

df = pd.DataFrame(
    {
        "Encounter": ("Zombie Soldier", "Imp", "Cacodemon", "Hell Knight", "Cyberdemon"),
        "Challenge Rating": (1, 4, 8, 12, None),
    }
)
df.to_html(buf="challenge_rating.html")

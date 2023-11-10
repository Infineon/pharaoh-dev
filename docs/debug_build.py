import os
from pathlib import Path

from sphinx.cmd.build import main

if __name__ == "__main__":
    os.chdir(Path(__file__).parents[1])
    main("-E -W -b html docs dist/docs".split(" "))

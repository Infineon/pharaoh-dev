from __future__ import annotations

import shlex

from tox.run import main

if __name__ == "__main__":
    main(shlex.split("config"))

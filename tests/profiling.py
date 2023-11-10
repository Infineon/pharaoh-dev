"""
Execute this script either via cProfile or profiling feature of PyCharm Pro.

The resulting .pstat file can be opened using snakeviz:
    pip install snakeviz
    snakeviz  "C:/Users\<user>\AppData\Local\JetBrains\PyCharm2023.1\snapshots\pharaoh.pstat"
"""

from pathlib import Path

import pytest

if __name__ == "__main__":
    Path("results/tmp_profiling").mkdir(parents=True, exist_ok=True)

    retcode = pytest.main(["unit", "--basetemp=results/tmp_profiling"])

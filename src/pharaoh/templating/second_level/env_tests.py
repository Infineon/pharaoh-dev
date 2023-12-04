from __future__ import annotations

from typing import Callable

env_tests: dict[str, Callable] = {}


# Only document the functions defined in here
to_document = {k: func for k, func in env_tests.items() if hasattr(func, "__module__") and func.__module__ == __name__}

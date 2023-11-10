from __future__ import annotations

import pluggy

NAME = "pharaoh"  # the name of the pharaoh pluggy hook

impl = pluggy.HookimplMarker(NAME)  # decorator to mark pharaoh plugin hooks

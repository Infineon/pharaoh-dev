from __future__ import annotations


class PharaohError(Exception):
    pass


class ProjectInconsistentError(PharaohError):
    pass


class AssetGenerationError(PharaohError):
    pass

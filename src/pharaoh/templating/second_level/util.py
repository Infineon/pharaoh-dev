from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pharaoh.assetlib.finder import Asset
    from pharaoh.project import PharaohProject
    from pharaoh.sphinx_app import PharaohSphinx


def asset_rel_path_from_build(sphinx_app: PharaohSphinx, template_file: Path, asset: Asset):
    asset.copy_to(sphinx_app.assets_dir)
    return (
        Path(os.path.relpath(sphinx_app.confdir, os.path.dirname(template_file)))
        / sphinx_app.assets_dir.name
        / asset.assetfile.name
    ).as_posix()


def asset_rel_path_from_project(project: PharaohProject, asset: Asset):
    return "/" + asset.assetfile.relative_to(project.asset_build_dir.parent).as_posix()

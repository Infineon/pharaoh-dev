from __future__ import annotations

import typing as t
from pathlib import Path

from sphinx.application import Sphinx

if t.TYPE_CHECKING:  # We get circular imports otherwise
    from pharaoh.project import PharaohProject
    from pharaoh.templating.second_level.template_env import PharaohTemplateEnv


class PharaohSphinx(Sphinx):
    pharaoh_proj: PharaohProject
    """
    Set by entrypoint of Sphinx plugin ...asset_ext.setup()
    """

    pharaoh_te: PharaohTemplateEnv
    """
    Set by entrypoint of Sphinx plugin ...jinja_ext.setup()
    """

    seen_warnings: t.ClassVar = set()
    """
    Set of warnings that have been seen already. Used to avoid duplicate warnings.
    Added by PharaohAssetDirective.
    """

    @property
    def assets_dir(self):
        return Path(self.builder.outdir) / "pharaoh_assets"

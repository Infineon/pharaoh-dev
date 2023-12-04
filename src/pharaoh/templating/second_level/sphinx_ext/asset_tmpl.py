from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pharaoh.templating.second_level.template_env import PharaohTemplateEnv


def find_asset_template(template_name: str) -> Path:
    from pharaoh.plugins.plugin_manager import PM

    files = PM.pharaoh_find_asset_render_template(template_name)
    if not files:
        msg = f"Cannot find template that matches {template_name!r}!"
        raise LookupError(msg)
    if len(files) > 1:
        files_listed = "\n  ".join(map(str, files))
        msg = f"Found multiple matches for {template_name!r}:\n  {files_listed}\nPlease use a more specific name!"
        raise LookupError(msg)
    return files[0]


def render_asset_template(jinja_env: PharaohTemplateEnv, template: str, **kwargs) -> str:
    template_file = Path(template).absolute() if Path(template).absolute().exists() else find_asset_template(template)
    template_content = "\n" + template_file.read_text(encoding="utf-8").strip() + "\n"

    tmpl = jinja_env.from_string(template_content)
    return tmpl.render(**kwargs)

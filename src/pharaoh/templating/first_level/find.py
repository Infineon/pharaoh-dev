from __future__ import annotations

from pathlib import Path


def find_template(template: str) -> Path:
    from pharaoh.plugins.plugin_manager import PM

    templates = PM.pharaoh_collect_l1_templates()
    if isinstance(template, str):
        if template in templates:
            return Path(templates[template].path).absolute()
        ptemplate = Path(template)
        if ptemplate.exists() and str(ptemplate) not in ("", "."):
            return Path(template)

        msg = f"Not a valid template {template!r}! Available templates: {', '.join(templates)}."
        raise ValueError(msg)

    msg = f"Not a valid template {template!r}! Available templates: {', '.join(templates)}."
    raise ValueError(msg)

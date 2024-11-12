from __future__ import annotations

from pathlib import Path

from pharaoh.plugins.api import L1Template, impl

DEFAULT_ASSET_TEMPLATE_MAPPING = {
    ".html": "iframe",  # todo: use raw_html if this is not a full HTML file, iframe otherwise
    ".rst": "raw_rst",
    ".txt": "raw_txt",
    ".svg": "image",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".md": "markdown",
}


@impl
def pharaoh_collect_l1_templates():
    return [
        L1Template(
            name="pharaoh.default_project",
            path=Path(__file__).parent / "level_1" / "pharaoh_sphinx_project",
        ),
        L1Template(
            name="pharaoh.empty",
            path=Path(__file__).parent / "level_1" / "empty",
        ),
        L1Template(
            name="pharaoh.report_info",
            path=Path(__file__).parent / "level_1" / "report_info",
        ),
    ]


@impl
def pharaoh_collect_resource_types():
    from pharaoh.assetlib.resource import CustomResource, FileResource

    return [FileResource, CustomResource]


@impl(tryfirst=True)
def pharaoh_collect_default_settings():
    return Path(__file__).with_name("default_settings.yaml")


@impl(tryfirst=True)
def pharaoh_find_asset_render_template(template_name: str) -> Path:
    template_dir = Path(__file__).with_name("asset_templates")
    assert template_dir.exists()
    template = template_dir / f"{template_name}.rst.jinja2"
    if not template.exists():
        msg = f"Cannot find template {template_name!r} in {template_dir}!"
        raise LookupError(msg)
    return template


@impl(tryfirst=True)
def pharaoh_get_asset_render_template_mappings():
    return DEFAULT_ASSET_TEMPLATE_MAPPING

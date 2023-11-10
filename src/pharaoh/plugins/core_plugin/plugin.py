from pathlib import Path

from pharaoh.plugins.api import L1Template, impl


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
    ]


@impl
def pharaoh_collect_resource_types():
    from pharaoh.assetlib.resource import CustomResource, FileResource

    return [FileResource, CustomResource]


@impl(tryfirst=True)
def pharaoh_collect_default_settings():
    return Path(__file__).with_name("default_settings.yaml")

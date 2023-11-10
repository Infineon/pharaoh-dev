from pathlib import Path

from pharaoh.plugins.api import L1Template, impl


def abs(name):
    return Path(__file__).parent / name


first_level_template_dir = Path(__file__).parent / "level_1"
l1_template_names = [file.name for file in first_level_template_dir.glob("*")]


@impl
def pharaoh_collect_l1_templates():
    return [
        L1Template(
            name=f"pharaoh_testing.{name}",
            path=first_level_template_dir / name,
            needs=[],
            vars=[],
        )
        for name in l1_template_names
    ]

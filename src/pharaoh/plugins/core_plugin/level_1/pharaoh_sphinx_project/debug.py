from __future__ import annotations

from pharaoh.api import get_project

if __name__ == "__main__":
    proj = get_project("..")
    proj.generate_assets()
    proj.build_report()

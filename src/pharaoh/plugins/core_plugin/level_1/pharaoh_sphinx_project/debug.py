from __future__ import annotations

from pharaoh.api import PharaohProject

if __name__ == "__main__":
    proj = PharaohProject(project_root="..")
    proj.generate_assets()
    proj.build_report()

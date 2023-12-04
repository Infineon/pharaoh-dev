from __future__ import annotations


def test_pdf_builder(new_proj):
    new_proj._project_settings.asset_gen.force_static = True
    new_proj._project_settings.report.title = "Pharaoh PDF Report"
    new_proj._project_settings.report.builder = "latex"
    new_proj.add_component("report", "pharaoh_testing.complex")

    new_proj.generate_assets()
    status = new_proj.build_report()
    assert status == 0

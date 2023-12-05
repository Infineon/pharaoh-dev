from __future__ import annotations

import ast
import json
import tempfile
import typing as t
from pathlib import Path

from .find import find_template
from .scaffolder import Scaffolder


def render_template(template_path: Path, outputdir: Path, context: dict | None = None) -> Path:
    if template_path.is_dir():
        return render_template_directory(template_path, outputdir, context)
    if template_path.is_file():
        return render_template_file(template_path, outputdir, context)
    raise NotImplementedError


def render_template_directory(template_path: Path, outputdir: Path, context: dict | None = None) -> Path:
    outputdir.mkdir(parents=True, exist_ok=True)
    assert template_path.is_dir(), f"{template_path} is not a directory!"

    Scaffolder(source_dir=template_path, target_dir=outputdir, render_context=context).run()

    if isinstance(context, dict):
        context_dump_file = outputdir / ".template_context.json"
        context_dump_file.write_text(json.dumps(context, indent=2))
    return outputdir


def render_template_file(template_path: Path, outputdir: Path, context: dict | None = None) -> Path:
    if [suffix.lower() for suffix in template_path.suffixes] != [".pharaoh", ".py"]:
        msg = "If template_path is a file, only files with .pharaoh.py suffix are supported!"
        raise ValueError(msg)

    with tempfile.TemporaryDirectory(prefix="pharaoh_") as tdir:
        tempdir = Path(tdir)
        template_content = template_path.read_text(encoding="utf-8")
        tree = ast.parse(template_content)
        module_docstring = (ast.get_docstring(tree) or "").strip()

        stem = ".".join(template_path.name.split(".")[:-2])
        asset_scripts = tempdir / "asset_scripts"
        asset_scripts.mkdir()
        (asset_scripts / f"{stem}.py").write_text(template_content, encoding="utf-8")
        if module_docstring:
            (tempdir / f"index_{stem}.rst").write_text(module_docstring, encoding="utf-8")

        return render_template_directory(tempdir, outputdir, context)


def render_sphinx_base_project(outputdir: Path, templates: t.Iterable[str], context: dict | None = None):
    for templ in templates:
        render_template_directory(
            template_path=find_template(templ),
            outputdir=outputdir,
            context=context,
        )

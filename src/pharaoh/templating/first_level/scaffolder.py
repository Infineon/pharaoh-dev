from __future__ import annotations

from pathlib import Path

from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader


class Scaffolder:
    def __init__(self, source_dir: Path, target_dir: Path, render_context: dict | None = None):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.render_context = render_context or {}
        self.template_suffix = ".jinja2"

        self.env = Environment(
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            block_end_string="%]",
            block_start_string="[%",
            comment_end_string="#]",
            comment_start_string="[#",
            variable_end_string="]]",
            variable_start_string="[[",
            loader=FileSystemLoader(self.source_dir),
        )

    def run(self):
        self._render_folder(self.source_dir)

    def _render_folder(self, src_abspath: Path) -> None:
        """Recursively render a folder.

        Args:
            src_path:
                Folder to be rendered. It must be an absolute path within
                the template.
        """
        assert src_abspath.is_absolute()
        src_relpath = src_abspath.relative_to(self.source_dir)
        dst_relpath = self._render_path(src_relpath)
        if dst_relpath is None:
            return
        if not self._render_allowed(dst_relpath, is_dir=True):
            return
        dst_abspath = Path(self.target_dir, dst_relpath)
        dst_abspath.mkdir(parents=True, exist_ok=True)
        for file in src_abspath.iterdir():
            if file.is_dir():
                self._render_folder(file)
            else:
                self._render_file(file)

    def _render_path(self, relpath: Path) -> Path | None:
        """Render one relative path.

        Args:
            relpath:
                The relative path to be rendered. Obviously, it can be templated.
        """
        is_template = relpath.name.endswith(self.template_suffix)
        # If there is a sibling file in the same dir that is templated, skip the current file
        templated_sibling = self.source_dir / f"{relpath}{self.template_suffix}"
        # With an empty suffix, the templated sibling always exists.
        if templated_sibling.exists():
            return None
        if self.template_suffix and is_template:
            relpath = relpath.with_suffix("")
        rendered_parts = []
        for part in relpath.parts:
            # Skip folder if any part is rendered as an empty string
            part = self._render_string(part)
            if not part:
                return None
            # restore part to be just the end leaf
            rendered_parts.append(part)
        result = Path(*rendered_parts)
        if not is_template:
            templated_sibling = self.source_dir / f"{result}{self.template_suffix}"
            if templated_sibling.exists():
                return None
        return result

    def _render_file(self, src_abspath: Path) -> None:
        """Render one file.

        Args:
            src_abspath:
                The absolute path to the file that will be rendered.
        """
        assert src_abspath.is_absolute()
        src_relpath = src_abspath.relative_to(self.source_dir).as_posix()
        src_renderpath = src_abspath.relative_to(self.source_dir)
        dst_relpath = self._render_path(src_renderpath)
        if dst_relpath is None:
            return
        if src_abspath.name.endswith(self.template_suffix):
            try:
                tpl = self.env.get_template(src_relpath)
            except UnicodeDecodeError:
                if self.template_suffix:
                    # suffix is not empty, re-raise
                    raise
                # suffix is empty, fallback to copy
                new_content = src_abspath.read_bytes()
            else:
                new_content = tpl.render(**self.render_context).encode()
        else:
            new_content = src_abspath.read_bytes()
        dst_abspath = Path(self.target_dir, dst_relpath)
        src_mode = src_abspath.stat().st_mode
        if not self._render_allowed(dst_relpath, expected_contents=new_content):
            return
        dst_abspath.parent.mkdir(parents=True, exist_ok=True)
        dst_abspath.write_bytes(new_content)
        dst_abspath.chmod(src_mode)

    def _render_string(self, string: str) -> str:
        """Render one templated string.

        Args:
            string:
                The template source string.
        """
        tpl = self.env.from_string(string)
        return tpl.render(**self.render_context)

    def _render_allowed(
        self,
        dst_relpath: Path,
        is_dir: bool = False,
        expected_contents: bytes | Path = b"",
    ) -> bool:
        """Determine if a file or directory can be rendered.

        Args:
            dst_relpath:
                Relative path to destination.
            is_dir:
                Indicate if the path must be treated as a directory or not.
            expected_contents:
                Used to compare existing file contents with them. Allows to know if
                rendering is needed.
        """
        assert not dst_relpath.is_absolute()
        assert not expected_contents or not is_dir, "Dirs cannot have expected content"
        dst_abspath = Path(self.target_dir, dst_relpath)
        if not is_dir and dst_abspath.exists():
            previous_content: bytes = dst_abspath.read_bytes()
            return previous_content != expected_contents
        if is_dir:
            return True
        return True

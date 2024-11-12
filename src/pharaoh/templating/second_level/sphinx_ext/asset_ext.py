from __future__ import annotations

import contextlib
import copy
import os
import re
import textwrap
import traceback
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives.images import Image
from docutils.statemachine import StateMachine
from sphinx.util import logging

import pharaoh
import pharaoh.project
from pharaoh.templating.second_level.util import asset_rel_path_from_build, asset_rel_path_from_project

from .asset_tmpl import render_asset_template

if TYPE_CHECKING:
    from pharaoh.sphinx_app import PharaohSphinx

logger = logging.getLogger("pharaoh_asset")


class PharaohDirectiveError(Exception):
    pass


def setup(app: PharaohSphinx):
    app.pharaoh_proj = pharaoh.project.PharaohProject(os.path.dirname(app.confdir))
    setup.app = app  # type: ignore[attr-defined]
    setup.config = app.config  # type: ignore[attr-defined]
    setup.confdir = app.confdir  # type: ignore[attr-defined]
    app.add_directive("pharaoh-asset", PharaohAssetDirective)
    app.add_directive("pharao-asset", PharaohAssetDirective)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": pharaoh.__version__,
    }


def get_app() -> PharaohSphinx:
    return setup.app  # type: ignore[attr-defined]


INFO_TEMPLATE = """
Executing pharaoh-asset directive:
    Source:
        File:    {source_file}:{line_no}
        Section: {section}

    Directive:
{block_text}
"""


ERROR_TEMPLATE = """
Error: {error}

Source:
    File:    {source_file}:{line_no}
    Section: {section}

Directive:
{block_text}

Traceback:
{traceback}
"""


# -------------------------------------
# Options
# -------------------------------------
def _option_boolean(arg):
    if not arg or not arg.strip():
        # no argument given, assume used as a flag
        return True
    if arg.strip().lower() in ("no", "0", "false"):
        return False
    if arg.strip().lower() in ("yes", "1", "true"):
        return True
    msg = f'"{arg}" unknown boolean'
    raise ValueError(msg)


# -------------------------------------
# Directive
# -------------------------------------
class PharaohAssetDirective(Directive):
    """The ``.. pharaoh-asset::`` directive."""

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec: ClassVar = {
        "optional": _option_boolean,
        "ignore-title": _option_boolean,
        "ignore-description": _option_boolean,
        "index": directives.unchanged,
        "filter": directives.unchanged,
        "image-alt": directives.unchanged,
        "image-height": directives.length_or_unitless,
        "image-width": directives.length_or_percentage_or_unitless,
        "image-scale": directives.nonnegative_int,
        "image-align": Image.align,
        "iframe-width": directives.unchanged,
        "iframe-height": directives.unchanged,
        "components": directives.unchanged,
        "datatable-extended-search": _option_boolean,
        # fixme: for now keep this undocumented until a better solution is found to supply multiple CSS rules for
        # the specific datatable that is rendered (CSS id selector)
        "datatable-style-override": directives.unchanged,
        "template": directives.unchanged,
    }

    def run(self) -> list:
        """Run the plot directive."""
        sphinx_app: PharaohSphinx = get_app()
        rst_file = self.state_machine.document.attributes["source"]
        section = self.state_machine.node.shortrepr()
        # The line number actually refers to the rendered file coming out of 2nd-lvl templating,
        source_file = Path(rst_file + ".rendered").relative_to(sphinx_app.confdir)
        # Find lineno in source file. Here we have to iteratively search the parent items for the first
        # occurrence of a source file/line tuple. Let's hope this implementation detail does not change on
        # Sphinx side, otherwise this code might break :)
        try:
            parent = self.content
            items = parent.items
            while not len(items):
                parent = parent.parent
                items = parent.items
            line_no = items[0][1]
        except Exception:
            line_no = "?"

        msg = INFO_TEMPLATE.format(
            source_file=source_file,
            line_no=line_no,
            section=section,
            block_text=textwrap.indent(self.block_text.strip(), " " * 8),
        )
        logger.verbose(msg)

        try:
            return self._run(source_file, line_no)
        except Exception as e:
            # If there's any error, render a nice error description into the report.
            # It will contain the source file + line number as well as the error message and traceback
            # in a nice collapsible card.
            msg = ERROR_TEMPLATE.format(
                error=repr(e),
                source_file=source_file,
                line_no=line_no,
                section=section,
                block_text=textwrap.indent(self.block_text.strip(), " " * 4),
                traceback=textwrap.indent(traceback.format_exc(limit=3).strip(), " " * 4),
            )
            logger.warning(textwrap.indent(msg, " " * 4))

            assert sphinx_app.pharaoh_te is not None
            error = render_asset_template(
                jinja_env=sphinx_app.pharaoh_te,
                template="error",
                error=repr(e),
                content=msg,
            )
            StateMachine.insert_input(self.state_machine, error.splitlines(keepends=False), source=rst_file)
            # Let the Sphinx build fail (if warnings are errors, which is the default) and show a warning
            self.state_machine.reporter.warning(
                f"{e} (see report for traceback or logs above)", source=source_file, line=line_no
            )
            return []

    def _run(self, source_file: Path, line_no: str) -> list:
        arguments = self.arguments
        content = self.content
        state_machine = self.state_machine
        template_file = state_machine.document.attributes["source"]
        options = self.options
        options = {k.replace("-", "_"): v for k, v in options.items()}

        sphinx_app: PharaohSphinx = setup.app  # type: ignore
        assert sphinx_app.pharaoh_proj is not None
        pharaoh_proj: pharaoh.project.PharaohProject = sphinx_app.pharaoh_proj
        asset_finder = pharaoh_proj.asset_finder

        asset_optional = options.pop("optional", False)
        # Per default, only find assets from the same component as the invoking RST file using the special value _this_
        option_components = options.get("components", "_this_").lower().strip()

        # Find the component name of the currently handled RST file
        try:
            current_component = Path(template_file).relative_to(pharaoh_proj.sphinx_report_project_components).parts[0]
        except Exception:
            current_component = None

        component_selection = set()
        if option_components != "_all_":
            for comp in map(str.strip, option_components.split(",")):
                if comp != "_this_":
                    component_selection.add(comp)
                elif current_component is not None:
                    component_selection.add(current_component)

        # Discover assets by filter
        assets = []
        filter_string = (
            split_filter(" ".join(content))
            + split_filter(options.get("filter", ""))
            + split_filter(" ".join(arguments))
        )
        filter_string = list(set(filter_string))
        if len(filter_string) == 1 and filter_string[0].strip().startswith("__ID__"):
            asset = asset_finder.get_asset_by_id(filter_string[0].strip())
            if asset is not None:
                assets.append(asset)
        else:
            for line in filter_string:
                line = line.strip()
                if line:
                    assets.extend(asset_finder.search_assets(line, list(component_selection)))
        assets = list(set(assets))  # Filter potential duplicates added by multiple "overlapping" asset filters
        if not len(assets) and not asset_optional:
            msg = "No assets matched!\n"
            raise Exception(msg)

        # Parse index. Following style is possible: 1,2,4-8,9. Whitespace is ignored.
        index = str(options.pop("index", "")).replace(" ", "")
        indices: list[int] = []
        if index:
            for part in index.split(","):
                if "-" in part:
                    start, stop = part.split("-")
                    indices.extend(range(int(start), int(stop)))
                else:
                    indices.append(int(part))

        lines_to_insert = []
        for iasset, asset in enumerate(assets):
            if len(indices) and iasset not in indices:
                continue
            # Template option priorities:
            #  1. Directive options
            #  2. Asset template options
            #  3. Project defaults

            # 1. Directive options
            template_opts = copy.deepcopy(options)
            # 2. Asset template options
            asset_options = asset.context.get("asset", {})
            for k, v in asset_options.items():
                template_opts.setdefault(k, v)
            #  3. Project defaults
            template_opts.setdefault("iframe_width", pharaoh_proj.get_setting("asset_gen.default_iframe_width"))
            template_opts.setdefault("iframe_height", pharaoh_proj.get_setting("asset_gen.default_iframe_height"))
            template_opts.setdefault(
                "datatable_extended_search", pharaoh_proj.get_setting("asset_gen.default_datatable_extended_search")
            )

            if "template" not in template_opts:
                msg = f"No template selected for asset {asset}!"
                raise PharaohDirectiveError(msg)
            template = template_opts["template"].strip().lower()

            image_opts = {key.replace("image_", ""): val for key, val in options.items() if key.startswith("image_")}

            logger.verbose(f"Rendering {asset} with template {template!r}")

            # Let generated error assets using the "catch_exceptions" function also issue a Sphinx warning
            # to fail report generation.
            if asset.context.get("asset_type", "") == "error_traceback":
                msg = (
                    f"An error occurred during asset generation: {asset.context.get('error_message', '')}. "
                    f"Please search the log for the error message including traceback!"
                )
                if msg not in sphinx_app.seen_warnings:
                    sphinx_app.seen_warnings.add(msg)
                    self.state_machine.reporter.warning(msg)

            assert sphinx_app.pharaoh_te is not None
            content = render_asset_template(
                jinja_env=sphinx_app.pharaoh_te,
                template=template,
                opts=template_opts,
                image_opts=image_opts,
                asset=asset,
                asset_rel_path_from_project=partial(asset_rel_path_from_project, pharaoh_proj),
                asset_rel_path_from_build=partial(asset_rel_path_from_build, sphinx_app, Path(template_file)),
            )

            result = render_asset_template(
                jinja_env=sphinx_app.pharaoh_te,
                template="include_wrapper",
                asset=asset,
                content=content,
                opts=template_opts,
            )

            lines_to_insert.extend(result.split("\n"))
        if lines_to_insert:
            # Sphinx 7.2: #10678: Emit “source-read” events for files read via the include directive.
            # This fix actually removed to need for pre-rendering included files, because a Sphinx source-read event
            # is sent once a file is included via the Include directive and then automatically rendered like all other
            # source files.
            # But in our case it may lead to an infinite recursion. Here's what is think happens:
            # The Include directive monkey patches StateMachine.insert_input to trigger source-read events whenever
            # a file is included.
            # If the included code contains a Pharaoh directive that uses StateMachine.insert_input to add content,
            # it triggers again a source-read event on the same file, leading to an infinity loop.
            # We can come out of this loop by using the original parent implementation ``StateMachine.insert_input``
            # instead of the monkey-patched one.
            StateMachine.insert_input(state_machine, lines_to_insert, source=template_file)

        return []


def split_filter(string: str) -> list[str]:
    # First split by all ; that are not escaped with \
    split_by_semicolon = [substring.strip() for substring in re.split(r"(?<!\\);", string)]

    # Join linebreaks with space
    filter = [" ".join(map(str.strip, part.splitlines())) for part in split_by_semicolon]
    with contextlib.suppress(ValueError):
        filter.remove("")
    return filter

from __future__ import annotations

import functools
import os
import pprint
import shutil
import uuid
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Callable

import jinja2
import jinja2.utils
import omegaconf
from jinja2_git import GitExtension

from pharaoh.log import log
from pharaoh.util.contextlib_chdir import chdir

from .env_filters import env_filters
from .env_globals import env_globals
from .env_tests import env_tests
from .util import asset_rel_path_from_build, asset_rel_path_from_project

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sphinx.config import Config

    import pharaoh.project
    from pharaoh.sphinx_app import PharaohSphinx


class PharaohFileSystemLoader(jinja2.loaders.FileSystemLoader):
    def get_source(self, environment: jinja2.Environment, template: str) -> tuple[str, str, Callable[[], bool]]:
        # Overwrite to support absolute filenames as well as relative ones that have to be looked up in the search paths
        for searchpath in self.searchpath:
            if "<>" in template:  # See PharaohTemplateEnv.join_path
                parent, template_ = template.rsplit("<>", 1)
                template_path = Path(parent) / template_
                if template_path.is_absolute() and template_path.exists():
                    filename = template_path.as_posix()
                else:
                    pieces = jinja2.loaders.split_template_path(template_)
                    filename = jinja2.loaders.posixpath.join(searchpath, *pieces)
            else:
                pieces = jinja2.loaders.split_template_path(template)
                filename = jinja2.loaders.posixpath.join(searchpath, *pieces)

            # Original code starts from here

            if not os.path.isfile(filename):
                continue
            with open(filename, "rb") as f:
                contents = f.read().decode(self.encoding)

            def up_to_date() -> bool:
                return False

            # Use normpath to convert Windows altsep to sep.
            return contents, os.path.normpath(filename), up_to_date
        raise jinja2.TemplateNotFound(template)


class PharaohTemplate(jinja2.Template):
    def render(self, *args, **kwargs) -> str:
        return super().render(*args, **kwargs)


class PharaohTemplateEnv(jinja2.Environment):
    template_class = PharaohTemplate

    def __init__(self):
        super().__init__(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            extensions=["jinja2_ansible_filters.AnsibleCoreFiltersExtension"],
        )
        self.default_context: dict = {
            "project": {},  # Project related context
            "local": {},  # Discovered content of context files next to the source file
            "assets": {},  # Discovered content of asset files registered via register_templating_context function
            "config": None,  # Content of conf.py (Sphinx Config object)
            "user": None,  # Content of user given dict "pharaoh_jinja_context" in conf.py
        }
        self.local_context_file_cache: dict[Path, ModuleType] = {}

        self.sphinx_app: PharaohSphinx | None = None
        self.globals.update(env_globals)
        self.filters.update(env_filters)
        self.tests.update(env_tests)

        # todo: remove or enable if needed. Unused right now
        # from jinjatag.extension import JinjaTag
        # jinja_tag = JinjaTag()
        # self.add_extension(jinja_tag)
        # jinja_tag.init()

        self.add_extension(GitExtension)

    def sphinx_config_inited_hook(self, app: PharaohSphinx, config: Config):
        """
        Called by Sphinx core event "config-inited". Emitted when the config object has been initialized.
        https://www.sphinx-doc.org/en/master/extdev/appapi.html#event-config-inited
        """
        from pharaoh.plugins.plugin_manager import PM

        self.sphinx_app = app
        pharaoh_proj = app.pharaoh_proj

        # Configure globals/filters from Pharaoh app
        pharaoh_proj._update_template_env(self)

        # Configure users globals/filters/tests from conf.py
        user_filters = self.sphinx_app.config.pharaoh_jinja_filters or {}
        for k, v in user_filters.items():
            if k in self.filters:
                msg = f"A Jinja filter named {k!r} already exists: {self.filters[k]}"
                raise NameError(msg)
            self.filters[k] = v

        user_globals = self.sphinx_app.config.pharaoh_jinja_globals or {}
        for k, v in user_globals.items():
            if k in self.globals:
                msg = f"A Jinja global named {k!r} already exists: {self.globals[k]}"
                raise NameError(msg)
            self.globals[k] = v

        user_tests = self.sphinx_app.config.pharaoh_jinja_tests or {}
        for k, v in user_tests.items():
            if k in self.tests:
                msg = f"A Jinja test named {k!r} already exists: {self.tests[k]}"
                raise NameError(msg)
            self.tests[k] = v

        template_paths = PM.pharaoh_collect_l2_templates()
        # dynamically discovered
        for path in config.pharaoh_jinja_templates or []:
            # Extend user-configured template paths
            path = Path(path)
            if not path.is_absolute():
                if str(path) not in self.sphinx_app.config.exclude_patterns:
                    # Extend exclude patterns by user's local template directory, so Sphinx does not warn about files
                    # that are not included in any toctree.
                    self.sphinx_app.config.exclude_patterns.append(str(path))
                p = Path(self.sphinx_app.confdir) / path
                if not p.exists() and not p.is_dir():
                    msg = f"Directory {p} does not exists or is no directory!"
                    raise FileNotFoundError(msg)
                template_paths.append(p)
            else:
                template_paths.append(path.resolve())

        self.loader = PharaohFileSystemLoader(template_paths)

        components = []
        for comp in pharaoh_proj._project_settings.get("components", []) or []:
            rst_entrypoint = pharaoh_proj.sphinx_report_project_components / comp["name"] / "index.rst"
            if rst_entrypoint.exists():
                components.append(rst_entrypoint.relative_to(pharaoh_proj.sphinx_report_project).as_posix())
        self.default_context["project"]["instance"] = pharaoh_proj
        self.default_context["config"] = app.config or {}
        self.default_context["user"] = app.config.pharaoh_jinja_context or {}

    def sphinx_builder_inited_hook(self, app: PharaohSphinx):
        """
        Called by Sphinx core event "builder-inited". Emitted when the builder object has been created.
        https://www.sphinx-doc.org/en/master/extdev/appapi.html#event-builder-inited
        """
        finder = app.pharaoh_proj.asset_finder

        # Copy shared resources
        assets_to_copy = finder.search_assets("asset.copy2build")
        build_assetdir = app.assets_dir
        if build_assetdir.exists():
            shutil.rmtree(build_assetdir, ignore_errors=False)

        for asset in assets_to_copy:
            log.debug(f"Copying asset {asset} to build directory")
            asset.copy_to(build_assetdir)

    def sphinx_source_read_hook(self, app: PharaohSphinx, docname: str, source: list):
        """
        Emitted when a source file has been read. The source argument is a list whose single element is the contents
        of the source file.
        You can process the contents and replace this item to implement source-level transformations.

        :param app: The Sphinx app
        :param docname: The document name as string
        :param source: A list with a single item, the string content of 'docname'.
                       May be modified in place to change the source Sphinx will use.
                       Here it is used send the file content through Jinja rendering before Sphinx gets it.
        """
        rendered, _ = self.render_file(docname)
        source[0] = rendered  # source item 0 must be modified in place

    def sphinx_include_read_hook(self, app: PharaohSphinx, relative_path, parent_docname, content):
        file = Path(self.sphinx_app.srcdir) / relative_path
        rendered, _ = self.render_file(file)
        content[0] = rendered

    def render_file(self, docname: Path | str) -> tuple[str, Path]:
        project: pharaoh.project.PharaohProject = self.sphinx_app.pharaoh_proj

        if isinstance(docname, str):
            template_file = Path(self.sphinx_app.env.doc2path(docname))
        elif isinstance(docname, Path):
            template_file = docname
        else:
            msg = f"Unsupported type ({type(docname)!r}) for argument 'docname'!"
            raise TypeError(msg)

        try:
            # Find component name by parent directory
            components_dir = project.sphinx_report_project_components
            try:
                parts = template_file.relative_to(components_dir).parts
                component_name = "" if len(parts) < 2 else parts[0]
            except ValueError:
                component_name = ""

            # Context Creation
            log.debug(f"Discovering additional templating context for component {component_name!r}...")
            self.default_context["project"]["component_name"] = component_name
            self.default_context["local"] = {}

            for key, ctx in self.read_local_context_files(self.default_context, template_file.parent).items():
                log.debug(f"... discovered local context {key!r}")
                if key in self.default_context["local"]:
                    log.warning(f"Overwriting existing local context namespace {key!r}!")
                self.default_context["local"][key] = ctx

            for key, ctx in self.read_asset_context_files(component=component_name):
                log.debug(f"... discovered asset context {key!r}")
                if key in self.default_context["local"]:
                    log.warning(f"Overwriting existing local context namespace {key!r}!")
                self.default_context["local"][key] = ctx

            with chdir(template_file.parent):
                template = self.select_template([template_file.name], parent=str(template_file.parent))
                rendered = template.render(
                    {"ctx": self.default_context}, **self.get_render_globals(project, component_name, template_file)
                )

            rendered_file = template_file.parent / (template_file.name + ".rendered")
            rendered_file.write_text(rendered)
            return rendered, rendered_file
        except Exception:
            log.error(
                f"Error in PharaohTemplateEnv.sphinx_source_read_hook while trying to render template "
                f"{template_file} with context {pprint.pformat(self.default_context)}!",
                exc_info=True,
            )
            raise
        finally:
            self.default_context["local"] = {}

    def get_render_globals(
        self, project: pharaoh.project.PharaohProject, component_name: str, template_file: Path
    ) -> dict[str, Callable]:
        return {
            "search_error_assets": functools.partial(
                project.asset_finder.search_assets,
                components=[component_name],
                condition="asset_type == 'error_traceback'",
            ),
            "search_assets": functools.partial(project.asset_finder.search_assets, components=[component_name]),
            "asset_rel_path_from_project": partial(asset_rel_path_from_project, project),
            "asset_rel_path_from_build": partial(asset_rel_path_from_build, self.sphinx_app, template_file),
        }

    def join_path(self, template: str, parent: str) -> str:
        """
        Join a template with the parent. By default, all the lookups are
        relative to the loader root so this method returns the `template`
        parameter unchanged, but if the paths should be relative to the
        parent template, this function can be used to calculate the real
        template name.

        Subclasses may override this method and implement template path
        joining here.
        """
        if "<>" in parent:
            # This case happens only when pharaoh is deployed at site-packages (don't know why, no time to find out).
            # In this case under Python 3.7, the following parent.is_dir() is failing because os.stat
            # does not allow <> in the file path, Python 3.9 does, apparently.
            # So we split off the suffix after <> (which would be done anyway using the "parent.parent" statement).
            parent = parent.split("<>")[0]
        parent_path = Path(parent)
        if not parent_path.is_dir():
            parent_path = parent_path.parent
        # Use a special illegal string <> to be able to split the template from the parent in
        # PharaohFileSystemLoader.get_source
        return parent_path.as_posix() + "<>" + Path(template).as_posix()

    def read_local_context_files(self, base_context: dict, basepath: Path) -> dict:
        """
        Reads all *_context.yaml and executes all *_context.py files to collect additional context data for templating.
        """
        local_context: dict = {}
        for file in basepath.glob("*_context.yaml"):
            f = Path(file)
            key = f.name.rsplit("_", 1)[0]
            with f.open():
                conf = omegaconf.OmegaConf.load(f)
                omegaconf.OmegaConf.resolve(conf)
                local_context[key] = conf

        for file in basepath.glob("*_context.py"):
            f = Path(file)
            key = f.name.rsplit("_", 1)[0]
            if f in self.local_context_file_cache:
                module = self.local_context_file_cache[f]
            else:
                module = module_from_file(f)
                run_module(module, f.read_text(encoding="utf-8"))
                self.local_context_file_cache[f] = module
            result_ctx: dict = module.__dict__
            if not ("context" in result_ctx and isinstance(result_ctx["context"], dict)):
                msg = (
                    "No dict-typed variable named 'context' was defined by the script!\n"
                    "Example of valid script content: context={}"
                )
                raise LookupError(msg)
            if key in local_context:
                log.warning(f"Local context key {key!r} already exists and will be overwritten by {file}")
            local_context[key] = result_ctx["context"]

        return local_context

    def read_asset_context_files(self, component: str) -> Iterator[tuple[str, list | dict]]:
        proj = self.sphinx_app.pharaoh_proj
        for asset in proj.asset_finder.search_assets(
            components=[component], condition="pharaoh_templating_context != ''"
        ):
            suffix = asset.assetfile.suffix.lower()
            if suffix == ".json":
                context = asset.read_json()
            elif suffix == ".yaml":
                context = asset.read_yaml()
            else:
                msg = f"Unsupported file suffix {suffix!r}"
                raise NotImplementedError(msg)
            yield asset.context.pharaoh_templating_context, context


def module_from_file(path: str | Path) -> ModuleType:
    """
    Creates a module from file at runtime.

    :param path: Path to the module source code.
    :return: A fresh module
    """

    module_path = Path(path)
    module_name = f"local_context_{module_path.stem.replace(' ', '_').replace('-', '_')}_{uuid.uuid4().hex[:6]}"
    module = ModuleType(module_name)
    module.__dict__["__file__"] = str(module_path.absolute())
    module.__path__ = [str(module_path.parent)]
    module.__dict__["__name__"] = "__main__"
    module.__dict__["__module_name__"] = module_name

    return module


def run_module(module: ModuleType, code: str):
    """
    Execute the configured source code in a module.

    :param module: A module object.
    :param code: The code to be run inside the module
    """
    compiled_code = compile(code, module.__dict__["__file__"], "exec")

    target_wd = Path(module.__dict__["__file__"]).parent
    with chdir(target_wd):
        exec(compiled_code, module.__dict__)

from __future__ import annotations

import datetime
import functools
import logging
import os
import re
import shutil
import sys
import traceback
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import attr
import attrs
import omegaconf
import omegaconf.errors

import pharaoh
import pharaoh.log
import pharaoh.util.oc_resolvers
from pharaoh.assetlib import finder, resource
from pharaoh.assetlib.context import context_stack
from pharaoh.errors import AssetGenerationError, ProjectInconsistentError
from pharaoh.plugins.plugin_manager import PM
from pharaoh.util.contextlib_chdir import chdir

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    import jinja2

try:
    PHARAOH_CLI_PATH = Path(shutil.which("pharaoh.exe")).as_posix()  # type: ignore[arg-type]
except TypeError:
    PHARAOH_CLI_PATH = "pharaoh.exe"

PathLike = Union[str, Path]

LRU_PHARAOH_PROJECT: PharaohProject | None = None

DEFAULT_MISSING = object()

log = pharaoh.log.log


def get_project(lookup_path: str | Path | None = None) -> PharaohProject:
    """
    Returns an instance of PharaohProject.

    :param lookup_path: If None, the function tries to return the Pharaoh singleton instance that is already loaded in
                        memory and raises and exception if there is none.
                        If given a string or Path instance, searches the given path and all its parent folders
                        for a ``pharaoh.yaml`` project file and returns a PharaohProject instance.
    """
    if lookup_path is None:
        # Enforce having a singleton per process
        if LRU_PHARAOH_PROJECT is None:
            msg = "No PharaohProject instance created yet!"
            raise RuntimeError(msg)
        return LRU_PHARAOH_PROJECT

    if isinstance(lookup_path, (str, Path)):
        lookup_path = Path(lookup_path)
        if lookup_path.is_file():
            lookup_path = lookup_path.parent
    else:
        msg = "Unsupported value for argument 'lookup_path'."
        raise ValueError(msg)

    path = Path(lookup_path).absolute()
    if path.is_file():
        path = path.parent
    while True:
        if (path / PharaohProject.PROJECT_SETTINGS_YAML).exists():
            return PharaohProject(project_root=path)

        if path == path.parent:
            # We reached the path's anchor level
            msg = (
                f"Cannot find a Pharaoh project file {PharaohProject.PROJECT_SETTINGS_YAML} in "
                f"{lookup_path} or one of its parent directories!"
            )
            raise LookupError(msg)

        path = path.parent


class PharaohProject:
    PROJECT_SETTINGS_YAML = "pharaoh.yaml"

    def __new__(cls, *args, **kwargs):
        # Cache the last recently used project instance in a global variable,
        # so it can be accessed from anywhere after creation
        global LRU_PHARAOH_PROJECT  # noqa: PLW0603
        LRU_PHARAOH_PROJECT = object.__new__(cls)
        return LRU_PHARAOH_PROJECT

    def __del__(self):
        try:  # noqa: SIM105
            pharaoh.log.remove_filehandlers(self._project_root)
        except Exception:
            pass

    def __init__(
        self,
        project_root: PathLike,
        overwrite: bool = False,
        templates: str | list[str] | tuple[str] = ("pharaoh.default_project",),
        template_context: dict[str, Any] | None = None,
        **kwargs,
    ):
        """
        Instantiates a Pharaoh project instance using either an existing project root
        (directory containing pharaoh.yaml) or creates a new project.

        :param project_root: A directory containing a pharaoh.yaml file
        :param overwrite: If the project directory already contains files, overwrite them.
        :param templates: The project template(s) to use for creating the Sphinx project files.
                          Maybe be any number of template names or paths to directories.
        :param template_context: The Jinja rendering context for the selected project templates.
        :keyword custom_settings: A path to a YAML file containing settings to overwrite the default project settings.
        """
        self._settings_map: dict[str, omegaconf.DictConfig] = {}
        self._merged_settings: omegaconf.DictConfig = omegaconf.DictConfig({})
        self._project_root: Path = Path(project_root).absolute().resolve()
        self._asset_finder: finder.AssetFinder | None = None

        logging_add_filehandler = kwargs.pop("logging_add_filehandler", True)
        custom_settings = kwargs.pop("custom_settings", None)
        if kwargs:
            msg = f"Unknown keyword arguments {tuple(kwargs.keys())}!"
            raise ValueError(msg)

        pharaoh.log.add_streamhandler()
        if logging_add_filehandler:
            pharaoh.log.add_filehandler(self._project_root)
            pharaoh.log.add_warning_filehandler(self._project_root)

        if isinstance(templates, str):
            templates = [templates]
        self._ensure_project(
            templates=list(templates),
            template_context=template_context,
            recreate=overwrite,
            custom_settings=custom_settings,
        )

        self.load_settings(namespace="all")
        log.setLevel(self.get_setting("logging.level").upper())

    def load_settings(self, namespace: str = "all"):
        """
        Loads settings from various namespaces.

        default
            The default setting in the Pharaoh library

        project
            The project settings that may be modified by the user

        env
            The settings defined by environment variables starting with PHARAO

        all
            Loads all of the above

        :param namespace: The namespace to load settings from. all, default, project or env.
        """
        if namespace in ("all", "default"):
            self._settings_map["default"] = self._load_default_settings()

        if namespace in ("all", "project"):
            project_settings = self._project_root / self.PROJECT_SETTINGS_YAML
            with open(project_settings) as fp:
                self._settings_map["project"] = omegaconf.OmegaConf.load(fp)  # type: ignore[assignment]

        if namespace in ("all", "env"):
            dotlist = []
            env_pat = re.compile(r"^PHARAOH?((\.)|(__)).+$", re.IGNORECASE)
            for k, v in os.environ.items():
                if env_pat.fullmatch(k):
                    keys = re.split(r"\.|(?<!_)__(?!_)", k)
                    key = ".".join(keys[1:]).lower()
                    dotlist.append(f"{key}={v}")
            if len(dotlist):
                self._settings_map["env"] = omegaconf.OmegaConf.from_dotlist(dotlist)
            else:
                self._settings_map["env"] = omegaconf.OmegaConf.create({})
        self._update_merged_settings()

    def _update_merged_settings(self):
        """
        Merges settings from all namespaces.
        """
        self._merged_settings = omegaconf.OmegaConf.create(
            omegaconf.OmegaConf.merge(
                self._settings_map["default"],
                self._settings_map["project"],
                self._settings_map["env"],
            )
        )  # type: ignore[assignment]

    def get_settings(self) -> omegaconf.DictConfig:
        """
        Returns merged settings from all namespaces.
        """
        if self._merged_settings is None:
            self._update_merged_settings()
        return self._merged_settings

    def put_setting(self, key: str, value: Any):
        """
        Sets a setting by its dot-separated name, e.g. "core.debug".

        This has no effect, if there is an environment variable defining the same setting!
        """
        # todo: Let put_setting be able to overwrite settings defined in env vars.
        #       Currently env vars have priority.
        paths = key.lower().split(".")
        node = self._project_settings
        for path in paths[:-1]:
            node = getattr(node, path)
        setattr(node, paths[-1], value)
        self._update_merged_settings()

    def get_setting(self, key: str, default=DEFAULT_MISSING, to_container: bool = False, resolve: bool = True):
        """
        Gets a setting by its dot-separated name, e.g. "core.debug".

        The settings are preferably taken from environment variables (e.g. PHARAOH.CORE.DEBUG), whereas the values
        must be TOML compatible values (e.g. "true" for boolean).

        If no environment variable is found, the user defined settings in the pharaoh.yaml file in the
        project root will be used. If the setting is not specified in there or the file is not existing,
        the Pharaoh default settings are queried.

        If the setting is not found, a LookupError is returned unless "default" is set.

        Examples::

            proj.get_setting("report.title")
            proj.get_setting("cloud.metadata", to_container=True, resolve=False) == {
                "author": "${report.author}",
                "title": "${report.title}",
            }
            proj.get_setting("cloud.metadata", to_container=True, resolve=True) == {
                "author": "loibljoh",
                "title": "Pharaoh Report",
            }
            proj.get_setting("cloud.metadata.title") == "Pharaoh Report"
            proj.get_setting("cloud.metadata") == omegaconf.dictconfig.DictConfig(...)

        :param key: Dot-separated name of the setting value to return
        :param default: The returned default value if the key does not exist.
        :param to_container: If set, recursively converts an OmegaConf config to a primitive Python container type
            (dict or list).
        :param resolve: True to resolve all values if "to_container" is set to True
        """
        if not key:
            msg = "Must be a string with a minimum length of 1!"
            raise ValueError(msg)
        merged_settings = self.get_settings()
        key = key.lower()
        ret = omegaconf.OmegaConf.to_container(merged_settings, resolve=resolve) if to_container else merged_settings
        try:
            paths = key.split(".")
            for path in paths:
                ret = ret[path]

            return ret
        except KeyError:
            if default is DEFAULT_MISSING:
                msg = f"No setting key called {key!r}!"
                raise LookupError(msg) from None
            return default

    def save_settings(self, include_env: bool = False):
        """
        Saves back the project settings to the project YAML file.

        :param include_env: If True, Pharaoh settings that are set via environment variables will be persisted
            to the project settings YAML file.
        """
        project_settings = self._project_root / self.PROJECT_SETTINGS_YAML
        if include_env:
            settings = omegaconf.OmegaConf.merge(
                self._settings_map["project"],
                self._settings_map["env"],
            )
        else:
            settings = self._project_settings
        with open(project_settings, "w") as fp:
            omegaconf.OmegaConf.save(config=settings, f=fp)

    @property
    def _project_settings(self):
        return self._settings_map["project"]

    @property
    def settings_file(self):
        return self._project_root / self.PROJECT_SETTINGS_YAML

    @property
    def project_root(self):
        return self._project_root

    @property
    def sphinx_report_project(self):
        return self.project_root / "report-project"

    @property
    def sphinx_report_project_components(self):
        return self.sphinx_report_project / "components"

    @property
    def sphinx_report_build(self):
        return self.project_root / "report-build"

    @property
    def asset_build_dir(self):
        return self.sphinx_report_project / ".asset_build"

    @property
    def asset_finder(self) -> finder.AssetFinder:
        if self._asset_finder is None:
            self._asset_finder = finder.AssetFinder(self.asset_build_dir)
        return self._asset_finder

    def add_component(
        self,
        component_name: str,
        templates: str | (Path | (Iterable[str] | Iterable[Path])) = ("pharaoh.empty",),
        render_context: dict | None = None,
        resources: list[resource.Resource] | None = None,
        metadata: dict[str, Any] | None = None,
        index: int = -1,
        overwrite: bool = False,
    ):
        """
        Adds a new component to the Pharaoh project

        Example::

            from pharaoh.api import FileResource, PharaohProject

            proj = PharaohProject(".")
            proj.add_component(
                component_name="component_ABC",
                templates=[
                    "plugin_abc.template_xyz",              # plugin template
                    "path/to/template/directory",           # template directory
                    "path/to/template/file/tmpl.pharaoh.py" # template file
                ],
                render_context={"foo": "bar"},
                resources=[FileResource(alias="dlh5_result", pattern="C:/temp/**/*.dlh5")],
                metadata={"some tag": "some value"},
                index=-1,  # append
                overwrite=False
            )

        :param component_name: The name of the component. Must be a valid Python identifier.
        :param templates: A list of component templates to use for creating the components project files.
            Those may be the template identifier (e.g. ``plugin_abc.template_xyz``) of a registered plugin template,
            a path to a template directory or a path to a template file (single-file template).

            Since multiple template may be specified, their order matters in cases where different templates
            create equally-named files, thus templates might overwrite files of the previous templates.

            This enables *template-composition*, where template designers can chunk their bigger templates into
            smaller reusable building blocks.

            If omitted, an empty default template is used.

        :param render_context: The Jinja rendering context for the selected template.
                               The actual template rendering context will have ``component_name``, ``resources`` and
                               ``metadata`` available under the respective keys.
        :param resources: A list of Resource instances, defining the component's resources used in asset scripts
        :param metadata: A dictionary of metadata that may be used to find the component via
                         :func:`PharaohProject.find_component()
                         <pharaoh.project.PharaohProject.find_component>` method.
        :param overwrite: If True, an already existing component will be overwritten
        """
        from pharaoh.templating.first_level.find import find_template
        from pharaoh.templating.first_level.render import render_template

        # Check if component with this name already added
        components = []
        for component in self.iter_components():
            if component["name"] == component_name:
                if overwrite:
                    pass
                else:
                    msg = f"Component {component_name!r} already exists!"
                    raise KeyError(msg)
            else:
                components.append(component)

        render_context = render_context or {}
        render_context["pharaoh_cli_path"] = PHARAOH_CLI_PATH

        if isinstance(templates, (str, Path)):
            templates = [str(templates)]
        templates = [str(t) for t in templates]

        if not templates:
            msg = "No templates specified!"
            raise ValueError(msg)

        new_component = Component(
            name=component_name,
            templates=templates,
            render_context=render_context,
            resources=resources or [],
            metadata=metadata or {},
        )

        # Support negative indexing where -1 is the last item. Normal insert with -1 will insert at second last index.
        if index < 0:
            index = max(0, len(components) + 1 + index)

        components.insert(
            index,
            attrs.asdict(new_component),  # type: ignore[arg-type]
        )

        for templ in templates:
            template_path = find_template(templ)
            if (template_path / "[[ component_name ]]").exists():  # pragma: no cover
                msg = (
                    "The usage of [[ component_name ]] as top level directory name of component "
                    "templates is not required anymore. "
                )
                raise RuntimeError(msg)

            render_template(
                template_path=template_path,
                outputdir=self.sphinx_report_project_components / component_name,
                context=new_component.get_render_context(),
            )

        self._project_settings.components = components
        self.save_settings()
        log.info(f"Added component {component_name!r}. Saved project.")

    def add_template_to_component(
        self, component_name: str, templates: str | Path | Iterable[str], render_context: dict | None = None
    ):
        """
        Adds additional templates to an existing component, that may overwrite existing files during rendering.

        :param component_name: The name of the component. Must be a valid Python identifier.
        :param templates: The component template(s) to use for creating the components project files.
                          Maybe be the a single or multiple template names or paths to a directory.
        :param render_context: The Jinja rendering context for the selected template.
                               The actual template rendering context will have component_name, resources and metadata
                               available under the respective keys.
        """
        from pharaoh.templating.first_level.find import find_template
        from pharaoh.templating.first_level.render import render_template

        # Check if component with this name already added
        for component_index, comp in enumerate(self.iter_components()):  # noqa: B007
            if comp["name"] == component_name:
                component = Component.from_dictconfig(comp)
                break
        else:
            msg = f"Component {component_name!r} does not exist!"
            raise KeyError(msg)

        component.render_context.update(render_context or {})

        if isinstance(templates, (str, Path)):
            templates = [str(templates)]
        templates = [str(t) for t in templates]

        if not templates:
            msg = "No templates specified!"
            raise ValueError(msg)

        component.templates.extend(templates)

        for templ in templates:
            template_path = find_template(templ)
            render_template(
                template_path=template_path,
                outputdir=self.sphinx_report_project_components / component_name,
                context=component.get_render_context(),
            )

        self._project_settings.components[component_index] = attrs.asdict(component)

        self._update_merged_settings()
        self.save_settings()
        log.info(f"Updated component {component_name!r}. Saved project.")

    def remove_component(
        self,
        filter: str,
        regex: bool = False,
    ) -> list[str]:
        """
        Removes one or multiple existing components.

        :param filter: A case-insensitive component filter. Either a full-match or regular expression, depending on
            regex argument.
        :param regex: If True, the filter argument will be treated as regular expression. Components
            that partially match the regular expression are removed.
        :returns: A list of component names that got removed
        """
        # Check if component with this name already added
        if regex:
            rex = re.compile(filter, flags=re.IGNORECASE)
        else:
            filter = filter.lower()
        removed = []
        components = []
        for comp in self.iter_components():
            if regex and rex.match(comp["name"]) is not None or comp["name"].lower() == filter:
                comp_files = self.sphinx_report_project_components / comp["name"]
                if comp_files.exists() and comp_files.is_dir():  # pragma: no cover
                    shutil.rmtree(comp_files)
                removed.append(comp["name"])
            else:
                components.append(comp)

        if len(removed):
            self._project_settings.components = components
            self.save_settings()
            log.info(f"Removed components {','.join(removed)}. Saved project.")
        return removed

    def iter_components(self) -> Iterator[omegaconf.DictConfig]:
        """
        Returns an iterator over all components from a project.
        """
        yield from self._project_settings.get("components", []) or []

    def find_components(self, expression: str = "") -> list[omegaconf.DictConfig]:
        """
        Find components by their metadata using an evaluated expression.

        The expression must be a valid Python expression and following local variables may be used:

        - name: The name of the component
        - templates: A list of templates used to render the component
        - metadata: A dict of metadata specified
        - render_context: The Jinja rendering context specified
        - resources: A list of resource definitions

        :param expression: A Python expression that will be evaluated. If it evaluates to a truthy result,
           the component name is included in the returned list.

           Example: ``name == "dummy" and metadata.foo in (1,2,3)``.

           A failing evaluation will be treated as False. An empty expression will always match.
        """
        found = []
        for comp in self.iter_components():
            if not expression:
                found.append(comp)
                continue
            try:
                result = eval(expression, {}, comp)
            except Exception:
                result = False
            if result:
                found.append(comp)
        return found

    def get_resource(self, alias: str, component: str) -> resource.Resource:
        """
        Finds a Resource from a project component by its alias.

        :param component: The component's name
        :param alias: The resource's alias
        """
        for r in self.iter_resources(component):
            if r["alias"] == alias:
                obj = resource.Resource.from_dict(r)
                obj._cachedir = str(self.sphinx_report_project / ".resource_cache" / component)
                return obj

        msg = f"Cannot find resource {alias!r} in component {component!r}!"
        raise LookupError(msg)

    def iter_resources(self, component: str) -> Iterator[omegaconf.DictConfig]:
        """
        Returns an iterator over all resources from a project component.

        :param component: The component's name
        """
        for comp in self.iter_components():
            if comp["name"] == component:
                yield from comp["resources"]
                return

        msg = f"Component {component} does not exist!"
        raise LookupError(msg)

    def update_resource(self, alias: str, component: str, resource: resource.Resource):
        """
        Updates a Resource from a project component by its alias.

        :param component: The component's name
        :param alias: The resource's alias
        :param resource: The resource's alias
        """
        for comp in self.iter_components():
            if comp["name"] == component:
                for res in comp["resources"]:
                    if res["alias"] == alias:
                        res.update(resource.to_dict())
                        self.save_settings()
                        return
                comp["resources"].append(resource.to_dict())
                self.save_settings()
                return

        msg = f"Component {component} does not exist!"
        raise LookupError(msg)

    def get_default_sphinx_configuration(self, confdir: PathLike):
        """
        Provides Sphinx project configurations, that will be dynamically included by the generated conf.py.
        """
        confdir = Path(confdir)

        config = {
            "pharaoh_jinja_templates": [],
            "pharaoh_jinja_context": {},
            "extensions": [
                "sphinx_design",  # https://github.com/executablebooks/sphinx-design
                "pharaoh.templating.second_level.sphinx_ext.jinja_ext",
                "pharaoh.templating.second_level.sphinx_ext.asset_ext",
            ],
            "project": self.get_setting("report.title"),
            "author": self.get_setting("report.author"),
            "copyright": f"{datetime.datetime.now(tz=datetime.timezone.utc).date()}",
            # The suffix(es) of source filenames.
            # You can specify multiple suffix as a list of string:
            "source_suffix": [".rst", ".rst.jinja2", ".txt"],
            "master_doc": "index",
            "templates_path": ["_templates"],
            # List of patterns, relative to source directory, that match files and
            # directories to ignore when looking for source files.
            # This pattern also affects html_static_path and html_extra_path.
            "exclude_patterns": [".asset_build", "**/asset_scripts"],
            # Make sure the target is unique
            "autosectionlabel_prefix_document": True,
            # Latex Builder (PDF)
        }
        # HTML Builder
        static_path = confdir / "_static"
        assert static_path.exists()
        css_files = list((static_path / "css").glob("*.css"))
        js_files = list((static_path / "js").glob("*.js"))
        config.update(
            {
                "html_title": self.get_setting("report.title"),
                "html_use_smartypants": True,
                "html_last_updated_fmt": "%b %d, %Y",
                "html_split_index": False,
                "html_sidebars": {
                    "**": ["searchbox.html", "globaltoc.html", "sourcelink.html"],
                },
                # Custom index page
                # https://ofosos.org/2018/12/28/landing-page-template/
                # html_additional_pages={"index": "index.html"},
                # Add any paths that contain custom static files (such as style sheets) here,
                # relative to this directory. They are copied after the builtin static files,
                # so a file named "pharaoh.css" will overwrite the builtin "pharaoh.css".
                "html_static_path": ["_static"],
                "html_css_files": [f"css/{cssfile.name}" for cssfile in css_files],
                "html_js_files": [f"js/{jsfile.name}" for jsfile in js_files],
                "html_show_sphinx": False,
                "html_show_copyright": True,
                "html_context": {
                    "pharaoh_version": pharaoh.__version__,
                    "pharaoh_logo": "_static/html_logo.png",
                    "pharaoh_show_logo": self.get_setting("report.html.show_pharaoh_logo"),
                    "pharaoh_homepage": "",  # todo: change to RTD
                },
                "html_style": "sphinx_rtd_theme_overrides.css",
                "html_theme": "sphinx_rtd_theme",
                "html_theme_options": {
                    "display_version": False,
                    "prev_next_buttons_location": "both",
                    "style_external_links": False,
                    "collapse_navigation": False,
                    "sticky_navigation": True,
                    "navigation_depth": 5,
                    "includehidden": False,
                },
            }
        )

        PM.pharaoh_configure_sphinx(self, config, confdir)

        return config

    def generate_assets(self, component_filters: Iterable[str] = (".*",)) -> list[Path]:
        """
        Generate all assets by executing the asset scripts of a selected or all components.

        All asset scripts are executed in separate parallel child processes
        (number of workers determined by ``asset_gen.worker_processes`` setting;
        setting 0 executes all asset scripts sequentially in the current process).

        Setting ``asset_gen.script_ignore_pattern`` determines if a script is ignored.

        Putting the comment ``# pharaoh: ignore`` at the start of a script will also ignore the file.

        :param component_filters: A list of regular expressions that are matched against each component name.
                                  If a component name matches any of the regular expressions, the component's
                                  assets are regenerated (containing directory will be cleared)
        """
        from pharaoh.assetlib.generation import generate_assets, generate_assets_parallel

        pharaoh.log.log_version_info()
        log.info("Generating assets...")

        PM.pharaoh_asset_gen_started(self)
        sources = []
        for comp in self.iter_components():
            comp_name = comp["name"]
            comp_asset_build_dir = self.asset_build_dir / comp_name
            for cfilter in component_filters:
                if re.match(cfilter, comp_name, re.IGNORECASE) is not None:
                    if comp_asset_build_dir.exists():
                        shutil.rmtree(comp_asset_build_dir, ignore_errors=False)

                    cachedir = self.sphinx_report_project / ".resource_cache" / comp_name
                    log.info(f"Preparing resources of component {comp_name!r} for asset generation...")
                    cachedir.mkdir(parents=True, exist_ok=True)
                    resources: dict[str, resource.Resource] = {
                        resource_dict["alias"]: resource.Resource.from_dict(resource_dict)
                        for resource_dict in comp["resources"]
                    }
                    for r in resources.values():
                        r._cachedir = str(cachedir)

                    PM.pharaoh_asset_gen_prepare_resources(project=self, resources=resources)

                    # TransformedResource may depend on others, so process them first.
                    for r in resources.values():
                        r._cachedir = str(cachedir)
                        if isinstance(r, resource.TransformedResource):
                            r.transform(resources=resources)

                    for script in (self.sphinx_report_project_components / comp_name / "asset_scripts").rglob("*"):
                        sources.append((comp_name, script))
                    break

        workers = self.get_setting("asset_gen.worker_processes", 0)
        if workers == 0:  # Run in same process - used for easier debugging
            results: list[tuple[Path, str | None]] = []
            for component_name, asset_source in sources:
                try:
                    generate_assets(self.project_root, asset_src=asset_source, component_name=component_name)
                    results.append((asset_source, None))
                except Exception:
                    results.append((asset_source, traceback.format_exc()))
        else:
            results = generate_assets_parallel(self.project_root, asset_sources=sources, workers=workers)

        msg = "At least one error occurred while asset script execution:\n"
        i = 1
        processed_asset_scripts = []
        for script, ex in results:
            if ex:
                msg += f"\n\nError #{i}: {ex}\n"
                i += 1
            else:
                processed_asset_scripts.append(script)
        if i > 1:
            pharaoh.log.log_debug_info()
            raise AssetGenerationError(msg)

        return processed_asset_scripts

    def build_report(self, catch_errors=True) -> int:
        """
        Builds the Sphinx project and returns the status code.

        :param catch_errors: If True, Sphinx build errors will not raise an exception but return a -1 instead.
        """
        import multiprocessing

        from sphinx.util.docutils import docutils_namespace, patch_docutils

        from pharaoh.sphinx_app import PharaohSphinx

        builder = self.get_setting("report.builder")
        PM.pharaoh_build_started(self, builder)
        self._check_template_dependencies()

        with chdir(self.sphinx_report_project):
            pharaoh.log.log_version_info()
            log.info(f"Building Sphinx project using {builder.upper()} builder...")

            resolved_settings = omegaconf.OmegaConf.create(
                omegaconf.OmegaConf.merge(
                    self._settings_map["default"],
                    self._settings_map["project"],
                    self._settings_map["env"],
                )
            )
            omegaconf.OmegaConf.resolve(resolved_settings)
            self.sphinx_report_build.mkdir(parents=True, exist_ok=True)
            with open(self.sphinx_report_build / "pharaoh.resolved.yaml", "w") as fp:
                omegaconf.OmegaConf.save(config=resolved_settings, f=fp)

            # Sphinx is used via its API instead of the CLI because we want to modify the info/warning stream
            try:
                sourcedir = "."
                confdir = sourcedir
                outputdir = str(self.sphinx_report_build)
                doctreedir = f"{outputdir}\\.doctrees"
                confoverrides: dict | None = {}
                status = pharaoh.log.SphinxLogRedirector(logging.DEBUG)
                warning = pharaoh.log.SphinxLogRedirector(logging.WARNING)
                freshenv = True
                warningiserror = True
                tags = None
                verbosity = int(self.get_setting("report.verbosity", 0))
                jobs = multiprocessing.cpu_count()
                keep_going = True
                pdb = False

                with patch_docutils(confdir), docutils_namespace():
                    app = PharaohSphinx(
                        sourcedir,
                        confdir,
                        outputdir,
                        doctreedir,
                        builder,
                        confoverrides,
                        status,
                        warning,
                        freshenv,
                        warningiserror,
                        tags,
                        verbosity,
                        jobs,
                        keep_going,
                        pdb,
                    )

                    PM.pharaoh_sphinx_app_inited(app)
                    app.build(force_all=False, filenames=None)
                    if app.statuscode:
                        log.error(
                            f"Sphinx build finished with non-zero exit code {app.statuscode}. "
                            f"See warnings/errors in log above!"
                        )
                    else:
                        log.info(f"Sphinx build finished successfully! Report at:\n{self.sphinx_report_build}")

                    PM.pharaoh_build_finished(self, None)

                    return app.statuscode
            except Exception:
                log.error("Errors occurred during Sphinx build:", exc_info=True)
                pharaoh.log.log_debug_info()

                PM.pharaoh_build_finished(self, sys.exc_info())

                if not catch_errors:
                    raise
                return -1

    def open_report(self):  # pragma: no cover
        """
        Opens the generated report (if possible, e.g. for local HTML reports).
        """
        builder = self.get_setting("report.builder").lower()
        if builder == "html" and os.name == "nt":
            report = self.sphinx_report_build / "index.html"
            if not report.is_file():
                log.warning(f"Could not find HTML report {report}!")
                return
            import webbrowser

            webbrowser.WindowsDefault().open_new_tab(f"file://{report}")
        else:
            log.warning(f"The open_report method is not implemented for builder {builder}!")

    def archive_report(self, dest: PathLike | None = None) -> Path:
        """
        Create an archive from the build folder.

        :param dest: A destination path to create the archive. Relative paths are relative to the project root.
                     If omitted, the filename will be taken from the ``report.archive_name`` setting.
        :return: The path to the archive
        """
        if not self.sphinx_report_build.exists():
            msg = "Pharaoh report not built yet!"
            raise Exception(msg)
        dest_path = Path(self.get_setting("report.archive_name") if dest is None else dest)

        if not dest_path.is_absolute():
            dest_path = (self.project_root / dest_path).absolute()

        if not dest_path.suffix:
            dest_path /= self.get_setting("report.archive_name")

        if dest_path.exists():
            os.remove(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        base_name = dest_path.parent / dest_path.stem
        fmt = dest_path.suffix.replace(".", "")
        shutil.make_archive(str(base_name), fmt, self.sphinx_report_build)
        log.info(f"Created archive at {dest_path}")

        return dest_path

    def _check_template_dependencies(self):
        """
        Checks if the used templates of all components are have dependencies to templates that are not used in any
        component.

        E.g. "plugin_abc.template_A" requires an additional component that renders the "plugin_abc.template_B" template,
        in order for all glossary references to work properly.
        """
        l1_templates = PM.pharaoh_collect_l1_templates()
        used_templates = set()
        dependent_templates = set()
        for comp in self._project_settings.get("components", []):
            for template in comp.templates:
                if template in l1_templates:
                    used_templates.add(template)
                    for need in l1_templates[template].needs:
                        dependent_templates.add(need)
        if not dependent_templates.issubset(used_templates):
            msg = (
                f"The used project templates requires the existence of components that render "
                f"following templates: {','.join(dependent_templates - used_templates)}"
            )
            raise ProjectInconsistentError(msg)

    def _ensure_project(
        self,
        templates: list[str],
        template_context: dict[str, Any] | None = None,
        recreate=False,
        custom_settings: str | Path | None = None,
    ):
        """
        Creates a new project by rendering the Sphinx default project at the desired project location.
        """
        self.project_root.mkdir(exist_ok=True, parents=True)
        existing_files = tuple(self.project_root.glob("*"))
        if len(existing_files):
            if recreate:
                shutil.rmtree(
                    self.project_root, onerror=lambda func, path, exc_info: log.warning(f"Could not delete file {path}")
                )
            else:
                # There are existing files, check if those are the required pharaoh project files/folders
                for path in (
                    self.settings_file,
                    self.project_root,
                    self.sphinx_report_project,
                ):
                    if not path.exists():
                        msg = f"Project structure inconsistent. Missing {path}!"
                        raise ProjectInconsistentError(msg)
                self.asset_build_dir.mkdir(exist_ok=True, parents=True)
                return

        # Create a new project
        self.project_root.mkdir(exist_ok=True, parents=True)
        self.asset_build_dir.mkdir(exist_ok=True, parents=True)

        default_settings = self._load_default_settings()
        if isinstance(custom_settings, (str, Path)):
            custom_settings = omegaconf.OmegaConf.load(custom_settings)  # type: ignore[assignment]
            default_settings = omegaconf.OmegaConf.unsafe_merge(default_settings, custom_settings)  # type: ignore[assignment]

        self.settings_file.write_text(omegaconf.OmegaConf.to_yaml(default_settings, resolve=False))

        gitignore = self.project_root / ".gitignore"
        gitignore_lines = [
            "# Auto-generated by Pharaoh",
            "/log*.txt",
            "/report-build",
            "/report-project/.asset_build",
            "/report-project/.resource_cache",
            "/*.zip",
            "/*.idea",
        ]
        PM.pharaoh_modify_gitignore(gitignore_lines)
        gitignore.write_text("\n".join(gitignore_lines), encoding="utf-8")

        from .templating.first_level.render import render_sphinx_base_project

        render_sphinx_base_project(
            outputdir=self.sphinx_report_project,
            templates=templates,
            context={**(template_context or {}), **{"pharaoh_cli_path": PHARAOH_CLI_PATH}},  # noqa: PIE800
        )

        PM.pharaoh_project_created(self)
        return

    def _load_default_settings(self) -> omegaconf.DictConfig:
        default_settings_collection = PM.pharaoh_collect_default_settings()
        loaded = []
        for default_settings in default_settings_collection:
            if isinstance(default_settings, (str, Path)):
                if not Path(default_settings).exists():
                    msg = f"Custom setting YAMl file {default_settings} does not exist!"
                    raise FileNotFoundError(msg)
                loaded.append(omegaconf.OmegaConf.load(default_settings))
            elif isinstance(default_settings, dict):
                loaded.append(omegaconf.OmegaConf.create(default_settings))
            else:
                msg = (
                    f"Unsupported settings type {type(default_settings)} collected from plugin hook "
                    f"pharaoh_collect_default_settings!"
                )
                raise TypeError(msg)

        return functools.reduce(omegaconf.OmegaConf.unsafe_merge, loaded)  # type: ignore[return-value]

    def _update_template_env(self, env: jinja2.Environment):
        """
        Called by PharaohTemplateEnv.sphinx_config_inited_hook to update the template env by
        project specific Jinja globals or filters

        :param env: the Jinja env to update
        """

        def search_error_assets_global():
            """
            Find all error traceback assets in the project grouped by component name.
            """
            error_assets = {}
            for comp in self.iter_components():
                assets = self.asset_finder.search_assets("asset_type == 'error_traceback'", comp.name)
                if assets:
                    error_assets[comp.name] = assets
            return error_assets

        env.globals["get_setting"] = self.get_setting
        env.globals["search_assets_global"] = self.asset_finder.search_assets
        env.globals["search_error_assets_global"] = search_error_assets_global

    def _build_asset_filepath(self, file: PathLike, component_name: str | None = None) -> Path:
        """
        Returns a new file name inside the asset build directory with the same filename as the input file,
        except its file stem is suffixed with a unique uuid4 hash (first 8 chars).

        E.g. `foo/bar/iris_scatter_plot.html` --> `<asset-build-dir>/<component_name>/iris_scatter_plot_ab8b4081.html`
        """
        file = Path(file)
        try:
            component = component_name or context_stack.get_parent_context("generate_assets")["asset"]["component_name"]
        except Exception:
            component = "unknown_component"
        (self.asset_build_dir / component).mkdir(parents=True, exist_ok=True)
        return self.asset_build_dir / component / f"{file.stem}_{str(uuid.uuid4())[:8]}{file.suffix}"


@attrs.define(frozen=True, slots=False)
class Component:
    name: str = attrs.field(validator=(attr.validators.instance_of(str), attr.validators.matches_re(r"\w+")))
    templates: list[str] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(str),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )
    render_context: dict = attrs.field(factory=dict)
    resources: list[dict] = attrs.field(factory=list, converter=lambda resources: [r.to_dict() for r in resources])
    metadata: dict = attrs.field(factory=dict)

    def get_render_context(self) -> dict:
        for reserved_key in ("component_name", "resources", "metadata"):
            if reserved_key in self.render_context:
                msg = f"{reserved_key!r} is a reserved context key!"
                raise ValueError(msg)

        return dict(**self.render_context, component_name=self.name, resources=self.resources, metadata=self.metadata)

    @staticmethod
    def from_dictconfig(cfg: omegaconf.DictConfig):
        return Component(**omegaconf.OmegaConf.to_container(cfg, resolve=False))  # type: ignore[arg-type]


if __name__ == "__main__":
    pass

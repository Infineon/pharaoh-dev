from __future__ import annotations

import importlib
import importlib.util
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pluggy
import wrapt

import pharaoh.plugins.core_plugin.plugin
from pharaoh.plugins import NAME, spec

if TYPE_CHECKING:
    import types
    from collections.abc import Iterable

    import click

    from pharaoh.api import PharaohProject, PharaohSphinx, Resource
    from pharaoh.plugins.template import L1Template


_plugin_result_cache: dict[str, dict] = {}


@wrapt.decorator
def cached(wrapped, instance, args, kwargs):
    func = wrapped.__name__
    key = (args, tuple(kwargs))
    try:
        return _plugin_result_cache[func][key]
    except KeyError:
        result = wrapped(*args, **kwargs)
        _plugin_result_cache.setdefault(func, {})
        _plugin_result_cache[func][key] = result
        return result


def clear_cache():
    _plugin_result_cache.clear()


class PharaohPluginManager:
    """
    Responsible for discovering Pharaoh plugins via namespace packages and PHARAOH_PLUGINS environment variable.
    """

    def __init__(self):
        self.pm = pluggy.PluginManager("pharaoh")

        def before(hook_name, hook_impls, kwargs):
            ...
            # log.debug(f"Plugins: Executing hook {hook_name!r} from plugins " +
            #           ", ".join([impl.plugin_name for impl in hook_impls]))

        def after(outcome, hook_name, hook_impls, kwargs): ...

        self.pm.add_hookcall_monitoring(before=before, after=after)
        self.pm.add_hookspecs(spec)
        self.reload_plugins()

    def reload_plugins(self):
        for name, plugin in self.pm.list_name_plugin():
            self.pm.unregister(plugin, name)

        clear_cache()

        self.pm.load_setuptools_entrypoints(NAME)
        for plugin in self._discover_plugin_modules():
            self.pm.register(plugin)
        self.pm.register(pharaoh.plugins.core_plugin.plugin, name="pharaoh_core")
        self.pm.check_pending()

    @contextmanager
    def disable_plugins(self, *names: str):
        """
        Temporarily disable loaded plugins::

            with PM.disable_plugins("plugin_abc", "..."):
                ...

        :param names: Names of the loaded plugins
        """
        plugins = [(name, self.pm.get_plugin(name)) for name in names]
        for _, plugin in plugins:
            if plugin is not None:
                self.pm.unregister(plugin)
        clear_cache()
        try:
            yield
        finally:
            clear_cache()
            for name, plugin in plugins:
                if plugin is not None:
                    self.pm.register(plugin, name)

    def _discover_plugin_modules(self) -> Iterable[types.ModuleType]:
        """
        Discovers all plugins.

        :return: An iterable of plugins
        """
        for path_item in os.environ.get("PHARAOH_PLUGINS", "").strip("\"'").split(";"):
            path_item = path_item.strip().strip("\"'")
            if not path_item:
                continue
            path = Path(path_item) / "plugin.py"
            if not path.exists():
                msg = f"Cannot find plugin path {path} from environment variable PHARAOH_PLUGINS!"
                raise FileNotFoundError(msg)

            spec = importlib.util.spec_from_file_location(path.stem, str(path))
            if not spec:
                msg = f"Could not get module spec from {path}!"
                raise OSError(msg)
            plugin_module = importlib.util.module_from_spec(spec)
            if not plugin_module:
                msg = f"Plugin {path} is not a valid Python module!"
                raise OSError(msg)
            if not spec.loader:  # pragma: no cover
                msg = f"Could not get module loader for {path}"
                raise OSError(msg)
            spec.loader.exec_module(plugin_module)

            yield plugin_module

    @cached
    def pharaoh_collect_l1_templates(self) -> dict[str, L1Template]:
        """
        Returns a mapping of first-level templates
        """
        return {t.name: t for templates in self.pm.hook.pharaoh_collect_l1_templates() for t in templates}

    @cached
    def pharaoh_collect_l2_templates(self) -> list[Path]:
        return [path for paths in self.pm.hook.pharaoh_collect_l2_templates() for path in paths]

    @cached
    def pharaoh_collect_resource_types(self) -> dict[str, type[Resource]]:
        resources = [resource for resources in self.pm.hook.pharaoh_collect_resource_types() for resource in resources]
        return {type_.__name__: type_ for type_ in resources}

    def pharaoh_asset_gen_prepare_resources(self, project: PharaohProject, resources: dict[str, Resource]):
        return self.pm.hook.pharaoh_asset_gen_prepare_resources(project=project, resources=resources)

    def pharaoh_configure_sphinx(self, project: PharaohProject, config: dict[str, Any], confdir: Path):
        return self.pm.hook.pharaoh_configure_sphinx(project=project, config=config, confdir=confdir)

    def pharaoh_collect_default_settings(self) -> list[Path | dict]:
        return self.pm.hook.pharaoh_collect_default_settings()

    def pharaoh_add_cli_commands(self, cli: click.Group):
        return self.pm.hook.pharaoh_add_cli_commands(cli=cli)

    def pharaoh_build_finished(self, project, exc_info):
        return self.pm.hook.pharaoh_build_finished(project=project, exc_info=exc_info)

    def pharaoh_modify_gitignore(self, gitignore_lines: list[str]):
        return self.pm.hook.pharaoh_modify_gitignore(gitignore_lines=gitignore_lines)

    def pharaoh_project_created(self, project: PharaohProject):
        return self.pm.hook.pharaoh_project_created(project=project)

    def pharaoh_asset_gen_started(self, project: PharaohProject):
        return self.pm.hook.pharaoh_asset_gen_started(project=project)

    def pharaoh_build_started(self, project: PharaohProject, builder: str):
        return self.pm.hook.pharaoh_build_started(project=project, builder=builder)

    def pharaoh_sphinx_app_inited(self, app: PharaohSphinx):
        return self.pm.hook.pharaoh_sphinx_app_inited(app=app)

    @cached
    def pharaoh_find_asset_render_template(self, template_name: str) -> list[Path]:
        templates = self.pm.hook.pharaoh_find_asset_render_template(template_name=template_name)
        return list({Path(t) for t in templates})

    @cached
    def pharaoh_get_asset_render_template_mappings(self) -> dict[str, str]:
        mapping = {}
        for m in self.pm.hook.pharaoh_get_asset_render_template_mappings():
            mapping.update(m)
        return mapping


PM = PharaohPluginManager()

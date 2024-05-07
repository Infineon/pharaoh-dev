from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import omegaconf

from pharaoh.log import log

from .util import obj_groupby

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


class AssetFileLinkBrokenError(LookupError):
    pass


class Asset:
    """
    Holds information about a generated asset.

    :ivar id: An MD5 hash of the asset's filename, prefixed with "__ID__".
        Since a unique suffix is included in the filename, this ID hash is also unique.
        Can be used to quickly find this Asset instance.
    :ivar Path infofile: Absolute path to the ``*.assetinfo`` file
    :ivar Path assetfile: Absolute path to the actual asset file
    :ivar omegaconf.DictConfig context: The content of *infofile* parsed into a OmegaConf dict.
    """

    def __init__(self, info_file: Path):
        assert info_file.suffix == ".assetinfo"
        self.id: str = "__ID__" + hashlib.md5(bytes(info_file.name, "utf-8")).hexdigest()
        self.infofile: Path = info_file
        self.context = omegaconf.OmegaConf.create(json.loads(self.infofile.read_text()))
        for file in self.infofile.parent.glob(f"{self.infofile.stem}*"):
            if file.suffix != ".assetinfo":
                self.assetfile: Path = file
                break
        else:
            msg = f"There is no asset for inventory file {self.infofile}!"
            raise AssetFileLinkBrokenError(msg)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"Asset[{self.infofile.stem}]"

    def __eq__(self, other):
        if isinstance(other, Asset):
            return self.id == other.id and self.infofile == other.infofile and self.assetfile == other.assetfile
        raise NotImplementedError

    def __hash__(self):
        return hash(self.infofile.name)

    def __lt__(self, other):
        if isinstance(other, Asset):
            return self.infofile < other.infofile
        raise NotImplementedError

    def copy_to(self, target_dir: Path) -> Path:
        """
        Copy the asset plus info-file.

        :param target_dir: The target directory to copy to. Will be created if it does not exist.
        :returns: True if files were copied, False otherwise (files already exist)
        """
        target_dir.mkdir(exist_ok=True, parents=True)
        target_info_file = target_dir / self.infofile.name
        if target_info_file.exists():
            return target_dir / self.assetfile.name

        log.debug(f"Copying asset {self} to build directory")
        shutil.copy(self.infofile, target_info_file)

        if Path(self.assetfile).is_file():
            return Path(shutil.copy(self.assetfile, target_dir))

        if Path(self.assetfile).is_dir():
            shutil.copytree(self.assetfile, target_dir / self.assetfile.name)
            return target_dir / self.assetfile.name

        raise NotImplementedError

    def read_json(self) -> dict:
        """
        Reads the file using a JSON parser.
        """
        if self.assetfile.suffix.lower() != ".json":
            msg = "Can only read .json files!"
            raise Exception(msg)
        return json.loads(self.assetfile.read_text("utf-8"))

    def read_yaml(self) -> dict:
        """
        Reads the file using a YAML parser.
        """
        import yaml

        if self.assetfile.suffix.lower() not in (".yaml", ".yml"):
            msg = "Can only read .yaml/.yml files!"
            raise Exception(msg)
        with open(self.assetfile, encoding="utf-8") as fp:
            return yaml.safe_load(fp)

    def read_text(self, encoding: str = "utf-8") -> str:
        """
        Reads the file as text
        """
        return self.assetfile.read_text(encoding)

    def read_bytes(self) -> bytes:
        """
        Reads the file as bytes
        """
        return self.assetfile.read_bytes()


class AssetFinder:
    def __init__(self, lookup_path: Path):
        """
        A class for discovering and searching generated assets.

        An instance of this class will be created by the Pharaoh project, where ``lookup_path`` will be set to
        ``report_project/.asset_build``.

        :param lookup_path: The root directory to look for assets. It will be searched recursively for assets.
        """
        self._lookup_path = lookup_path
        self._assets: dict[str, list[Asset]] = {}
        self.discover_assets()

    def discover_assets(self, components: list[str] | None = None) -> dict[str, list[Asset]]:
        """
        Discovers all assets by recursively searching for ``*.assetinfo`` files and stores
        the collection as instance variable (`_assets`).

        :param components: A list of components to search for assets.
            If None (the default), all components will be searched.
        :return: A dictionary that maps component names to a list of :class:`Asset` instances.
        """
        if isinstance(components, list) and len(components):
            for component in components:
                self._assets[component] = [Asset(file) for file in (self._lookup_path / component).glob("*.assetinfo")]
        else:
            self._assets.clear()
            for asset in (Asset(file) for file in self._lookup_path.glob("*/*.assetinfo")):
                component = asset.assetfile.parent.name
                if component not in self._assets:
                    self._assets[component] = []
                self._assets[component].append(asset)

        return self._assets

    def search_assets(self, condition: str, components: str | Iterable[str] | None = None) -> list[Asset]:
        """
        Searches already discovered assets (see :func:`discover_assets`) that match a condition.

        :param condition: A Python expression that is evaluated using the content of the ``*.assetinfo`` JSON file
            as namespace. If the evaluation returns a truthy result, the asset is returned.

            Refer to :ref:`this example assetinfo file <example_asset_info>` to see the available default namespace.

            Example::

                # All HTML file where the "label" metadata ends with "_plot"
                finder.search_assets('asset.suffix == ".html" and label.endswith("_plot")')

        :param components: A list of component names to search. If None (the default), all components will be searched.
        :return: A list of assets whose metadata match the condition.
        """
        if not condition.strip():
            return []

        code = compile(condition, "<string>", "eval")
        found = []

        for asset in self.iter_assets(components):
            try:
                result = eval(code, {}, asset.context)
            except Exception:
                result = False
            if result:
                found.append(asset)

        def sort_key(asset):
            try:
                return asset.context.asset.index
            except AttributeError:
                return 0

        # Sort by asset index, which reflects the order in which the assets were generated in the asset script
        return sorted(found, key=sort_key)

    def iter_assets(self, components: str | Iterable[str] | None = None) -> Iterator[Asset]:
        """
        Iterates over all discovered assets.

        :param components: A list of component names to search. If None (the default), all components will be searched.
        :return: An iterator over all discovered assets.
        """
        if not self._assets:
            self.discover_assets()

        if isinstance(components, str):
            components = [components]
        components = components or list(self._assets.keys())
        for component in components:
            if component in self._assets:
                yield from self._assets[component]

    def get_asset_by_id(self, id: str) -> Asset | None:
        """
        Returns the corresponding :class:`Asset` instance for a certain ID.

        :param id: The ID of the asset to return
        :return: An :class:`Asset` instance if found, None otherwise.
        """
        for asset in self.iter_assets():
            if asset.id == id:
                return asset
        return None


def asset_groupby(
    seq: Iterable[Asset], key: str, sort_reverse: bool = False, default: str | None = None
) -> dict[str, list[Asset]]:
    """
    Groups an iterable of Assets by a certain metadata key.

    During build-time rendering this function will be available as Jinja global function
    ``asset_groupby`` and alias ``agroupby``.

    Example:

    .. code-block:: none

        We have following 4 assets (simplified notation of specified metadata):
        Asset[a="1", b="3"]
        Asset[a="1", c="4"]
        Asset[a="2", b="3"]
        Asset[a="2", c="4"]

        Grouping by "a":
            asset_groupby(assets, "a")
        will yield
            {
                "1": [Asset[a="1", b="3"], Asset[a="1", c="4"]],
                "2": [Asset[a="2", b="3"], Asset[a="2", c="4"]],
            }


        Grouping by "b" and default "default":
            asset_groupby(assets, "b", default="default")
        will yield
            {
                "3":       [Asset[a="1", b="3"], Asset[a="2", b="3"]],
                "default": [Asset[a="1", c="4"], Asset[a="2", c="4"]],
            }


    :param seq: The iterable of assets to group
    :param key: The nested attribute to use for grouping, e.g. "A.B.C"
    :param sort_reverse: Reverse-sort the keys in the returned dictionary
    :param default: Sort each item, where "key" is not an existing attribute, into this default group
    :return: A dictionary that maps the group names (values of A.B.C) to a list of items out of the input iterable
    """
    return obj_groupby(seq=seq, key=key, sort_reverse=sort_reverse, attr="context", default=default)

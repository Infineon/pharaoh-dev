from __future__ import annotations

import abc
import copy
import glob
from pathlib import Path
from typing import ClassVar

import attrs
import natsort
import omegaconf
from attrs.validators import deep_iterable, in_, instance_of, min_len

__all__ = ["Resource", "LocalResource", "TransformedResource", "FileResource", "CustomResource"]


@attrs.define
class Resource:
    """
    The base class for all resources. Provides serialization/deserialization methods.
    """

    _registry: ClassVar[dict] = {}

    alias: str = attrs.field(validator=(instance_of(str), min_len(1)))
    _cachedir: str = attrs.field(validator=instance_of(str), kw_only=True, default="")

    @staticmethod
    def from_dict(definition: dict | omegaconf.DictConfig) -> Resource:
        from pharaoh.plugins.plugin_manager import PM

        if isinstance(definition, omegaconf.DictConfig):
            definition: dict = omegaconf.OmegaConf.to_container(definition, resolve=True)
        else:
            definition: dict = copy.deepcopy(definition)
        resource_class = definition.pop("__class__")
        registry = PM.pharaoh_collect_resource_types()
        if resource_class not in registry:
            msg = (
                f"No such resource type {resource_class!r} from definition of resource {definition}. "
                f"Available types are {','.join(Resource._registry.keys())!r}!"
            )
            raise LookupError(msg)
        return registry[resource_class](**definition)

    def to_dict(self):
        dikt = dict(**attrs.asdict(self, filter=lambda attr, value: not attr.name.startswith("_")))
        dikt["__class__"] = self.__class__.__name__
        return dikt


@attrs.define
class LocalResource(abc.ABC, Resource):
    """
    Represents a resource that is located on the user's hard-drive.
    """

    @abc.abstractmethod
    def locate(self) -> Path:
        """
        Returns the path to the resource file.
        """
        raise NotImplementedError


@attrs.define
class TransformedResource(LocalResource, abc.ABC):
    """
    A resource that is depending on another resource and maybe transforms it dynamically into another resource.
    """

    sources: list[str] = attrs.field(
        validator=(
            deep_iterable(
                member_validator=instance_of(str),
                iterable_validator=instance_of(list),
            ),
            min_len(1),
        )
    )

    @abc.abstractmethod
    def transform(self, resources: dict[str, Resource]):
        """
        Executed by Pharaoh before asset generation.
        Transforms the linked resource into a new one.
        The resulting resource may be cached or recreated each time.
        """
        raise NotImplementedError


@attrs.define
class CustomResource(Resource):
    """
    A resource that can hold arbitrary information. It may be used as a temporary replacement for
    more specific resources that are not yet implemented.
    For example, it could hold database connection properties or other custom data.

    Example::

        CustomResource(alias="foo", traits=dict(a=1, b=[2, 3], c=dict(d=[4, 5])))


    :ivar traits: A dict with arbitrary data.
    """

    traits: dict


@attrs.define
class FileResource(LocalResource):
    """
    A resource that matches files/directories using a wildcard pattern.

    Example::

        FileResource(alias="mycsvfile", pattern="C:/temp/*.csv", sort="ascending")

    :ivar pattern: A pathname pattern.
        The pattern may contain simple shell-style wildcards.
        Filenames starting with a dot are special cases that are not matched by '*' and '?' patterns.
    :ivar sort: descending (default) or ascending.
        Sorting is done using the natsort library to sort filesystem paths naturally. Example::

            0.txt, 01.txt, 1.txt, 10.txt, 2.txt  # default sorting (ascending)
            0.txt, 01.txt, 1.txt, 2.txt, 10.txt  # natural sorting (ascending)

    """

    pattern: str | Path = attrs.field(converter=str)

    sort: str = attrs.field(validator=in_(("ascending", "descending")), default="descending")

    def locate(self) -> Path:
        """
        Returns the first match for the file pattern, depending on the chosen sort order.
        """
        return self.first_match()

    def first_match(self) -> Path:
        """
        Returns the first match for the file pattern, depending on the chosen sort order.
        """
        return self.get_files()[0]

    def last_match(self) -> Path:
        """
        Returns the last match for the file pattern, depending on the chosen sort order.
        """
        return self.get_files()[-1]

    def get_match(self, index) -> Path:
        """
        Returns the n-th match for the file pattern, depending on the chosen sort order.
        """
        return self.get_files()[index]

    def get_files(self, recursive: bool = True) -> list[Path]:
        """
        Returns all matches for the file pattern, depending on the chosen sort order.

        :param recursive:   If recursive is true, the pattern '**' will match any files and
                            zero or more directories and subdirectories.
        """
        files = [Path(p).resolve() for p in glob.glob(self.pattern, recursive=recursive)]  # type: ignore[type-var]
        sort = {"ascending": False, "descending": True}
        return natsort.natsorted(files, reverse=sort[self.sort])

from __future__ import annotations

import copy
from contextlib import AbstractContextManager
from functools import partial, reduce
from pathlib import Path
from typing import Union

from pharaoh.log import log
from pharaoh.util import json_encoder, mergedeep

PathLike = Union[str, Path]


class MetadataContext(AbstractContextManager):
    def __init__(self, stack: MetadataContextStack, context_name: str = "", **context):
        self._stack = stack
        self._context = context
        self._context_name = context_name

    def __enter__(self):
        self._stack.append_context(self)
        return self

    def __exit__(self, *exc_args):
        self._stack.remove_context(self)

    def activate(self):
        return self.__enter__()

    def deactivate(self):
        self.__exit__()

    def __setitem__(self, key, value):
        self._context[key] = value

    def __getitem__(self, item):
        return self._context[item]

    def __repr__(self):
        return f"{self.__class__.__name__}[{self._context_name}]: {self._context}"

    def __str__(self):
        return repr(self)

    @property
    def name(self):
        return self._context_name


class MetadataContextStack:
    def __init__(self):
        self._stack: list[MetadataContext] = []

    def append_context(self, context: MetadataContext):
        self._stack.append(context)

    def remove_context(self, context: MetadataContext):
        if context in self._stack:
            self._stack.remove(context)

    def new_context(self, context_name="", **context) -> MetadataContext:
        """
        Returns a context manager that adds a new stack entry with custom metadata,
        effectively updating the metadata context assets are exported with.

        When the context manager is left, the stack entry is removed again.

        See :ref:`Metadata Stack docs <reference/assets:Metadata Stack>`.

        :param context_name: An optional name for the context in case it must be looked up.
        :param context: Keywords arguments to specify custom metadata.
        """
        context.pop("stack", None)
        return MetadataContext(context_name=context_name, stack=self, **context)

    def get_parent_context(self, name: str = "", index: int = -1) -> MetadataContext:
        if not name:
            return self._stack[index]

        for ctx in self._stack[::-1]:
            if ctx.name == name:
                return ctx
        msg = f"Cannot find context with name {name!r}!"
        raise LookupError(msg)

    def current_context(self):
        return self._stack[-1]

    def reset(self):
        self._stack.clear()

    def merge_stacks(self) -> dict:
        if len(self._stack) > 1:
            merge = partial(mergedeep.merge, safe=False)
            return reduce(merge, [copy.deepcopy(s._context) for s in self._stack])

        if len(self._stack) == 1:
            return copy.deepcopy(self._stack[0]._context)

        return {}

    def dump(self, asset_filepath: PathLike) -> Path:
        """
        Dumps the currently active context stack to a companion file of the
        asset with the file suffix ".assetinfo" and returns its path.

        :param asset_filepath: The path to the asset file for which the companion file shall be created.
                               This path is created by PharaohApp.build_asset_filepath
        """
        asset_filepath = Path(asset_filepath)
        merged_stack = self.merge_stacks()
        assetinfo = asset_filepath.parent / f"{asset_filepath.stem}.assetinfo"
        assetinfo.write_text(json_encoder.encode_json(merged_stack, indent=1))
        log.debug(
            f"Created asset {merged_stack['asset']['name']!r} from script "
            f"{merged_stack['asset'].get('script_name', '__unknown__')!r}."
        )
        return assetinfo


context_stack = MetadataContextStack()
metadata_context = context_stack.new_context


if __name__ == "__main__":  # pragma: no cover
    stack = MetadataContextStack()
    metadata_context = stack.new_context

    with metadata_context(a=1), metadata_context(b=2):
        pass

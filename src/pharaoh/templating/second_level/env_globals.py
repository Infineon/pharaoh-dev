from __future__ import annotations

import uuid
from functools import partial
from pathlib import Path

from pharaoh.assetlib.finder import asset_groupby


def raise_helper(msg):
    """
    Raises an Exception with a certain message. The actual name of the Jinja global function is ``raise``.
    """
    raise Exception(msg)


def heading(text: str, level: int) -> str:
    """
    Renders a heading for a certain level.

    Shortcuts for this function are automatically generated with names h1...h7.

    Examples::

        {{ heading("Page Title", 1) }}
        {{ h2("Sub-Title") }}

    :param text: The heading
    :param level: The heading level. From 1 (top-level) to 7.
    """
    default = {1: "#", 2: "*", 3: "=", 4: "-", 5: "^", 6: '"', 7: "~"}
    if isinstance(level, (float, int)):
        if int(level) not in default:
            msg = "Default heading characters only available from index 1 to 7!"
            raise LookupError(msg)
        character = default[level]
    else:
        character = str(level)
        if character not in default.values():
            raise ValueError("character must be an integer from 1-7 or one of " + ",".join(default.values()))

    text = text.strip().replace("\r", "").replace("\n", "")
    if len(text) < 2:
        msg = "Heading text must be at least 2 characters"
        raise ValueError(msg)
    return f"{text}\n{character*len(text)}"


def rand_id(chars: int | None = None) -> str:
    """
    Returns a unique id for usage in HTML as it is made sure it starts with no number
    """
    id = "i" + uuid.uuid4().hex
    return id[:chars]


def read_text(file) -> str:
    """
    Reads a file content using utf-8 encoding.
    """
    file = Path(file)
    return file.read_text("utf-8")


def hrule():
    """
    Renders a 1px gray horizontal rule using a raw html directive.
    """
    return '.. raw:: html\n\n    <hr style="height:1px;border-width:0;color:gray;background-color:gray">\n\n'


def fglob(pattern: str, root: str = ".") -> list[Path]:
    """
    Returns a list of relative paths of all files relative to a root directory that match a certain pattern.

    Examples::

        {% set index_files1 = fglob("index_*.rst") %}
        {% set index_files2 = fglob("subdir/index_*.rst") %}

    :param pattern: A glob pattern to match files.
    :param root: The root directory for discovering files and anchor for relative paths.
        Default is the current working directory (the parent directory of the currently rendered file).
    """
    rootpath = Path(root).absolute()
    matches = rootpath.glob(pattern)
    return [file.relative_to(rootpath) for file in matches]


def assert_true(statement: bool, message: str = ""):
    """
    Wrapper for Python's assert builtin.

    :param statement: A boolean statement
    :param message: The message for the AssertionError, if statement is False.
    """
    if message:
        assert statement, message
    else:
        assert statement


env_globals = {
    "assert_true": assert_true,
    "fglob": fglob,
    "hrule": hrule,
    "raise": raise_helper,
    "heading": heading,
    "rand_id": rand_id,
    "read_text": read_text,
    "agroupby": asset_groupby,
    "asset_groupby": asset_groupby,
}
# Shortcuts for headings
for i in range(1, 8):
    env_globals[f"h{i}"] = partial(heading, level=i)  # type: ignore[assignment]


# Only document the functions defined in here
to_document = {
    k: func for k, func in env_globals.items() if hasattr(func, "__module__") and func.__module__ == __name__
}

from __future__ import annotations

import pytest

from pharaoh.assetlib.util import parse_signature
from pharaoh.templating.second_level.sphinx_ext.asset_ext import split_filter


def test_parse_signature_plotly_write_html(tmp_path):
    sig = parse_signature("plotly.io._html.write_html", ("bla", 123), {"post_script": 456})
    print(sig)
    assert sig["fig"] == "bla"
    assert sig["file"] == 123
    assert sig["config"] is None
    assert sig["post_script"] == 456
    assert len(sig) == 14


def test_parse_signature_holoviews_util_save(tmp_path):
    sig = parse_signature("holoviews.util.save", ("bla", 123), {"title": "foo"})
    print(sig)
    assert sig["obj"] == "bla"
    assert sig["filename"] == 123
    assert sig["title"] == "foo"
    assert len(sig) == 8


@pytest.mark.parametrize(
    ("string", "expected"),
    [
        ("", []),
        ("a", ["a"]),
        (r"a\;b", [r"a\;b"]),
        (" a\n ", ["a"]),
        ("a;b", ["a", "b"]),
        ("a;b\nc\\;d", ["a", "b c\\;d"]),
        ("a; b \n   c ", ["a", "b c"]),
    ],
)
def test_pharaoh_asset_ext_split_filter(string: str, expected: list):
    result = split_filter(string)
    assert result == expected

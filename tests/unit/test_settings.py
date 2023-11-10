import os
import re
from datetime import datetime

import pytest


def test_load_and_get_settings(new_proj):
    assert new_proj.get_setting("report.title") == "Pharaoh Report"
    assert new_proj.get_setting("toolkits.matplotlib.savefig.dpi") == 150
    assert new_proj.get_setting("toolkits.matplotlib.savefig.edgecolor") == "auto"
    assert new_proj.get_setting("unknown", None) is None
    assert new_proj.get_setting("unknown", "baz") == "baz"

    os.environ["PHARAOH.PYTEST.FOO"] = "123"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo") == 123

    os.environ["PHARAOH.PYTEST.FOO"] = "abc"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo") == "abc"

    os.environ["PHARAOH.PYTEST.FOO"] = "True"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo") is True

    os.environ["PHARAOH.PYTEST.FOO"] = "true"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo") is True

    os.environ["PHARAOH.PYTEST.FOO"] = "false"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo") is False

    os.environ["PHARAOH.PYTEST.FOO"] = "[1,2,3]"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo") == [1, 2, 3]

    os.environ["PHARAOH.PYTEST.FOO"] = "{'a':1}"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo") == {"a": 1}

    os.environ["PHARAOH__PYTEST__FOO.BA___R"] = "1"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo.ba___r") == 1

    os.environ["PHARAOH__PYTEST__FOO.BA___R"] = "1"
    new_proj.load_settings("env")
    assert new_proj.get_setting("pytest.foo.ba___r") == 1

    # cleanup
    del os.environ["PHARAOH__PYTEST__FOO.BA___R"]
    del os.environ["PHARAOH.PYTEST.FOO"]
    new_proj.load_settings("env")

    # test default
    assert new_proj.get_setting("does_not_exist", 123) == 123

    # test errors
    with pytest.raises(LookupError):
        new_proj.get_setting("does_not_exist")

    with pytest.raises(ValueError, match="Must be a string"):
        new_proj.get_setting("")


def test_save_load_settings(new_proj):
    new_proj.put_setting("a", 1)
    assert new_proj.get_setting("a") == 1
    assert new_proj._project_settings.a == 1

    new_proj.put_setting("b", {"d": 1})
    assert new_proj.get_setting("b.d") == 1
    new_proj.put_setting("b.c", 1)
    assert new_proj.get_setting("b.c") == 1

    os.environ["PHARAOH.PYTEST.FOO"] = "abc"
    # Check if unsaved changes are overwritten
    new_proj.load_settings()
    assert new_proj._project_settings.get("a", None) is None

    with pytest.raises(AttributeError):
        assert new_proj._project_settings.pytest.foo
    assert new_proj.get_setting("pytest.foo") == "abc"

    # Check is save/load is persistent
    new_proj._project_settings.a = 1
    new_proj.save_settings()
    new_proj.load_settings()
    assert new_proj._project_settings.a == 1

    with pytest.raises(AttributeError):
        assert new_proj._project_settings.pytest.foo
    assert new_proj.get_setting("pytest.foo") == "abc"

    del os.environ["PHARAOH.PYTEST.FOO"]
    new_proj.save_settings(include_env=True)
    new_proj.load_settings()

    assert new_proj._project_settings.pytest.foo == "abc"
    assert new_proj.get_setting("pytest.foo") == "abc"


def test_resolvers(new_proj):
    new_proj.put_setting("project_dir", "${pharaoh.project_dir:}")
    project_dir = new_proj.get_setting("project_dir")
    assert new_proj.project_root.as_posix() == project_dir

    timestamp_regex = re.compile("^[0-9]{8}_[0-9]{6}$")

    new_proj.put_setting("utcnow", "${utcnow.strf:%Y%m%d_%H%M%S}")
    utcnow = new_proj.get_setting("utcnow")
    assert timestamp_regex.fullmatch(utcnow) is not None
    utcnow_parsed = datetime.strptime(utcnow, "%Y%m%d_%H%M%S").astimezone()

    new_proj.put_setting("now", "${now.strf:%Y%m%d_%H%M%S}")
    now = new_proj.get_setting("now")
    assert timestamp_regex.fullmatch(now) is not None
    now_parsed = datetime.strptime(now, "%Y%m%d_%H%M%S").astimezone()

    assert (now_parsed - utcnow_parsed).total_seconds() != 0

    new_proj.put_setting(
        "test",
        {
            "author": "${report.author}",
            "title": "${report.title}",
        },
    )
    assert new_proj.get_setting("test", to_container=True, resolve=False) == {
        "author": "${report.author}",
        "title": "${report.title}",
    }
    assert new_proj.get_setting("test", to_container=True, resolve=True) == {
        "author": os.environ["USERNAME"],
        "title": "Pharaoh Report",
    }

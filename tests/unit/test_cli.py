import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from pharaoh.cli import cli
from pharaoh.project import get_project
from pharaoh.util.contextlib_chdir import chdir


@pytest.fixture()
def tmp_cwd(tmp_path):
    with chdir(tmp_path) as cwd:
        yield cwd


@pytest.fixture()
def invoke():
    cli_runner = CliRunner()

    def invoke_(args: str):
        print(f"Invoking: pharaoh {args}")
        result = cli_runner.invoke(cli, args, catch_exceptions=False)
        print(f"Stdout:   {result.stdout}")
        assert result.exit_code == 0, result.stdout
        return result.stdout

    return invoke_


def test_new_with_default_arguments(tmp_cwd, invoke):
    _result = invoke("new")


def test_new_with_env_vars(tmp_cwd):
    cli_runner = CliRunner()
    with cli_runner.isolation(env={"PHARAOH.FOO": "{'bar': 123}"}):
        result = cli_runner.invoke(cli, "new", catch_exceptions=False)
    assert result.exit_code == 0, result.stdout

    proj = get_project(tmp_cwd)
    assert proj.get_setting("foo.bar") == 123


def test_new_with_templates_and_context(tmp_cwd, invoke):
    _result = invoke("new -t pharaoh_testing.simple -c \"{'a': 1}\"")

    template_context = json.loads((tmp_cwd / "report-project/.template_context.json").read_text())
    assert template_context["a"] == 1

    assert (tmp_cwd / r"report-project/asset_scripts/plotly_plots.py").exists()


def test_new_with_custom_settings(tmp_cwd, invoke):
    settings = Path("settings.yaml")
    settings.write_text('pytest:\n  foo: "bar"\n')
    _result = invoke("-p project new -s settings.yaml")

    proj = get_project(tmp_cwd / "project")
    assert proj.get_setting("pytest.foo") == "bar"


def test_add(tmp_cwd, invoke):
    invoke("new")
    _result = invoke("add -n dummy1 -t pharaoh_testing.simple -c \"{'test_name':'dummy'}\"")
    assert "dummy1" in _result


def test_add_template(tmp_cwd, invoke):
    invoke("new")
    invoke("add -n dummy1 -t pharaoh_testing.simple -c \"{'test_name':'dummy'}\"")
    _result = invoke("add-template -n dummy1 -t pharaoh_testing.complex")
    assert "Updated component 'dummy1'" in _result


def test_add_with_resource(tmp_cwd, invoke):
    invoke("new")
    _result = invoke(
        """add -n dummy1 -t pharaoh_testing.simple -r "FileResource(alias='foo', pattern='.*')"
        -r "FileResource(alias='bar', pattern='.*')" """
    )
    assert "dummy1" in _result

    proj = get_project(tmp_cwd)
    rsrc_foo = proj.get_resource("foo", "dummy1")
    rsrc_bar = proj.get_resource("bar", "dummy1")
    assert rsrc_foo.alias == "foo"
    assert rsrc_bar.alias == "bar"


def test_update_resource(tmp_cwd, invoke):
    invoke("new")
    _result = invoke(
        """add -n dummy1 -t pharaoh_testing.simple -r "FileResource(alias='foo', pattern='.*')"
        -r "FileResource(alias='bar', pattern='.*')" """
    )
    assert "dummy1" in _result

    _result = invoke("""update-resource -n dummy1 -a foo -r "FileResource(alias='baz', pattern='.*')" """)

    proj = get_project(tmp_cwd)
    with pytest.raises(LookupError):
        proj.get_resource("foo", "dummy1")
    rsrc_bar = proj.get_resource("bar", "dummy1")
    rsrc_baz = proj.get_resource("baz", "dummy1")
    assert rsrc_bar.alias == "bar"
    assert rsrc_baz.alias == "baz"


def test_remove(tmp_cwd, invoke):
    invoke("new")
    invoke("add -n dummy1 -t pharaoh_testing.simple")
    invoke("add -n dummy2 -t pharaoh_testing.simple")
    invoke("add -n dummy3 -t pharaoh_testing.simple")
    assert "dummy1, dummy2" in invoke("remove -f dummy[12] -r")
    assert "dummy3" in invoke("remove -f dummy3")


def test_env_vars(tmp_cwd, invoke):
    invoke("new")
    invoke("env foo_A 123")
    invoke("env foo_B bar")
    invoke("env foo_C \"{'baz': 123}\"")
    invoke("env foo_C.bar something")
    invoke("env foo_D class")
    invoke("env foo_E")

    proj = get_project(tmp_cwd)
    assert proj.get_setting("foo_a") == 123
    assert proj.get_setting("foo_b") == "bar"
    assert proj.get_setting("foo_c") == {"baz": 123, "bar": "something"}
    assert proj.get_setting("foo_d") == "class"
    assert proj.get_setting("foo_e") is None


def test_cli_flow(tmp_cwd, invoke):
    plugins_text = invoke("print-plugins")
    print(plugins_text)
    assert "core_plugin" in plugins_text
    assert rf"testing{os.sep}plugin.py" in plugins_text

    invoke("new")
    invoke("add --name dummy1 -t pharaoh_testing.simple -c \"{'test_name':'dummy'}\"")
    invoke("add --name dummy2 -t pharaoh_testing.simple -c \"{'test_name':'dummy'}\"")
    result = invoke("generate")
    assert "dummy1/asset_scripts" in result
    assert "dummy2/asset_scripts" in result
    result = invoke("generate -f .*")
    assert "dummy1/asset_scripts" in result
    assert "dummy2/asset_scripts" in result
    result = invoke("generate -f dummy1 -f dummy2")
    assert "dummy1/asset_scripts" in result
    assert "dummy2/asset_scripts" in result
    result = invoke("generate -f dummy2")
    assert "dummy1/asset_scripts" not in result
    assert "dummy2/asset_scripts" in result

    result = invoke(f"-p {tmp_cwd.as_posix()} build")
    assert "finished successfully" in result

    result = invoke("archive")
    assert "Created archive at" in result
    assert ".zip\n" in result

    result = invoke(f"-p {tmp_cwd.as_posix()} archive --dest archives")
    assert rf"archives{os.sep}pharaoh_report_" in result

    result = invoke(f"-p {tmp_cwd.as_posix()} archive -d archives/myarchive.zip")
    assert rf"archives{os.sep}myarchive.zip" in result

    assert (get_project(tmp_cwd).sphinx_report_build / "index.html").exists()


def test_cli_command_chaining(tmp_cwd, invoke):
    result = invoke(
        "new"
        " add --name dummy1 -t pharaoh_testing.simple -c \"{'test_name':'dummy1'}\""
        " add --name dummy2 -t pharaoh_testing.simple -c \"{'test_name':'dummy2'}\""
        " generate build archive -d archives/myarchive.zip"
    )
    assert "Added component 'dummy1'" in result
    assert "Added component 'dummy2'" in result
    assert "Generating assets..." in result
    assert "Building Sphinx" in result
    assert "Sphinx build finished successfully" in result
    assert "Created archive at" in result
    assert rf"archives{os.sep}myarchive.zip" in result

    assert (get_project(tmp_cwd).sphinx_report_build / "index.html").exists()

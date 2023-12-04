from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def eng():
    try:
        import matlab.engine as me

        from pharaoh.assetlib.api import Matlab
    except ModuleNotFoundError:
        pytest.xfail("matlab.engine not installed")

    m = Matlab()
    try:
        m.connect()
        yield m
    except me.EngineError:
        pytest.xfail("Failed connecting to Matlab.")


def test_execute_script(eng, tmp_path):
    script = tmp_path / "myscript.m"
    script.write_text(
        """
[x,y,z] = sphere;
r = 2;
surf(x*r,y*r,z*r)
axis equal

disp('disp')
fprintf('fprintf default\\n')
fprintf(1, 'fprintf stdout\\n')
fprintf(2, 'fprintf stderr\\n')
"""
    )
    out, err = eng.execute_script(script)
    assert out.splitlines(False) == ["disp", "fprintf default", "fprintf stdout"]
    assert err.splitlines(False) == ["fprintf stderr"]


def test_execute_function(eng, tmp_path):
    script = tmp_path / "myfunc.m"
    script.write_text(
        """
function dummy=myfunc(r)
dummy = 123;
[x,y,z] = sphere;
surf(x*r,y*r,z*r)
axis equal

disp('disp')
fprintf('fprintf default\\n')
fprintf(1, 'fprintf stdout\\n')
fprintf(2, 'fprintf stderr\\n')
end
"""
    )
    result, out, err = eng.execute_function("myfunc", [800.0], nargout=1, workdir=tmp_path)
    assert result == 123.0
    assert out.splitlines(False) == ["disp", "fprintf default", "fprintf stdout"]
    assert err.splitlines(False) == ["fprintf stderr"]

    result, out, err = eng.execute_function("myfunc", [800.0], nargout=0, workdir=tmp_path)

from __future__ import annotations

import datetime
import io
import os
import typing as t
from pathlib import Path

from pharaoh.log import log

if t.TYPE_CHECKING:
    import matlab.engine as me


def ensure_engine():
    try:
        import matlab.engine  # noqa: F401
    except Exception:
        log.error(
            "The Matlab Engine for Python is not installed.\n"
            "Please install the corresponding version via PIP:\n"
            "  R2020B: pip install matlabengine==9.9.*\n"
            "  R2021A: pip install matlabengine==9.10.*\n"
            "  R2021B: pip install matlabengine==9.11.*\n"
            "  R2022A: pip install matlabengine==9.12.*\n"
            "  R2022B: pip install matlabengine==9.13.*\n"
            "  R2023A: pip install matlabengine==9.14.*\n"
            "  R2023B: pip install matlabengine==9.15.*\n"
        )
        raise


PathLike = t.Union[str, Path]


class Matlab:
    """
    Matlab engine for Pharaoh asset generation.

    Usage::

        from pharaoh.assetlib.api import Matlab

        eng = Matlab()
        with eng:
            out, err = eng.execute_script("myscript.m")
            result, out, err = eng.execute_function("myfunc", [800.0], nargout=1)

    """

    def __init__(self, start_options: str = "-nodesktop"):
        """
        Matlab engine for Pharaoh asset generation.

        :param start_options: See options at https://de.mathworks.com/help/matlab/ref/matlabwindows.html
        """
        self._engine: me.MatlabEngine | None = None
        self._start_options = start_options

    @property
    def eng(self) -> me.MatlabEngine:
        """
        Returns the matlab engine instance
        """
        return self._engine

    def __enter__(self):
        """
        Context manager enter. Connects to Matlab.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit. Disconnects from Matlab.
        """
        if self.eng is not None:
            self.eng.exit()
            self._engine = None

    def connect(self):
        """
        Connects to a Matlab engine. If an engine is running it will be connected, otherwise a new Matlab instance
        will be started and connected.
        """
        ensure_engine()
        import matlab.engine as me

        active_engines = me.find_matlab()
        if len(active_engines):
            self._engine = me.connect_matlab(name=active_engines[0], background=False)
        else:
            self._engine = me.start_matlab(option=self._start_options, background=False)

        # Write connection info to Matlab workspace
        info = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + f", PID {os.getpid()}"
        self.eng.workspace["PharaohConnected"] = info

    def show_gui(self):
        """
        Makes the Matlab GUI visible.
        """
        self.eng.desktop(nargout=0)

    def execute_script(self, script_path: PathLike) -> tuple[str, str]:
        """
        Executes a Matlab script.

        Returns a tuple of strings containing the stdout and stderr streams of the script execution.
        """
        script_path = Path(script_path).absolute()

        # Call the script
        fname = script_path.stem
        workdir = str(script_path.parent) if script_path.exists() else None
        _, out, err = self.execute_function(function_name=fname, args=None, nargout=0, workdir=workdir)
        return out, err

    def execute_function(
        self,
        function_name: str,
        args: list[t.Any] | None = None,
        nargout: int = 0,
        workdir: PathLike | None = None,
    ) -> tuple[t.Any, str, str]:
        """
        Executes a Matlab function

        Returns a tuple of result, stdout stream and stderr stream of the function execution.

        The shape/type of result depends on the argument 'nargout'. See below.

        :param function_name:
            The name of the function to execute.

            The function must be in the Matlab path to execute it.

            Alternatively the workdir argument can be set to the parent directory of the function.
        :param args: A list of positional input arguments to the function
        :param nargout:
            The number of output arguments.

            If 0, the result return value of this function will be None.

            If 1, the result return value will be a single value.

            If greater than 1, the result return value will be a tuple containing nargout values.
        :param workdir: The Matlab working directory to be changed to during function execution. Skipped if None.
        """
        old_cwd = self.eng.cd(str(workdir)) if workdir is not None else None
        try:
            out = io.StringIO()
            err = io.StringIO()
            result = getattr(self.eng, function_name)(
                *(args or []), background=False, nargout=max(0, int(nargout)), stdout=out, stderr=err
            )
            return result, out.getvalue(), err.getvalue()
        except Exception as e:
            log.error(f"Execution of Matlab function/script {function_name!r} failed: {e}", exc_info=True)
            raise
        finally:
            if old_cwd:
                self.eng.cd(old_cwd, background=False)

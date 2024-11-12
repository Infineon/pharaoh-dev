from __future__ import annotations

import contextlib
import io
import traceback

import pharaoh.log
from pharaoh.assetlib.generation import register_asset

log = pharaoh.log.log


@contextlib.contextmanager
def catch_exceptions(
    catch: tuple[type[Exception], ...] = (Exception,),
    reraise: tuple[type[Exception], ...] = (),
    msg_prefix: str = "",
    log_exc: bool = True,
    render_exc: bool = True,
):
    """
    Catch exceptions of given types.

    If an exception is caught, the Sphinx report generation will report a warning.

    .. seealso:: :ref:`reference/assets:Catching Errors`

    :param catch: The exception types to catch
    :param reraise: The exception types to re-raise (has precedence over catch)
    :param msg_prefix: The message prefix to log before the exception message
    :param log_exc: Whether to log the exception message as a warning
    :param render_exc: Whether to export the exception traceback as an asset to be included in the report
    """
    try:
        yield
    except reraise:
        raise
    except catch as e:
        if log_exc:
            log.warning(
                f"An error occurred during asset generation: {msg_prefix}{e}\n"
                f"Traceback:\n{traceback.format_exc(limit=-1)}"
            )
        if render_exc:
            register_asset(
                file="error.txt",
                template="error_traceback",
                data=io.BytesIO(traceback.format_exc(limit=-1).encode("utf-8")),
                metadata={"error_message": f"{msg_prefix}{e}", "asset_type": "error_traceback"},
            )

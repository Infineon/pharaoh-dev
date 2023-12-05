# mypy: disable-error-code="method-assign"
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

try:
    import panel.io.save as panel_io_save
    from bokeh.core.templates import get_env

    PANEL_AVAIL = True
except (ImportError, ModuleNotFoundError):
    PANEL_AVAIL = False

# from pharaoh import project
from pharaoh.assetlib.util import parse_signature

if PANEL_AVAIL:
    # memorize the unpatched functions
    vanilla_panel_io_save_save = panel_io_save.save

    @contextmanager
    def patch():
        # switching out the original with the patched functions
        # Not implemented yet
        # setattr(panel_io_save, "save", patched_panel_io_save_save)

        yield

        # undo the patching
        # setattr(panel_io_save, "save", vanilla_panel_io_save_save)

    def patched_panel_io_save_save(*args, **kwargs):
        """
        This is the patched version of ``panel.io.save.save(*args, **kwargs)`` function.
        """
        params = parse_signature(obj=vanilla_panel_io_save_save, args=args, kwargs=kwargs)
        params.pop("kwargs")
        params.update(kwargs)
        params["template"] = get_env().from_string(
            Path(__file__).with_name("bokeh_embed.html").read_text(encoding="utf-8")
        )
        raise NotImplementedError
        vanilla_panel_io_save_save(**params)

else:

    def init_module():
        pass

    @contextmanager
    def patch():
        yield

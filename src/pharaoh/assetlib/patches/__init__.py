from __future__ import annotations

from contextlib import ExitStack, contextmanager


@contextmanager
def patch_3rd_party_libraries():
    """
    A context manager that patches certain save/show functions of the supported libraries (mostly plotting frameworks).
    When exiting this context the patching will be undone.

    show/display functions become no-ops and functions outputting files are patching the storage location
    to be inside <pharaoh-project>/pharaoh_assets/build. For interactive plots the options that control things like
    js/css resources are patched to use a single copy inside the asset folder to avoid wasting diskspace for each plot.
    For static images

    User perspective:
        The patched functions only change their behavior when the script is called by pharaoh. When the script is called
        standalone then the behavior remains unchanged.

    .. important::

        When using this function, either use it as a context manager or instantiate it, assign it to a variable and
        call ``__enter()__`` on it. If no reference to the context manager is kept, it gets garbage-collected and
        shuts down, which leads to a premature reset of patches.

    """
    from pharaoh.assetlib.patches import _bokeh, _holoviews, _matplotlib, _pandas, _panel, _plotly

    patch_modules = (_bokeh, _holoviews, _matplotlib, _pandas, _plotly, _panel)

    with ExitStack() as stack:
        for module in patch_modules:
            if hasattr(module, "init_module"):
                module.init_module()
            stack.enter_context(module.patch())
        try:
            yield
        finally:
            # In error case, close the exit stack explicitly here,
            # since yield will raise an exception if the asset script execution results in an error.
            # So we have to handle this error and undo the patching.
            # Previously there was no try...except around the yield, which led to not un-patching
            # the 3rd-party packages.
            stack.close()

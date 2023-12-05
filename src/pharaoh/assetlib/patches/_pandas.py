# mypy: disable-error-code="method-assign"
from __future__ import annotations

import uuid
from contextlib import contextmanager
from pathlib import Path

try:
    import pandas as pd

    PANDAS_AVAIL = True
except (ImportError, ModuleNotFoundError):
    PANDAS_AVAIL = False

from pharaoh import project
from pharaoh.assetlib.context import context_stack
from pharaoh.assetlib.util import parse_signature

if PANDAS_AVAIL:
    # memorize the unpatched functions
    vanilla_df_to_html = pd.DataFrame.to_html

    @contextmanager
    def patch():
        """
        A context manager that patches all functions of pandas relevant to export html when executed in a pharaoh
        context. When the program exits the patch-context, the patching will be undone.

        The main goals:
            - retain original function call signature
            - alter storage location of figures to the pharaoh build folder
            - inject table generation parameters via config file
        """

        # switching out the original with the patched functions
        if pd.DataFrame.to_html == vanilla_df_to_html:
            pd.DataFrame.to_html = patched_df_to_html

        yield

        # undo the patching
        if pd.DataFrame.to_html != vanilla_df_to_html:
            pd.DataFrame.to_html = vanilla_df_to_html

    def patched_df_to_html(*args, **kwargs):
        """
        This is the patched version of ``pandas.DataFrame.to_html(...)`` function.

        Changes:
            - if a storage location is passed in (optional) it changes the destination to be inside pharaoh's asset
              build folder
            - takes kwargs from the pharaoh config file and updates the kwargs passed into the function

        docs: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_html.html
        """
        params = parse_signature(obj=vanilla_df_to_html, args=args, kwargs=kwargs, fromclass=True)
        buf = params["buf"]

        if buf is None:
            return  # when to_html() is called without a destination (optional), there's nothing to patch

        active_app = project.get_project()

        # relocating the saved file by patching the buf parameter
        file_path = active_app._build_asset_filepath(Path(buf))
        with context_stack.new_context(
            asset={
                "user_filepath": str(buf),
                "file": str(file_path),
                "name": file_path.name,
                "stem": file_path.stem,
                "suffix": file_path.suffix,
                "template": "datatable",
            }
        ):
            params["buf"] = str(file_path)
            params["table_id"] = "T_" + uuid.uuid4().hex[:5]  # make sure id does not start with a number
            pandas_config = active_app.get_setting("toolkits.pandas.to_html")
            params.update(pandas_config)

            vanilla_df_to_html(**params)
            context_stack.dump(file_path)

else:
    # if the package is not installed there is nothing to patch, so we silently do nothing when patch() is called.

    @contextmanager
    def patch():
        yield

from __future__ import annotations

import getpass
import logging
import os
import platform
import re
import sys
from pathlib import Path

import pharaoh

log = logging.getLogger("pharaoh")
log.setLevel(logging.WARNING)


FMT = logging.Formatter("%(levelname)-7s|%(asctime)s.%(msecs)03d|  %(message)s")


def add_streamhandler():
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(FMT)
    h.name = "pharaoh_sh"
    for hdl in log.handlers:
        if hdl.name == h.name:
            log.removeHandler(hdl)
            break
    log.addHandler(h)


def remove_filehandlers(path: Path):
    for hdl in log.handlers[:]:
        if isinstance(hdl, logging.FileHandler):
            try:
                Path(hdl.baseFilename).relative_to(path)
                log.removeHandler(hdl)
            except ValueError:
                pass


def add_filehandler(path: Path):
    h = logging.FileHandler(path / "log.txt", mode="a", delay=True)
    h.setFormatter(FMT)
    h.name = "pharaoh_fh"
    for hdl in log.handlers:
        if hdl.name == h.name:
            log.removeHandler(hdl)
            break
    log.addHandler(h)


def add_warning_filehandler(path: Path):
    h = logging.FileHandler(path / "log_warnings.txt", mode="a", delay=True)
    h.setFormatter(FMT)
    h.setLevel(logging.WARNING)
    h.name = "pharaoh_fh_warn"
    for hdl in log.handlers:
        if hdl.name == h.name:
            log.removeHandler(hdl)
            break
    log.addHandler(h)


class SphinxLogRedirector:
    ansi_re = re.compile("\x1b\\[(\\d\\d;){0,2}\\d\\dm")

    def __init__(self, level: int):
        self.log_func = {
            logging.DEBUG: log.debug,
            logging.INFO: log.info,
            logging.WARNING: log.warning,
        }[level]

    def write(self, data: str):
        line = self.ansi_re.sub("", data).rstrip()
        if line:
            self.log_func(f"Sphinx Build | {line}")

    def flush(self):
        pass


def log_version_info():
    level = log.level
    log.setLevel(logging.INFO)
    try:
        log.info(f"Pharaoh {pharaoh.__version__} [Python {platform.python_version()}, {platform.platform()}]")
    finally:
        log.setLevel(level)


def log_debug_info():
    envs = dict(os.environ)
    envs.pop("LIBRARY_ROOTS", None)
    envs.pop("_OLD_VIRTUAL_PATH", None)
    level = log.level
    log.setLevel(logging.INFO)
    try:
        log.info(f"Pharaoh version: {pharaoh.__version__}")
        log.info(f"Python Version:  {platform.python_version()}")
        log.info(f"Python Binary:   {sys.executable}")
        log.info(f"System:          {platform.platform()}")
        log.info(f"User:            {getpass.getuser()}")
        log.info(f"Path:            {os.environ.get('PATH', '')}")
        log.info(f"PythonPath:      {os.environ.get('PYTHONPATH', '')}")
    finally:
        log.setLevel(level)


if __name__ == "__main__":
    add_streamhandler()
    log_debug_info()

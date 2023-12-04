from __future__ import annotations

import datetime
import getpass

import omegaconf


def pharaoh_project_dir(*args):
    from pharaoh.api import get_project

    return get_project().project_root.as_posix()


omegaconf.OmegaConf.register_new_resolver(
    name="pharaoh.project_dir",
    resolver=pharaoh_project_dir,
)


omegaconf.OmegaConf.register_new_resolver(
    name="now.strf",
    resolver=lambda fmt: datetime.datetime.now(
        tz=datetime.datetime.now(tz=datetime.timezone.utc).astimezone().tzinfo
    ).strftime(fmt),
)


omegaconf.OmegaConf.register_new_resolver(
    name="user",
    resolver=getpass.getuser,
)

omegaconf.OmegaConf.register_new_resolver(
    name="utcnow.strf",
    resolver=lambda fmt: datetime.datetime.now(tz=datetime.timezone.utc).strftime(fmt),
)

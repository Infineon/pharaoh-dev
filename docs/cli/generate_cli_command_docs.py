import os
from pathlib import Path

from click.testing import CliRunner

from pharaoh.cli import cli

THIS_DIR = Path(__file__).parent


def write_cli_command_doc(command: str):
    filename = command.replace(" ", "_") if command else "default"

    cli_runner = CliRunner()
    result = cli_runner.invoke(cli, f"{command} --help", catch_exceptions=False)

    (THIS_DIR / (filename + ".txt")).write_text(result.stdout, encoding="utf-8")


if __name__ == "__main__":
    cwd = os.getcwd()
    os.chdir(THIS_DIR)
    try:
        for command in [*list(cli.commands.keys()), ""]:
            print(f"Documenting CLI command {command!r}...")
            write_cli_command_doc(command)
    finally:
        os.chdir(cwd)

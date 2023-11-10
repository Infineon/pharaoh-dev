from pathlib import Path

from pharaoh.templating.second_level.template_env import PharaohTemplateEnv


def find_template(template_name: str) -> Path:
    files = list(Path(__file__).parent.glob(template_name + ".*"))
    if not files:
        msg = f"Cannot find template that matches {template_name!r}!"
        raise LookupError(msg)
    if len(files) > 1:
        msg = f"Found multiple matches for {template_name!r}. Please use a more specific name!"
        raise LookupError(msg)
    return files[0]


def render_template(jinja_env: PharaohTemplateEnv, template: str, **kwargs) -> str:
    template_file = Path(template).absolute() if Path(template).absolute().exists() else find_template(template)
    template_content = "\n" + template_file.read_text(encoding="utf-8").strip() + "\n"

    tmpl = jinja_env.from_string(template_content)
    return tmpl.render(**kwargs)

import os
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_FILE = "portfolio_template.html"
_CSS_FILE = "portfolio_style.css"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def generate_portfolio_html(data: dict, output_dir: str = ".", filename: str = "portfolio.html") -> str:
    """Render `data` (the dict returned by ai.get_resume_json) into an
    actual HTML file on disk, alongside its stylesheet.

    Returns the path to the generated portfolio.html.
    """
    template = _env.get_template(_TEMPLATE_FILE)
    html = template.render(**data)

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    css_src = os.path.join(_TEMPLATE_DIR, _CSS_FILE)
    css_dst = os.path.join(output_dir, _CSS_FILE)
    shutil.copyfile(css_src, css_dst)

    return output_path
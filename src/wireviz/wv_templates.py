from pathlib import Path
import jinja2


def get_template(template_name, extension=""):
    template_file_path = jinja2.FileSystemLoader(Path(__file__).parent / "templates")
    jinja_env = jinja2.Environment(loader=template_file_path)

    return jinja_env.get_template(template_name + extension)

import os

from jinja2 import Environment, FileSystemLoader

templates_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))

jinja_env = Environment(
    loader=FileSystemLoader(templates_directory)
)

image_prefix = 'crs'

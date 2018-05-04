from jinja2 import Environment, FileSystemLoader

jinja_env = Environment(
    loader=FileSystemLoader('./templates')
)

image_prefix = 'crs'
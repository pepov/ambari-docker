from ambari_docker.utils import Color

for color in Color:
    print(color.colorize(str(color)))

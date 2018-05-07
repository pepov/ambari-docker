import os
import shutil
import tempfile
import uuid


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


class TempDirectory(object):
    def __init__(self):
        self.path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))

    def __enter__(self):
        os.mkdir(self.path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            shutil.rmtree(self.path, ignore_errors=True)
        except:
            pass

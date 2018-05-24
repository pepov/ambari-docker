import logging
import os
import shutil
import subprocess
import tempfile
import uuid

import requests


def copy_tree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def copy_file(src, dst):
    if os.path.isfile(src):
        shutil.copy(src, dst)
    else:
        raise ValueError(f"'{src}' is not a file")


def download_file(url, destination):
    r = requests.get(url, stream=True)
    with open(destination, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


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


class ProcessRunner(object):
    LOG = logging.getLogger("ProcessRunner")

    def __init__(
            self,
            command_line: str,
            cwd: str = None
    ):
        self.process = subprocess.Popen(
            command_line,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=True,
            cwd=cwd
        )
        self.stream = self.process.stdout

    def communicate(self):
        data = ""
        while self.process.poll() is None:
            line = self.stream.readline().decode()
            self.LOG.debug(line.rstrip())
            data += line
        return data, self.process.returncode

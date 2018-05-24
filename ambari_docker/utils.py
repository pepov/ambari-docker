import enum
import fcntl
import io
import os
import select
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile

import pkg_resources
import requests


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def copy_file(src, dst):
    shutil.copy(src, dst)


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


COLOR_END = '\033[0m'


class Color(enum.Enum):
    # thanks to Shakiba Moshiri, constants provided in stackoverflow post
    # https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux

    # Regular Colors
    Black = '\033[0;30m'  # Black
    Red = '\033[0;31m'  # Red
    Green = '\033[0;32m'  # Green
    Yellow = '\033[0;33m'  # Yellow
    Blue = '\033[0;34m'  # Blue
    Purple = '\033[0;35m'  # Purple
    Cyan = '\033[0;36m'  # Cyan
    White = '\033[0;37m'  # White

    # Bold
    BBlack = '\033[1;30m'  # Black
    BRed = '\033[1;31m'  # Red
    BGreen = '\033[1;32m'  # Green
    BYellow = '\033[1;33m'  # Yellow
    BBlue = '\033[1;34m'  # Blue
    BPurple = '\033[1;35m'  # Purple
    BCyan = '\033[1;36m'  # Cyan
    BWhite = '\033[1;37m'  # White

    # Underline
    UBlack = '\033[4;30m'  # Black
    URed = '\033[4;31m'  # Red
    UGreen = '\033[4;32m'  # Green
    UYellow = '\033[4;33m'  # Yellow
    UBlue = '\033[4;34m'  # Blue
    UPurple = '\033[4;35m'  # Purple
    UCyan = '\033[4;36m'  # Cyan
    UWhite = '\033[4;37m'  # White

    # Background
    On_Black = '\033[40m'  # Black
    On_Red = '\033[41m'  # Red
    On_Green = '\033[42m'  # Green
    On_Yellow = '\033[43m'  # Yellow
    On_Blue = '\033[44m'  # Blue
    On_Purple = '\033[45m'  # Purple
    On_Cyan = '\033[46m'  # Cyan
    On_White = '\033[47m'  # White

    # High Intensity
    IBlack = '\033[0;90m'  # Black
    IRed = '\033[0;91m'  # Red
    IGreen = '\033[0;92m'  # Green
    IYellow = '\033[0;93m'  # Yellow
    IBlue = '\033[0;94m'  # Blue
    IPurple = '\033[0;95m'  # Purple
    ICyan = '\033[0;96m'  # Cyan
    IWhite = '\033[0;97m'  # White

    # Bold High Intensity
    BIBlack = '\033[1;90m'  # Black
    BIRed = '\033[1;91m'  # Red
    BIGreen = '\033[1;92m'  # Green
    BIYellow = '\033[1;93m'  # Yellow
    BIBlue = '\033[1;94m'  # Blue
    BIPurple = '\033[1;95m'  # Purple
    BICyan = '\033[1;96m'  # Cyan
    BIWhite = '\033[1;97m'  # White

    # High Intensity backgrounds
    On_IBlack = '\033[0;100m'  # Black
    On_IRed = '\033[0;101m'  # Red
    On_IGreen = '\033[0;102m'  # Green
    On_IYellow = '\033[0;103m'  # Yellow
    On_IBlue = '\033[0;104m'  # Blue
    On_IPurple = '\033[0;105m'  # Purple
    On_ICyan = '\033[0;106m'  # Cyan
    On_IWhite = '\033[0;107m'  # White

    NoColor = None

    def __init__(self, color_code):
        self.color_code = color_code

    def colorize(self, text: str):
        if self.color_code:
            return self.color_code + text + COLOR_END
        return text


class ProcessRunner(object):
    def __init__(
            self,
            command_line: str,
            cwd: str = None,
            prepend="===> ",
            prepend_color=Color.NoColor,
            text_color=Color.NoColor,
            line_sep="\n",
            silent=False
    ):
        self.process = subprocess.Popen(
            command_line,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            shell=True,
            cwd=cwd
        )
        self.stream = self.process.stdout
        self.prepend = prepend_color.colorize(prepend)
        self.text_color = text_color
        self.output = io.StringIO()
        self.line_sep = line_sep
        self.silent = silent
        self._make_stream_non_blocking()
        self._line_in_progress = False

    def _make_stream_non_blocking(self):
        fd = self.stream.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def _write_to_line(self, data):
        if data:
            if not self._line_in_progress:
                self._line_in_progress = True
                sys.stdout.write(self.prepend)
                sys.stdout.write(self.text_color.color_code)
            if "\r" in data:
                parts = data.split("\r")
                for part_index in range(len(parts)):
                    part = parts[part_index]
                    sys.stdout.write(part)
                    if part_index != len(parts) - 1:
                        sys.stdout.write("\r")
                        sys.stdout.write(COLOR_END)
                        sys.stdout.write(self.prepend)
                        sys.stdout.write(self.text_color.color_code)
                    sys.stdout.flush()
            else:
                sys.stdout.write(data)
                sys.stdout.flush()

    def _begin_new_line(self):
        self._line_in_progress = False
        sys.stdout.write(COLOR_END)
        sys.stdout.write(self.line_sep)

    def _write_to_stdio(self, data):
        if self.line_sep in data:
            parts = data.split(self.line_sep)
            for part_index in range(len(parts)):
                part = parts[part_index]
                self._write_to_line(part)
                if part_index != len(parts) - 1:
                    self._begin_new_line()
        else:
            self._write_to_line(data)

    def communicate(self):
        while self.process.poll() is None:
            ready_read, _, _ = select.select([self.process.stdout], [], [], 1)
            if ready_read:
                stream = ready_read[0]
                data = stream.read().decode()
                self.output.write(data)
                if not self.silent:
                    self._write_to_stdio(data)
        return self.output.getvalue(), self.process.returncode


class StdoutLogger(object):
    def __init__(self, format: str = "{asctime} {levelname}:{message}\n"):
        self.format = format

    def info(self, message):
        _time = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(self.format.format(asctime=_time, levelname="INFO", message=message))

    def debug(self, message):
        _time = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(self.format.format(asctime=_time, levelname="DEBUG", message=message))


class WithDataFiles(object):
    LOG = StdoutLogger()

    def __init__(self, package, data_file):
        self.package = package
        self.data_file = data_file
        self.directory = None

    def __enter__(self):
        self.directory = tempfile.mkdtemp()
        stream = pkg_resources.resource_stream("ambari_docker", 'data.zip')
        zip_ref = zipfile.ZipFile(stream, 'r')
        zip_ref.extractall(self.directory)
        zip_ref.close()
        stream.close()
        self.LOG.info(f"Extracted data files to {self.directory}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            shutil.rmtree(self.directory, ignore_errors=True)
        except:
            pass
        self.LOG.info(f"Cleared data files directory {self.directory}")

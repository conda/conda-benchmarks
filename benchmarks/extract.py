"""
Compare ways to extract conda packages.
"""

import pathlib
import re
import time
from ast import Import, Not
from concurrent.futures.thread import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from threading import Thread
from typing import List

import conda_package_streaming.extract
from conda_package_handling.api import extract
from conda_package_streaming import package_streaming

try:
    from rust_conda import unpack_conda
except ImportError:
    unpack_conda = None

from .test_server import base

MINIMUM_PACKAGES = 10
MAXIMUM_SECONDS = 8.0

STEM_FROM_CONDA = re.compile(r"(?P<stem>.*)(?P<ext>(\.conda|\.tar\.bz2))")


class TrackSuite:
    unit = "speedup"

    def setup(self):
        self.condas = list(base.glob("*.conda"))
        if len(self.condas) < MINIMUM_PACKAGES:
            raise NotImplementedError("Not enough .conda packages in ~/miniconda3/pkgs")

        self.tarbz2 = list(base.glob("*.tar.bz2"))

    def track_streaming_versus_handling(self):
        """
        Compare conda-package-streaming time versus conda-package-handling (should be a number > 1)
        """
        attempted = len(self.condas)
        with TemporaryDirectory(
            "conda-package-streaming"
        ) as streaming, TemporaryDirectory("conda-package-handling") as handling:

            # give faster streaming the cache disadvantage
            begin = time.monotonic()
            # revise self.condas down to the number extracted in no more thanœ
            # MAXIMUM_SECONDS
            self.condas = extract_streaming(streaming, self.condas)
            end = time.monotonic()
            cps_time = end - begin

            actual = len(self.condas)
            print(f"'streaming' extracted {actual} out of {attempted} .conda's")

            begin = time.monotonic()
            self.condas = extract_handling(
                handling, self.condas, time_limit=cps_time * 4
            )
            end = time.monotonic()
            handling_time = end - begin

            actual = len(self.condas)
            print(f"'handling' extracted {actual} out of {attempted} .conda's")

            return handling_time / cps_time

    # could potentially be swapped with env_nobuild in asv.conf instead
    def track_streaming_versus_handling_tarbz2(self):
        """
        Compare conda-package-streaming time versus conda-package-handling (should be a number > 1)
        """
        attempted = len(self.condas)
        with TemporaryDirectory(
            "conda-package-streaming-bz2"
        ) as streaming, TemporaryDirectory("conda-package-handling-bz2") as handling:

            # give faster streaming the cache disadvantage
            begin = time.monotonic()
            # revise self.condas down to the number extracted in no more thanœ
            # MAXIMUM_SECONDS
            self.tarbz2 = extract_streaming(streaming, self.tarbz2)
            end = time.monotonic()
            cps_time = end - begin

            actual = len(self.condas)
            print(f"'streaming' extracted {actual} out of {attempted} .tar.bz2's")

            begin = time.monotonic()
            self.tarbz2 = extract_handling(
                handling, self.tarbz2, time_limit=cps_time * 4
            )
            end = time.monotonic()
            handling_time = end - begin

            actual = len(self.condas)
            print(f"'handling' extracted {actual} out of {attempted} .tar.bz2's")

            return handling_time / cps_time


def u2(package, dest_dir):
    unpack_conda(str(package), str(dest_dir))
    assert pathlib.Path(dest_dir, "info").exists()


class TimeExtract:
    """
    Does threading speed up conda extraction?
    """

    params = [[1, 2, 3, 5, 7], [".conda", ".tar.bz2"], ["py", "rust"]]
    param_names = ["threads", "format", "lang"]

    def setup(self, threads, format, lang):
        if lang == "rust" and format == ".tar.bz2":
            raise NotImplementedError()
        self.td = TemporaryDirectory()

        # could use list from `conda-lock` in case more packages are in base
        self.packages = list(base.glob(f"*{format}"))
        if len(self.packages) < MINIMUM_PACKAGES:
            raise NotImplementedError(f"Not enough packages in {base}")

    def time_extract(self, threads, format, lang):
        if lang == "rust" and unpack_conda is None:
            raise NotImplementedError()
        if lang == "rust" and format == ".tar.bz2":
            raise NotImplementedError()
        extract_fn = {
            "rust": u2,
            "py": conda_package_streaming.extract.extract,
        }[lang]

        with ThreadPoolExecutor(threads) as executor:
            for package in self.packages:
                stem = package.name[: -len(format)]
                dest_dir = pathlib.Path(self.td.name, stem)
                print(package, str(dest_dir))
                executor.submit(extract_fn, package, dest_dir)

    def teardown(self, threads, format, lang):
        if hasattr(self, "td"):
            self.td.cleanup()  # ???


def conda_stem(conda: pathlib.Path):
    match = STEM_FROM_CONDA.match(conda.name)
    if not match:
        raise ValueError("Unsupported extension")
    stem = match.group("stem")
    return stem


def extract_handling(base, condas, time_limit=MAXIMUM_SECONDS):
    """
    Extract a bunch of .conda with conda-package-handling
    """
    limit = time.monotonic()
    extracted = []
    base = pathlib.Path(base)
    for conda in condas:
        stem = conda_stem(conda)
        dest_dir = base / stem
        dest_dir.mkdir(exist_ok=True)
        extract(str(conda), dest_dir)
        extracted.append(conda)
        if time.monotonic() - limit > time_limit:
            break

    return extracted


def extract_streaming(base, condas: List[pathlib.Path], time_limit=MAXIMUM_SECONDS):
    """
    Extract a bunch of .conda with conda-package-streaming
    """
    limit = time.monotonic()
    extracted = []
    base = pathlib.Path(base)
    for conda in condas:
        stem = conda_stem(conda)
        dest_dir = base / stem
        dest_dir.mkdir(exist_ok=True)
        with conda.open(mode="rb") as fp:
            for tar, _member in package_streaming.stream_conda_component(
                str(conda), fp, component="info"
            ):
                tar.extractall(dest_dir)
                break
            if not conda.name.endswith(".tar.bz2"):
                # .tar.bz2's don't filter by component, and would be already
                # extracted
                for tar, _member in package_streaming.stream_conda_component(
                    str(conda), fp, component="pkg"
                ):
                    tar.extractall(dest_dir)
                    break
        extracted.append(conda)
        if time.monotonic() - limit > time_limit:
            break

    return extracted


if __name__ == "__main__":
    # extract to tmp for comparison
    streaming = pathlib.Path("/tmp/conda-streaming")
    handling = pathlib.Path("/tmp/conda-handling")

    streaming.mkdir(exist_ok=True)
    handling.mkdir(exist_ok=True)

    ts = TrackSuite()
    ts.setup()

    # could differ if time runs out...
    extract_streaming(streaming, ts.condas + ts.tarbz2, time_limit=60)
    extract_handling(handling, ts.condas + ts.tarbz2, time_limit=60)

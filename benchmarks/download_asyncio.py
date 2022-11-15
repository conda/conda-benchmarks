"""
https://github.com/conda/conda/issues/11608

Code adapted from shughes-uk

I wrote a hacky little experiment that pre-populates the pkgs cache using asyncio to download packages listed in a conda-lock lockfile. I found it to be much faster than the default conda implementation. I suspect it would be faster than using multiple threads too.

Mostly looking to optimize start time for dask clusters, I can create the environment and wrap it up as a docker image, but it ends up being slower than doing this.

In benchmarking I found this to be as fast or faster than mamba's implementation.
"""

import asyncio
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp
from typing import Dict, List
from urllib.parse import urlparse

import aiofiles
import aiohttp
import conda.exports
import requests
import yaml
from conda_package_handling import api

from . import test_server

log = logging.getLogger(__name__)

PLATFORM = "osx-64"  # adjust based on conda-lock.yml

MAX_WORKERS = 10

cheap = yaml.load(
    (Path(__file__).parent / "../conda-lock.yml").open(), Loader=yaml.SafeLoader
)


def extract(sha256: str, file: str, target: str):
    hasher = hashlib.new("sha256")
    with open(file, "rb") as fh:
        for chunk in iter(partial(fh.read, 8192), b""):
            hasher.update(chunk)
    assert hasher.hexdigest() == sha256
    print("Extracting", file, target)
    api.extract(file, target)


async def main(packages: List[Dict], root: Path):
    async with aiohttp.ClientSession() as session:
        tasks = []
        urls = []
        for package in packages:
            if package["platform"] == PLATFORM and package["manager"] == "conda":
                url = package["url"]
                parsed = urlparse(url)
                pth = Path(parsed.path)
                pth.name
                tasks.append(
                    download_url(
                        sha256=package["hash"]["sha256"],
                        session=session,
                        fp=root / pth.name,
                        url=package["url"],
                    )
                )
                urls.append(url)
        await asyncio.gather(*tasks)
        async with aiofiles.open(root / Path("urls.txt").expanduser(), mode="w") as f:
            for url in urls:
                await f.write(url + "\n")
        async with aiofiles.open(root / Path("urls").expanduser(), mode="w") as f:
            await f.write("\n")


async def download_url(session: aiohttp.ClientSession, sha256: str, fp: Path, url: str):
    log.info("Download %s", url)
    async with session.get(url) as resp:
        async with aiofiles.open(fp, mode="wb") as f:
            async for chunk in resp.content.iter_chunked(10000):
                await f.write(chunk)
    log.info("Finish %s", url)

    loop = asyncio.get_running_loop()
    target_dir = (
        str(fp).removesuffix(".tar.bz2").removesuffix(".tar").removesuffix(".conda")
    )
    # await loop.run_in_executor(p, extract, sha256, str(fp), target_dir)


def add_bz2(packages):
    """
    Augment conda-lock["packages"] with ".tar.bz2" versions of each ".conda"

    To test threading benefits of extracting slower .bz2 format.
    """
    for package in packages:
        yield package
        bz2_url = package["url"].replace(".conda", ".tar.bz2")
        yield {**package, "url": bz2_url}


class TimeDownloadPackages:
    params = [[0.0, 0.01], ["serial", "threads", "aiohttp"]]
    param_names = ["latency", "strategy"]

    def setup(self, latency=0.0, strategy=None):
        self.tempdir = TemporaryDirectory("aiohttp")
        self.temppath = Path(self.tempdir.name)
        log.info("Download to %s", self.tempdir)
        self._port = test_server.run_on_random_port().getsockname()[1]
        requests.get(f"http://127.0.0.1:{self.port}/latency/{latency}")

    def teardown(self, latency=0.0, strategy=None):
        self.tempdir.cleanup()

    @property
    def port(self):
        return self._port

    def setup_cache(self):
        """
        Called once per session.
        self.value = x doesn't work here; benchmarks run in separate processes.
        """
        test_server.base.mkdir(parents=True, exist_ok=True)

        for package in add_bz2(cheap["package"]):
            name = package["url"].rpartition("/")[-1]
            if not (test_server.base / name).exists():
                conda.exports.download(package["url"], test_server.base / name)

    # Not a feature of ASV
    # def teardown_cache(self):
    #     requests.get(f"http://127.0.0.1:{self.port}/shutdown")

    def fixup_urls(self):
        """
        Retarget urls against our local test server.
        """
        port = self.port
        packages = []
        for package in cheap["package"]:
            name = package["url"].rsplit("/", 1)[-1]
            packages.append(
                {**package, "url": f"http://127.0.0.1:{port}/osx-64/{name}"}
            )
        return packages

    def download_aiohttp(self, latency=0.0):
        target_base = Path(mkdtemp(dir=self.temppath))  # no cleanup here
        asyncio.run(main(self.fixup_urls(), target_base))

    def download_serial(self, latency=0.0):
        # does teardown/setup not run for each function in this class
        target_base = Path(mkdtemp(dir=self.temppath))  # no cleanup here
        for package in self.fixup_urls():
            name = package["url"].rsplit("/", 1)[-1]
            target = target_base / name
            assert not target.exists()
            conda.exports.download(package["url"], target)

    def download_threads(self, latency=0.0):
        target_base = Path(mkdtemp(dir=self.temppath))  # no cleanup here
        targets = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as tpe:
            for package in self.fixup_urls():
                name = package["url"].rsplit("/", 1)[-1]
                target = target_base / name
                assert not target.exists()
                targets.append(target)
                tpe.submit(conda.exports.download, package["url"], target)

        assert all(target.exists() for target in targets)

    def time_download_strategy(self, latency, strategy):
        return {
            "aiohttp": self.download_aiohttp,
            "threads": self.download_threads,
            "serial": self.download_serial,
        }[strategy](latency)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    t = TimeDownloadPackages()
    t.setup()
    t.time_download_aiohttp()

"""
Time SubdirData (parses repodata.json) operations.
"""

import os
from pathlib import Path

import conda.exports
from conda.base.context import context, reset_context
from conda.core.subdir_data import SubdirData
from conda.models.channel import Channel

from .test_server import base

REPODATA_FILENAME = base / "osx-64" / "repodata.json"

CONDA_PKGS_DIR = Path(__file__).parents[1] / "env"
CONDA_CACHE_DIR = CONDA_PKGS_DIR / "cache"
CHANNEL_URL = "https://repo.anaconda.com/pkgs/main/osx-64"

MOD_STAMP = {
    "_url": "https://repo.anaconda.com/pkgs/main/osx-64",
    "_etag": 'W/"9cc6a2d13cc0daf168bb2f89712d2305"',
    "_mod": "Fri, 16 Sep 2022 19:48:11 GMT",
    "_cache_control": "public, max-age=30",
}


class SubdirDataNoPickle(SubdirData):
    """
    Don't want to time writing the pickle.
    """

    def _pickle_me(self, *args):
        print("not pickling")
        return None

    def _read_pickled(self, etag, mod_stamp):
        print("not reading pickle")
        return None


class TimeSubdirData:
    def setup(self):
        if not REPODATA_FILENAME.exists():
            REPODATA_FILENAME.parent.mkdir(exist_ok=True)
            # fake out
            (base / "noarch").mkdir(exist_ok=True)
            (base / "noarch" / "repodata.json").write_text("{}")
            (base / "noarch" / "repodata.json.bz2").write_text("")
            # do we have a frozen large-ish repodata.json or can we fake one?
            conda.exports.download(
                "https://repo.anaconda.com/pkgs/main/osx-64/repodata.json",
                REPODATA_FILENAME,
            )

    def time_subdir_data(self):
        channel = Channel(f"file://{base}", platform="osx-64")
        SubdirData.clear_cached_local_channel_data()

        sd_a = SubdirData(channel)
        assert sd_a.query_all("zlib =1.2.11")

    # SubdirData.cache_path_json
    # In [8]: ms = [(k,v) for k,v in json.load(open("./env/cache/7fb2ce72.json")).items() if k.startswith('_')]

    # In [9]: ms
    # Out[9]:
    # [('_url', 'https://repo.anaconda.com/pkgs/main/osx-64'),
    #  ('_etag', 'W/"9cc6a2d13cc0daf168bb2f89712d2305"'),
    #  ('_mod', 'Fri, 16 Sep 2022 19:48:11 GMT'),
    #  ('_cache_control', 'public, max-age=30')]

    def time_load_json(self):
        os.environ["CONDA_PKGS_DIRS"] = str(CONDA_PKGS_DIR)
        os.environ["CONDA_DEFAULT_THREADS"] = "1"
        SubdirData.clear_cached_local_channel_data()
        reset_context()
        context.offline = True
        channel = Channel(CHANNEL_URL)
        subdir = SubdirDataNoPickle(channel)
        subdir._read_local_repdata(MOD_STAMP["_etag"], MOD_STAMP["_mod"])

    def time_load_json_query_one(self):
        os.environ["CONDA_PKGS_DIRS"] = str(CONDA_PKGS_DIR)
        os.environ["CONDA_DEFAULT_THREADS"] = "1"
        SubdirData.clear_cached_local_channel_data()
        reset_context()
        context.offline = True
        channel = Channel(CHANNEL_URL)
        subdir = SubdirDataNoPickle(channel)
        subdir._read_local_repdata(MOD_STAMP["_etag"], MOD_STAMP["_mod"])
        subdir.query("python")

    def time_load_json_query_all(self):
        os.environ["CONDA_PKGS_DIRS"] = str(CONDA_PKGS_DIR)
        os.environ["CONDA_DEFAULT_THREADS"] = "1"
        SubdirData.clear_cached_local_channel_data()
        reset_context()
        context.offline = True
        channel = Channel(CHANNEL_URL)
        subdir = SubdirDataNoPickle(channel)
        subdir._read_local_repdata(MOD_STAMP["_etag"], MOD_STAMP["_mod"])
        subdir.query("[version=1.0]")

    def time_load_pickle(self):
        os.environ["CONDA_PKGS_DIRS"] = str(CONDA_PKGS_DIR)
        os.environ["CONDA_DEFAULT_THREADS"] = "1"
        SubdirData.clear_cached_local_channel_data()
        reset_context()
        context.offline = True
        channel = Channel(CHANNEL_URL)
        sd = SubdirData(channel)
        sd._read_pickled(MOD_STAMP["_etag"], MOD_STAMP["_mod"])

    def time_save_pickle(self):
        os.environ["CONDA_PKGS_DIRS"] = str(CONDA_PKGS_DIR)
        os.environ["CONDA_DEFAULT_THREADS"] = "1"
        SubdirData.clear_cached_local_channel_data()
        reset_context()
        context.offline = True
        channel = Channel(CHANNEL_URL)
        sd = SubdirData(channel)
        sd._pickle_me()


if __name__ == "__main__":
    TimeSubdirData().time_subdir_data()

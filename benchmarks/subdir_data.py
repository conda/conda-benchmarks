"""
Time SubdirData (parses repodata.json) operations.
"""

import inspect
import os
from pathlib import Path

import conda.exports
from conda.base.context import context, reset_context
from conda.core.subdir_data import SubdirData
from conda.models.channel import Channel

from .conda_install import timeme
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


# as of 2023-01-06
# probably stop benchmarking EXPECTS_DICT=False
EXPECTS_DICT = "state" in inspect.signature(SubdirData._read_pickled).parameters


class SubdirDataNoPickle(SubdirData):
    """
    Don't want to time writing the pickle.
    """

    def _pickle_me(self, *args):
        print("not pickling")
        return None

    def _read_local_repdata(self, state):
        return super()._read_local_repodata(state)

    if EXPECTS_DICT:

        def _read_pickled(self, state):
            print("not reading pickle")
            return None

    else:

        def _read_pickled(self, etag, mod_stamp):
            print("not reading pickle")
            return None


class TimeSubdirData:
    def setup(self):
        self.set_environ()
        reset_context()

        print(f"Ensure {REPODATA_FILENAME}")
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

    def channel(self):
        return Channel.from_url(f"file://{base}/osx-64")

    def clear_cache(self):
        """
        Remove in-memory SubdirData cached objects. Keep disk cache.
        """
        # doesn't clear out file://
        # SubdirData.clear_cached_local_channel_data()
        SubdirData._cache_.clear()

    def time_subdir_data(self):
        self.set_environ()
        reset_context()

        channel = self.channel()
        assert channel.platform == "osx-64"

        self.clear_cache()

        sd_a = SubdirData(channel)
        # load() and reload() don't appear to check _loaded; redundant methods?
        # sd_a.load()
        print(f"Should save to {sd_a.cache_path_json}")

        # could check sd_a.cache_path_json
        # may have changed from older code, not honoring CONDA_CACHE_DIR?
        zlib = list(sd_a.query("zlib =1.2.11"))
        assert len(zlib) > 0
        # query_all (static method) doesn't load *this* SubdirData by itself?
        # query_all calls query() on a list of SubdirData.
        assert sd_a._loaded

    # SubdirData.cache_path_json
    # In [8]: ms = [(k,v) for k,v in json.load(open("./env/cache/7fb2ce72.json")).items() if k.startswith('_')]

    # In [9]: ms
    # Out[9]:
    # [('_url', 'https://repo.anaconda.com/pkgs/main/osx-64'),
    #  ('_etag', 'W/"9cc6a2d13cc0daf168bb2f89712d2305"'),
    #  ('_mod', 'Fri, 16 Sep 2022 19:48:11 GMT'),
    #  ('_cache_control', 'public, max-age=30')]

    def time_load_json(self):
        self.set_environ()
        self.clear_cache()
        reset_context()
        context.offline = True
        channel = self.channel()
        subdir = SubdirDataNoPickle(channel)
        print(f"Should load from {subdir.cache_path_json}")
        print(
            len(
                # [sic] the function is called repdata not repodata, since a long time ago
                subdir._read_local_repdata(
                    {"_etag": MOD_STAMP["_etag"], "_mod": MOD_STAMP["_mod"]}
                )["_package_records"]
            ),
            "package records",
        )

    def set_environ(self):
        os.environ["CONDA_PKGS_DIRS"] = str(CONDA_PKGS_DIR)
        os.environ["CONDA_DEFAULT_THREADS"] = "1"

    def time_load_json_query_one(self):
        self.set_environ()

        self.clear_cache()
        reset_context()
        context.offline = True
        channel = self.channel()
        subdir = SubdirDataNoPickle(channel)
        subdir._read_local_repdata(
            {"_etag": MOD_STAMP["_etag"], "_mod": MOD_STAMP["_mod"]}
        )
        subdir.query("python")

    def time_load_json_query_all(self):
        self.set_environ()

        self.clear_cache()
        reset_context()
        context.offline = True
        channel = self.channel()
        subdir = SubdirDataNoPickle(channel)
        subdir._read_local_repdata(
            {"_etag": MOD_STAMP["_etag"], "_mod": MOD_STAMP["_mod"]}
        )
        subdir.query("[version=1.0]")

    def time_load_pickle(self):
        self.set_environ()

        self.clear_cache()
        reset_context()
        context.offline = True
        channel = self.channel()
        sd = SubdirData(channel)
        sd._read_pickled({"_etag": MOD_STAMP["_etag"], "_mod": MOD_STAMP["_mod"]})

    def time_save_pickle(self):
        self.set_environ()

        self.clear_cache()
        reset_context()
        context.offline = True
        channel = self.channel()
        sd = SubdirData(channel)
        sd._pickle_me()


if __name__ == "__main__":
    tsd = TimeSubdirData()
    with timeme("setup "):
        tsd.setup()
    with timeme("subdir_data "):
        tsd.time_subdir_data()
    with timeme("load_json "):
        tsd.time_load_json()

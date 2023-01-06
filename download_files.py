import os
import sys
import shutil
from six.moves import urllib
from conda.exports import subdir
from conda.common.io import env_vars
from conda.cli import python_api

pkgs_dir = os.path.join(sys.prefix, "pkgs")

channel_map = {
    "free": "https://repo.anaconda.com/pkgs/free",
    "main": "https://repo.anaconda.com/pkgs/main",
    "r": "https://repo.anaconda.com/pkgs/r",
    "conda-forge": "https://conda.anaconda.org/conda-forge",
    "bioconda": "https://conda.anaconda.org/bioconda",
}


with env_vars(
    {
        "CONDA_PKGS_DIRS": os.path.join("repos", "main", subdir),
    }
):
    try:
        python_api.run_command(
            "create", "-n", "fakeenv", "--download-only", "python=3.6", "mkl"
        )
    except:
        pass
    if sys.platform != "win32":
        try:
            python_api.run_command(
                "create", "-n", "fakeenv", "--download-only", "libopenblas"
            )
        except:
            pass

for chan, url in channel_map.items():
    for _subdir in (subdir, "noarch"):
        subdir_path = os.path.join("repos", chan, _subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
        for fn in (
            "repodata.json",
            "repodata.json.bz2",
            "current_repodata.json",
            "current_repodata.json.bz2",
        ):
            try:
                urllib.request.urlretrieve(
                    "%s/%s/%s" % (url, _subdir, fn), os.path.join(subdir_path, fn)
                )
            except urllib.error.HTTPError as e:
                print(url, _subdir, fn, e)

        # remove subdirs (extracted packages - we want to include package extraction in timing)
        for _, dirs, _ in os.walk(subdir_path):
            for dirname in dirs:
                shutil.rmtree(os.path.join(subdir_path, dirname))

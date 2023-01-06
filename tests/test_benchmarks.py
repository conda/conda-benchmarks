"""
This test is a bit of a broken mess, having been written years ago for older
dependencies etc.
"""

import os
import sys
import random
import string
from pathlib import Path
import pytest

# subdir = 'linux-64'
# os.environ['CONDA_SUBDIR'] = subdir

from unittest.mock import patch


def execute_conda_cmd(args):
    from conda.cli import main
    from conda.base.context import reset_context

    reset_context()
    with patch.object(sys, "argv", args):
        return main()


def random_env_name(N=10):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(N)
    )


CLEAN_INDEX_ARGS = ["conda", "clean", "-iy"]
CREATE_ARGS = ["conda", "create"]
SOLVE_ARGS = CREATE_ARGS + [
    "--override-channels",
    "--offline",
    "--dry-run",
    "-n",
    random_env_name(),
]
SOLVER_DEFAULT = "classic"


def paramaterize_solver(test):
    """
    Add asv test parameters to function.
    """
    test.params = ["classic", "libmamba"]
    return test


thisdir = os.path.dirname(__file__)
repos_dir = os.path.join(os.path.dirname(thisdir), "repos")


assert Path(
    repos_dir, "main", "osx-64", "bzip2-1.0.8-h1de35cc_0.conda"
).exists(), "run CONDA_SUBDIR=osx-64 python3 download_files.py"


def channel_url(name):
    return "/".join(["file:/", repos_dir, name])


main = channel_url("main")
free = channel_url("free")
r = channel_url("r")
conda_forge = channel_url("conda-forge")
bioconda = channel_url("bioconda")


@pytest.mark.benchmark
@paramaterize_solver
def test_solve_anaconda_53(solver=SOLVER_DEFAULT):
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(SOLVE_ARGS + [f"--solver={solver}", "-c", main, "anaconda=5.3.0"])


if True:
    # problems with free channel: conda looks for current_repodata.json

    @pytest.mark.benchmark
    @paramaterize_solver
    def test_solve_anaconda_44(solver=SOLVER_DEFAULT):
        execute_conda_cmd(CLEAN_INDEX_ARGS)
        execute_conda_cmd(
            SOLVE_ARGS
            + [f"--solver={solver}", "-c", main, "-c", free, "anaconda=4.4.0"]
        )

    @pytest.mark.benchmark
    @paramaterize_solver
    def test_solve_anaconda_44_free_only(solver=SOLVER_DEFAULT):
        execute_conda_cmd(CLEAN_INDEX_ARGS)
        execute_conda_cmd(
            SOLVE_ARGS + [f"--solver={solver}", "-c", free, "anaconda=4.4.0"]
        )


@pytest.mark.benchmark
@paramaterize_solver
def test_solve_r_essentials_r_base_defaults(solver=SOLVER_DEFAULT):
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(
        SOLVE_ARGS
        + [f"--solver={solver}", "-c", main, "-c", r, "r-essentials", "r-base"]
    )


@pytest.mark.benchmark
@paramaterize_solver
def test_solve_r_essentials_r_base_conda_forge(solver=SOLVER_DEFAULT):
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(
        SOLVE_ARGS
        + [
            f"--solver={solver}",
            "-c",
            conda_forge,
            "-c",
            main,
            "-c",
            r,
            "r-essentials",
            "r-base",
        ]
    )


# @pytest.mark.benchmark
# def test_solve_r_essentials_r_base_conda_forge_bioconda():
#    assert 1==execute_conda_cmd(CLEAN_INDEX_ARGS)
#    assert 1==execute_conda_cmd(SOLVE_ARGS + ['-c', bioconda, '-c', conda_forge, '-c', main, '-c', r,
#                                    'r-essentials', 'r-base'])


@pytest.mark.benchmark
@paramaterize_solver
def test_create_python(solver=SOLVER_DEFAULT):
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(
        CREATE_ARGS
        + [
            f"--solver={solver}",
            "-y",
            "-n",
            random_env_name(),
            "-c",
            main,
            "python=3.6",
        ]
    )


@pytest.mark.benchmark
@paramaterize_solver
def test_create_python_boost(solver=SOLVER_DEFAULT):
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(
        CREATE_ARGS
        + [
            f"--solver={solver}",
            "-y",
            "-n",
            random_env_name(),
            "-c",
            main,
            "python=3.6",
            "libboost",
        ]
    )


@pytest.mark.benchmark
@paramaterize_solver
def test_create_numpy_openblas(solver=SOLVER_DEFAULT):
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(
        CREATE_ARGS
        + [
            f"--solver={solver}",
            "-y",
            "-n",
            random_env_name(),
            "-c",
            main,
            "python=3.6",
            "numpy=1.15.2",
            "nomkl",
        ]
    )


@pytest.mark.benchmark
@paramaterize_solver
def test_create_numpy_mkl(solver=SOLVER_DEFAULT):
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(
        CREATE_ARGS
        + [
            f"--solver={solver}",
            "-y",
            "-n",
            random_env_name(),
            "-c",
            main,
            "python=3.6",
            "numpy=1.15.2",
        ]
    )

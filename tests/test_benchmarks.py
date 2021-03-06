import os
import sys
import shutil
import random
import string

import pytest

# subdir = 'linux-64'
# os.environ['CONDA_SUBDIR'] = subdir

try:
    # python 3.4+ should use builtin unittest.mock not mock package
    from unittest.mock import patch
except ImportError:
    from mock import patch

def execute_conda_cmd(args):
    from conda.cli import main
    with patch.object(sys, 'argv', args):
        return main()


def random_env_name(N=10):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))


CLEAN_INDEX_ARGS = ['conda', 'clean', '-iy']
CREATE_ARGS = ['conda', 'create']
SOLVE_ARGS = CREATE_ARGS + ['--dry-run', '-n', random_env_name()]

thisdir = os.path.dirname(__file__)
repos_dir = os.path.join(os.path.dirname(thisdir), 'repos')

def channel_url(name):
    return '/'.join(['file:/', repos_dir, name])

main = channel_url('main')
free = channel_url('free')
r = channel_url('r')
conda_forge = channel_url('conda-forge')
bioconda = channel_url('bioconda')


@pytest.mark.benchmark
def test_solve_anaconda_53():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(SOLVE_ARGS + ['-c', main, 'anaconda=5.3.0'])


@pytest.mark.benchmark
def test_solve_anaconda_44():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(SOLVE_ARGS + ['-c', main, '-c', free, 'anaconda=4.4.0'])


@pytest.mark.benchmark
def test_solve_anaconda_44_free_only():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(SOLVE_ARGS + ['-c', free, 'anaconda=4.4.0'])


@pytest.mark.benchmark
def test_solve_r_essentials_r_base_defaults():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(SOLVE_ARGS + ['-c', main, '-c', r, 'r-essentials', 'r-base'])


@pytest.mark.benchmark
def test_solve_r_essentials_r_base_conda_forge():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(SOLVE_ARGS + ['-c', conda_forge, '-c', main, '-c', r,
                                    'r-essentials', 'r-base'])


#@pytest.mark.benchmark
#def test_solve_r_essentials_r_base_conda_forge_bioconda():
#    execute_conda_cmd(CLEAN_INDEX_ARGS)
#    execute_conda_cmd(SOLVE_ARGS + ['-c', bioconda, '-c', conda_forge, '-c', main, '-c', r,
#                                    'r-essentials', 'r-base'])


@pytest.mark.benchmark
def test_create_python():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(CREATE_ARGS + ['-y', '-n', random_env_name(), '-c', main, 'python=3.6'])


@pytest.mark.benchmark
def test_create_python_boost():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(CREATE_ARGS + ['-y', '-n', random_env_name(),  '-c', main, 'python=3.6', 'libboost'])


@pytest.mark.benchmark
def test_create_numpy_openblas():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(CREATE_ARGS + ['-y', '-n', random_env_name(),  '-c', main, 'python=3.6', 'numpy=1.15.2', 'nomkl'])


@pytest.mark.benchmark
def test_create_numpy_mkl():
    execute_conda_cmd(CLEAN_INDEX_ARGS)
    execute_conda_cmd(CREATE_ARGS + ['-y', '-n', random_env_name(),  '-c', main, 'python=3.6', 'numpy=1.15.2'])

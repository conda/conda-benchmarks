import os
import sys

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


CREATE_ARGS = ['conda', 'create', '-n', 'test_env']
SOLVE_ARGS = CREATE_ARGS + ['--dry-run']

thisdir = os.path.dirname(__file__)
repos_dir = os.path.join(os.path.dirname(thisdir), 'repos')

def channel_url(name):
    return '/'.join(['file:/', repos_dir, name])

main = channel_url('main')
free = channel_url('free')
r = channel_url('r')
conda_forge = channel_url('conda-forge')
bioconda = channel_url('bioconda')


def test_solve_anaconda_53():
    execute_conda_cmd(SOLVE_ARGS + ['-c', main, 'anaconda=5.3.0'])


def test_solve_anaconda_44():
    execute_conda_cmd(SOLVE_ARGS + ['-c', main, '-c', free, 'anaconda=4.4.0'])


def test_solve_anaconda_44_free_only():
    execute_conda_cmd(SOLVE_ARGS + ['-c', free, 'anaconda=4.4.0'])


def test_solve_r_essentials_r_base_defaults():
    execute_conda_cmd(SOLVE_ARGS + ['-c', main, '-c', r, 'r-essentials', 'r-base'])


def test_solve_r_essentials_r_base_conda_forge():
    execute_conda_cmd(SOLVE_ARGS + ['-c', conda_forge, '-c', main, '-c', r,
                                    'r-essentials', 'r-base'])


def test_solve_r_essentials_r_base_conda_forge_bioconda():
    execute_conda_cmd(SOLVE_ARGS + ['-c', bioconda, '-c', conda_forge, '-c', main, '-c', r,
                                    'r-essentials', 'r-base'])


def test_create_python():
    execute_conda_cmd(CREATE_ARGS + ['-y', '-c', main, 'python=3.6'])


def test_create_python_boost():
    execute_conda_cmd(CREATE_ARGS + ['-y', '-c', main, 'python=3.6', 'libboost'])


def test_create_numpy_openblas():
    execute_conda_cmd(CREATE_ARGS + ['-y', '-c', main, 'python=3.6', 'numpy=1.15.2', 'nomkl'])


def test_create_numpy_mkl():
    execute_conda_cmd(CREATE_ARGS + ['-y', '-c', main, 'python=3.6', 'numpy=1.15.2'])

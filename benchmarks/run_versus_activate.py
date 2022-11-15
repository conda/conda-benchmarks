"""
conda run is much slower than conda activate (https://github.com/conda/conda/issues/11814)
"""


def time_conda_run():
    """
    May need to be string form of benchmark to catch import times?
    """
    from conda.testing.helpers import run_inprocess_conda_command

    run_inprocess_conda_command(
        "conda run -n base python -V",
        disallow_stderr=False,
    )

#!/usr/bin/env python
import benchmarks.conda_install


def go():
    ti = benchmarks.conda_install.TimeInstall()
    ti.setup(10, 0, server=True)

    # this multithreaded profiler is easier to use in pycharm
    # yappi.set_clock_type("wall")
    # yappi.start()

    ti.time_explicit_install(10, 0)

    # yappi.stop()


if __name__ == "__main__":
    go()

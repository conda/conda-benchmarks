# Conda Benchmarking

This is what Anaconda uses to benchmark the conda project.  It is only set up
on OSX-64 right now.  To run the benchmarks, first run the download_files.py
script, then run asv with your desired options.

## Quickstart

```bash
$> conda create -n conda-benchmarks -c conda-forge python=3.9 conda asv six pytest
$> conda activate conda-benchmarks
$> python download_files.py
$> asv machine --yes
$> asv dev  # quick run
```

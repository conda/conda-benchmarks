import os
import sys
import shutil
from six.moves import urllib

pkgs = []
with open('flist') as f:
    for line in f.readlines():
        name, version = line.split(":")
        fn = name.strip() + '-' + version.strip() + '.tar.bz2'
        pkgs.append(fn)

pkgs_dir = os.path.join(sys.prefix, 'pkgs')


def download_package(channel, subdir, fn, pkg_cache_dir, force=False):
    cache_folder = os.path.join(pkg_cache_dir, subdir)
    if not os.path.isdir(cache_folder):
        os.makedirs(cache_folder)
    if not os.path.isfile(os.path.join(cache_folder, fn)) and not force:
        print('Downloading %s' % fn)
        urllib.request.urlretrieve(
            "%s/%s/%s" % (channel, subdir, fn),
            os.path.join(cache_folder, fn))


for fn in pkgs:
    download_package('https://repo.anaconda.com/pkgs/main', 'osx-64', fn,
                     os.path.join('repos', 'main'))

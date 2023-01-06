import os
from pprint import pprint
import sys

benchmarks_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.dirname(benchmarks_dir)
test_dir = os.path.join(root_dir, "tests")
sys.path.insert(0, test_dir)
sys.path.insert(0, benchmarks_dir)

from utils import add_test_funcs_to_module, add_renamed_classes_to_module


this_module_name = os.path.splitext(__file__.split(os.path.sep)[-1])[0]
repl_name = this_module_name.split("_")[0]
this_module = __import__(this_module_name)

if sys.version_info.major >= 3:
    sys.modules["benchmarks"] = __import__("benchmarks")
    sys.modules["benchmarks." + this_module_name] = this_module
else:
    raise ValueError("I don't know how to do this with py27 (yet?)")


print("Module name is: {}".format(this_module_name))

add_test_funcs_to_module(this_module, repl_name)
add_renamed_classes_to_module(this_module, repl_name)

del os
del sys
del add_renamed_classes_to_module
del add_test_funcs_to_module

print("Final modified module dict:")
pprint(this_module.__dict__)

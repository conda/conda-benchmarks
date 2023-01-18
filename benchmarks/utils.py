import ast
import functools
from glob import glob
import inspect
import json
import os
from pprint import pprint
import sys
import types
from importlib import __import__  # NOQA


# https://stackoverflow.com/a/31197273/1170370
def _get_decorators(cls):
    target = cls
    decorators = {}

    def visit_FunctionDef(node):
        decorators[node.name] = []
        for n in node.decorator_list:
            name = ""
            if isinstance(n, ast.Call):
                name = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
            else:
                name = n.attr if isinstance(n, ast.Attribute) else n.id

            decorators[node.name].append(name)

    node_iter = ast.NodeVisitor()
    node_iter.visit_FunctionDef = visit_FunctionDef
    node_iter.visit(ast.parse(inspect.getsource(target)))
    return decorators


_thisdir = os.path.dirname(__file__)
test_dir = os.path.join(os.path.dirname(_thisdir), "tests")

flist = os.path.join(_thisdir, "benchmark_files.json")
if os.path.exists(flist):
    with open(flist) as f:
        flist = json.load(f)
else:
    flist = []


def _parse_ast(filename):
    with open(filename, "rt") as file:
        return ast.parse(file.read(), filename=filename)


def _is_test_func(ast_entry):
    return isinstance(ast_entry, ast.FunctionDef) and ast_entry.name.startswith("test_")


def _import_test_module(test_file_path):
    test_module_name = os.path.splitext(os.path.basename(test_file_path))[0]
    test_dir = os.path.dirname(test_file_path)
    if test_dir not in sys.path:
        sys.path.insert(0, test_dir)
    return __import__(test_module_name)


# ======================================================================
#      function-based test suites (pytest style)
# ======================================================================


# https://stackoverflow.com/a/31005891/1170370
def _top_level_functions(body, module):
    test_funcs = [f.name for f in body if _is_test_func(f)]
    benchmark_funcs = {}
    if test_funcs:
        benchmark_funcs = _get_decorators(module)
    return [
        f
        for f, decorators in benchmark_funcs.items()
        if ("benchmark" in decorators and f in test_funcs)
    ]


def _list_test_functions(filename):
    mod_ast = _parse_ast(filename)
    return _top_level_functions(mod_ast.body, _import_test_module(filename))


# https://stackoverflow.com/a/13503277/1170370
def _copy_func(f):
    """Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)"""
    g = types.FunctionType(
        f.__code__,
        f.__globals__,
        name=f.__name__,
        argdefs=f.__defaults__,
        closure=f.__closure__,
    )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


def _add_renamed_functions_from_test_file(dest_module, test_file_path, repl_name):
    # assumes that origin module is similarly named to dest module, just with
    #     test_* instead of time_* or mem_*
    test_module = _import_test_module(test_file_path)
    funcs = _list_test_functions(test_file_path)
    dest_module_name = os.path.splitext(os.path.basename(dest_module.__file__))[0]

    print("Found functions in {}".format(test_file_path))
    pprint(funcs)
    for func in funcs:
        new_func_name = func.replace("test", repl_name, 1)
        new_func = _copy_func(getattr(sys.modules[test_module.__name__], func))
        new_func.__name__ = new_func_name

        print("Adding function {} to module {}".format(new_func_name, dest_module_name))
        setattr(sys.modules[dest_module.__name__], new_func_name, new_func)


def add_test_funcs_to_module(module, repl_name):
    for test_file in glob(os.path.join(test_dir, "test_*.py")):
        if not flist or os.path.basename(test_file) in flist:
            _add_renamed_functions_from_test_file(module, test_file, repl_name)


# ======================================================================
#      class-based test suites (unittest style)
# ======================================================================


# https://stackoverflow.com/a/31005891/1170370
def _top_level_test_classes(mod_ast):
    return [
        f.name
        for f in mod_ast.body
        if (
            isinstance(f, ast.ClassDef)
            and any(_is_test_func(inner_f) for inner_f in f.body)
        )
    ]


def _list_classes_with_test_methods(filename):
    body = _parse_ast(filename)
    return _top_level_test_classes(body)


def _reclassify_test(klass, new_prefix, benchmark_funcs):
    new_attrs = {}
    for attr, val in klass.__dict__.items():
        if attr.startswith("test_") and attr in benchmark_funcs:
            new_attrs[attr.replace("test", new_prefix, 1)] = val
        else:
            new_attrs[attr] = val
    return new_attrs


def _add_renamed_classes_from_test_file(dest_module, test_file_path, repl_name):
    test_module = _import_test_module(test_file_path)
    class_names = _list_classes_with_test_methods(test_file_path)
    dest_module_name = os.path.splitext(os.path.basename(dest_module.__file__))[0]
    print("Found classes in {}".format(test_file_path))
    pprint(class_names)
    for cls_name in class_names:
        new_class_name = repl_name.capitalize() + cls_name
        old_class = getattr(test_module, cls_name)
        benchmark_funcs = {
            k: v for k, v in _get_decorators(old_class).items() if "benchmark" in v
        }
        if benchmark_funcs:
            attrs = _reclassify_test(old_class, repl_name, benchmark_funcs)
            print(
                "Adding class {} to module {} with attrs:".format(
                    new_class_name, dest_module_name
                )
            )
            pprint(attrs)
            setattr(
                sys.modules[dest_module.__name__],
                new_class_name,
                type(new_class_name, (old_class,), attrs),
            )


def add_renamed_classes_to_module(module, repl_name):
    for test_file in glob(os.path.join(test_dir, "test_*.py")):
        if not flist or os.path.basename(test_file) in flist:
            _add_renamed_classes_from_test_file(module, test_file, repl_name)

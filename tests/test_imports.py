import importlib
import pkgutil
import pytest

import parseanything

def test_all_imports():
    """
    Smoke test to ensure all modules in parseanything can be imported without errors.
    """
    package = parseanything
    prefix = package.__name__ + "."
    
    # Recursively find and import all modules
    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        importlib.import_module(modname)

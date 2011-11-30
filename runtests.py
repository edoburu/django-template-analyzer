#!/usr/bin/env python

# Django environment setup:
from django.conf import settings
from os.path import abspath, basename, dirname, exists, isdir, join, realpath
import sys, os

# Detect location and available modules
module_root = dirname(realpath(__file__))
module_names = [name for name in os.listdir(module_root) if isdir(join(module_root, name)) and not name[0] == '.' and exists(join(module_root, name, "models.py"))]
sys.stderr.write("Running tests for modules: {0}\n".format(', '.join(module_names)))

# Inline settings file
settings.configure(
    DEBUG = True,
    TEMPLATE_DEBUG = True,
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    },
    TEMPLATE_LOADERS = (
        'django.template.loaders.app_directories.Loader',
    ),
    INSTALLED_APPS = module_names,
)


# ---- app start

from django.test.utils import get_runner
TestRunner = get_runner(settings)
runner = TestRunner(verbosity=1, interactive=True, failfast=False)
failures = runner.run_tests(module_names)

if failures:
    sys.exit(bool(failures))

#!/usr/bin/env python
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

if not settings.configured:
    if django.VERSION >= (1, 8):
        template_settings = dict(
            TEMPLATES = [
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': (),
                    'OPTIONS': {
                        'loaders': (
                            'django.template.loaders.filesystem.Loader',
                            'django.template.loaders.app_directories.Loader',
                            #added dynamically: 'template_analyzer.tests.app_loader.Loader',
                        ),
                    },
                },
            ]
        )
    else:
        template_settings = dict(
            TEMPLATE_DEBUG = True,
            TEMPLATE_LOADERS = (
                'django.template.loaders.app_directories.Loader',
                'template_analyzer.tests.app_loader.Loader',
            )
        )

    settings.configure(
        DEBUG = True,
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        INSTALLED_APPS = (
            'template_analyzer',
        ),
        MIDDLEWARE_CLASSES = (),
        **template_settings
    )

def runtests():
    argv = sys.argv[:1] + ['test', 'template_analyzer', '--traceback'] + sys.argv[1:]
    execute_from_command_line(argv)

if __name__ == '__main__':
    runtests()

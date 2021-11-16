#!/usr/bin/env python
import sys

import django
from django.conf import settings
from django.core.management import execute_from_command_line

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=("template_analyzer",),
        MIDDLEWARE=(),
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": (),
                "OPTIONS": {
                    "loaders": (
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                        # added dynamically: 'template_analyzer.tests.app_loader.Loader',
                    ),
                },
            },
        ],
    )


def runtests():
    argv = sys.argv[:1] + ["test", "template_analyzer", "--traceback"] + sys.argv[1:]
    execute_from_command_line(argv)


if __name__ == "__main__":
    runtests()

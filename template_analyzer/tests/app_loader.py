"""
Based on:
* https://github.com/django-admin-tools/django-admin-tools/blob/master/admin_tools/template_loaders.py
* https://bitbucket.org/tzulberti/django-apptemplates/
* http://djangosnippets.org/snippets/1376/

Django template loader that allows you to load a template from a
specific application. This allows you to both extend and override
a template at the same time. The default Django loaders require you
to copy the entire template you want to override, even if you only
want to override one small block.

Template usage example::
    {% extends "admin:admin/base.html" %}
"""
import django
from os.path import dirname, join, abspath

from django.conf import settings
from django.template.loaders.filesystem import Loader as FilesystemLoader

try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module  # Python 2.6

_cache = {}


def get_app_template_dir(app_name):
    """Get the template directory for an application

    Uses apps interface available in django 1.7+

    Returns a full path, or None if the app was not found.
    """
    if app_name in _cache:
        return _cache[app_name]
    template_dir = None

    if django.VERSION >= (1, 7):
        from django.apps import apps
        for app in apps.get_app_configs():
            if app.label == app_name:
                template_dir = join(app.path, 'templates')
                break
    else:
        for app in settings.INSTALLED_APPS:
            if app.split('.')[-1] == app_name:
                # Do not hide import errors; these should never happen at this point
                # anyway
                mod = import_module(app)
                template_dir = join(abspath(dirname(mod.__file__)), 'templates')
                break

    _cache[app_name] = template_dir
    return template_dir


class Loader(FilesystemLoader):
    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        """
        Returns the absolute paths to "template_name" in the specified app.
        If the name does not contain an app name (no colon), an empty list
        is returned.
        The parent FilesystemLoader.load_template_source() will take care
        of the actual loading for us.
        """
        if ':' not in template_name:
            return []
        app_name, template_name = template_name.split(":", 1)
        template_dir = get_app_template_dir(app_name)
        if template_dir:
            if django.VERSION >= (1, 9):
                from django.template import Origin
                origin = Origin(
                    name=join(template_dir, template_name),
                    template_name=template_name,
                    loader=self,
                )
            else:
                origin = join(template_dir, template_name)
            return [origin]
        return []

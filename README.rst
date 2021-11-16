django-template-analyzer
========================

.. image:: https://github.com/edoburu/django-template-analyzer/actions/workflows/tests.yaml/badge.svg?branch=master
    :target: https://github.com/edoburu/django-template-analyzer/actions/workflows/tests.yaml
.. image:: https://img.shields.io/pypi/v/django-template-analyzer.svg
    :target: https://pypi.python.org/pypi/django-template-analyzer/
.. image:: https://img.shields.io/badge/wheel-yes-green.svg
    :target: https://pypi.python.org/pypi/django-template-analyzer/
.. image:: https://img.shields.io/codecov/c/github/edoburu/django-template-analyzer/master.svg
    :target: https://codecov.io/github/edoburu/django-template-analyzer?branch=master

The ``template_analyzer`` package offers an API to analyze the Django template structure.
It can be used to find nodes of a particular type, e.g. to do automatic detection of placeholder tags.

Supported features
==================

The scanner finds tags in various situations, including:

* Extend nodes
* Include nodes
* Overwritten blocks with new definitions
* Blocks with or without ``{{ block.super }}``
* Reorganized blocks
* Ignoring nodes outside blocks in extending templates
* Handling multiple levels of super includes

The returned nodes are provided in a natural ordering,
as they would be expected to appear in the outputted page.

While Django offers a ``template.nodelist.get_nodes_of_type()`` function,
this function does not produce the same results.


API example
===========

.. code-block:: python

    from django.template.loader import get_template
    from mycms.templatetags.placeholdertags import Placeholder
    from template_analyzer.djangoanalyzer import get_node_instances

    # Load a Django template
    template = get_template("mycms/default-page.html")

    # Find all tags in the template:
    placeholders = get_node_instances(template, Placeholder)

    # Read information from the template tag themselves:
    # (this is an example, accessing a custom method on the Placeholder object)
    placeholder_names = [p.get_name() for p in placeholders]

Installation
============

First install the module, preferably in a virtual environment. It can be installed from PyPI::

    pip install django-template-analyzer

Or the current folder can be installed::

    pip install .

Credits
=======

* This package is based on the work of
  `Django CMS <http://www.django-cms.org>`_. 
* Many thanks to the contributors of ``cms/utils/placeholder.py`` / ``cms/utils/plugins.py`` in Django CMS!

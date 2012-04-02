Introduction
============

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

::

    from template_analyzer.djangoanalyzer import get_node_instances
    from mycms.templatetags.placeholdertags import Placeholder

    template = get_template("mycms/default-page.html")

    placeholders = get_node_instances(template, Placeholder)
    placeholder_names = [p.get_name() for p in placeholders]

Installation
============

First install the module, preferably in a virtual environment. It can be installed from PyPI::

    pip install django-template-analyzer

Or the current folder can be installed::

    pip install .

Changelog
=========

Version 1.1: added Django 1.4 compatibility.
Version 1.0: initial release.

Credits
=======

* This package is based on the work of
  `Django CMS <http://www.django-cms.org>`_. 
* Many thanks to the contributors of ``cms/utils/plugins.py`` in Django CMS!

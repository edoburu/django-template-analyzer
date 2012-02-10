Introduction
============

The ``template_analyzer`` package offers an API to analyze the Django template structure.
It can be used to find nodes of a particular type, e.g. to do automatic detection of placeholder tags.

The scanner finds tags in various situations which ``template.nodelist.get_nodes_of_type()`` does not find:

* Extend nodes
* Include nodes
* Overwritten blocks with new definitions
* Blocks with or without ``{{ block.super }}``
* Reorganized blocks
* Ignoring nodes outside blocks in extending templates
* Handling multiple levens of super includes


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

Credits
=======

* This package is based on the work of
  `Django CMS <http://www.django-cms.org>`_. 
* Many thanks to the contributors of ``cms/utils/plugins.py`` in Django CMS!

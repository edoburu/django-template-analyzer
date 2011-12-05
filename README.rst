Introduction
============

The ``template_analyzer`` package offers an API to analyze the Django template structure.
It can be used to find nodes of a particular type, e.g. to do automatic detection of placeholder tags.

API example
==========

::

    from template_analyzer.djangoanalyzer import find_node_instances
    from mypackage.templatetags.placeholdertags import Placeholder

    template = get_template("mycms/default-page.html")

    placeholders = find_node_instances(template, Placeholder)
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

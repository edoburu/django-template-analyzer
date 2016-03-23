# -*- coding: utf-8 -*-

# Ensure that loader is imported before loader_tags, or a circular import may happen
# when this file is loaded from an `__init__.py` in an application root.
# The __init__.py files in applications are loaded very early due to the scan of of translation.activate()
import django
import django.template.loader  # noqa

# Normal imports
from django.utils import six
from django.template import NodeList, TemplateSyntaxError, Context, Template
from django.template.base import VariableNode
from django.template.loader import get_template
from django.template.loader_tags import ExtendsNode, BlockNode

try:
    # Django 1.8+
    from django.template.backends.django import Template as TemplateAdapter
except ImportError:
    TemplateAdapter = None

try:
    from django.template.loader_tags import ConstantIncludeNode as IncludeNode  # Django <= 1.6
except ImportError:
    from django.template.loader_tags import IncludeNode


def _is_variable_extends(extend_node):
    """
    Check whether an ``{% extends variable %}`` is used in the template.

    :type extend_node: ExtendsNode
    """
    if django.VERSION < (1, 4):
        return extend_node.parent_name_expr  # Django 1.3
    else:
        # The FilterExpression.var can be either a string, or Variable object.
        return not isinstance(extend_node.parent_name.var, six.string_types)  # Django 1.4


def _extend_blocks(extend_node, blocks, context):
    """
    Extends the dictionary `blocks` with *new* blocks in the parent node (recursive)

    :param extend_node: The ``{% extends .. %}`` node object.
    :type extend_node: ExtendsNode
    :param blocks: dict of all block names found in the template.
    :type blocks: dict
    """
    try:
        # This needs a fresh parent context, or it will detection recursion in Django 1.9+,
        # and thus skip the base template, which is already loaded.
        parent = extend_node.get_parent(_get_extend_context(context))
    except TemplateSyntaxError:
        if _is_variable_extends(extend_node):
            # we don't support variable extensions unless they have a default.
            return
        else:
            raise

    # Search for new blocks
    for parent_block in parent.nodelist.get_nodes_by_type(BlockNode):
        if not parent_block.name in blocks:
            blocks[parent_block.name] = parent_block
        else:
            # set this node as the super node (for {{ block.super }})
            block = blocks[parent_block.name]
            seen_supers = []
            while hasattr(block.parent, 'nodelist') and block.parent not in seen_supers:
                seen_supers.append(block.parent)
                block = block.parent
            block.parent = parent_block

    # search for further ExtendsNodes in the extended template
    # There is only one extend block in a template (Django checks for this).
    parent_extends = parent.nodelist.get_nodes_by_type(ExtendsNode)
    if parent_extends:
        _extend_blocks(parent_extends[0], blocks, context)


def _find_topmost_template(extend_node, context):
    try:
        parent_template = extend_node.get_parent(context)
    except TemplateSyntaxError:
        # we don't support variable extensions
        if _is_variable_extends(extend_node):
            return
        else:
            raise

    # There is only one extend block in a template (Django checks for this).
    parent_extends = parent_template.nodelist.get_nodes_by_type(ExtendsNode)
    if parent_extends:
        return _find_topmost_template(parent_extends[0], context)
    else:
        # No ExtendsNode
        return parent_template


def _extend_nodelist(extends_node, context, instance_types):
    """
    Returns a list of results found in the parent template(s)
    :type extends_node: ExtendsNode
    """
    results = []

    # Find all blocks in the complete inheritance chain
    blocks = extends_node.blocks.copy()  # dict with all blocks in the current template
    _extend_blocks(extends_node, blocks, context)

    # Dive into all blocks of the page one by one
    all_block_names = list(blocks.keys())
    for block in list(blocks.values()):
        results += _scan_nodes(block.nodelist, context, instance_types, block, ignore_blocks=all_block_names)

    # Scan topmost template for nodes that exist outside of blocks
    parent_template = _find_topmost_template(extends_node, context)
    if not parent_template:
        return []
    else:
        results += _scan_nodes(parent_template.nodelist, context, instance_types, ignore_blocks=all_block_names)
        return results


def _scan_nodes(nodelist, context, instance_types, current_block=None, ignore_blocks=None):
    """
    Loop through all nodes of a single scope level.

    :type nodelist: django.template.base.NodeList
    :type current_block: BlockNode
    :param instance_types: The instance to look for
    """
    results = []
    for node in nodelist:
        # first check if this is the object instance to look for.
        if isinstance(node, instance_types):
            results.append(node)
            # if it's a Constant Include Node ({% include "template_name.html" %})
        # scan the child template
        elif isinstance(node, IncludeNode):
            # if there's an error in the to-be-included template, node.template becomes None
            if node.template:
                # This is required for Django 1.7 but works on older version too
                # Check if it quacks like a template object, if not
                # presume is a template path and get the object out of it
                if not callable(getattr(node.template, 'render', None)):
                    template = get_template(node.template.var)
                else:
                    template = node.template

                if TemplateAdapter is not None and isinstance(template, TemplateAdapter):
                    # Django 1.8: received a new object, take original template
                    template = template.template

                results += _scan_nodes(template.nodelist, context, instance_types, current_block)
        # handle {% extends ... %} tags
        elif isinstance(node, ExtendsNode):
            results += _extend_nodelist(node, context, instance_types)
        # in block nodes we have to scan for super blocks
        elif isinstance(node, VariableNode) and current_block:
            if node.filter_expression.token == 'block.super':
                # Found a {{ block.super }} line
                if not hasattr(current_block.parent, 'nodelist'):
                    raise TemplateSyntaxError(
                        "Cannot read {{{{ block.super }}}} for {{% block {0} %}}, "
                        "the parent template doesn't have this block.".format(
                        current_block.name
                    ))
                results += _scan_nodes(current_block.parent.nodelist, context, instance_types, current_block.parent)
        # ignore nested blocks which are already handled
        elif isinstance(node, BlockNode) and ignore_blocks and node.name in ignore_blocks:
            continue
        # if the node has the newly introduced 'child_nodelists' attribute, scan
        # those attributes for nodelists and recurse them
        elif hasattr(node, 'child_nodelists'):
            for nodelist_name in node.child_nodelists:
                if hasattr(node, nodelist_name):
                    subnodelist = getattr(node, nodelist_name)
                    if isinstance(subnodelist, NodeList):
                        if isinstance(node, BlockNode):
                            current_block = node
                        results += _scan_nodes(subnodelist, context, instance_types, current_block)
        # else just scan the node for nodelist instance attributes
        else:
            for attr in dir(node):
                obj = getattr(node, attr)
                if isinstance(obj, NodeList):
                    if isinstance(node, BlockNode):
                        current_block = node
                    results += _scan_nodes(obj, context, instance_types, current_block)
    return results


def _get_main_context(nodelist):
    if TemplateAdapter is not None:
        # Django 1.8+
        # The context is empty, but needs to be provided to handle the {% extends %} node.
        context = Context({})

        if isinstance(nodelist, TemplateAdapter):
            # The top-level context.
            context.template = Template('', engine=nodelist.template.engine)
        else:
            # Just in case a different nodelist is provided.
            # Using the default template now.
            context.template = Template('')
        return context
    else:
        return {}


def _get_extend_context(parent_context):
    if TemplateAdapter is not None:
        # Django 1.8+
        # For extends nodes, a fresh template instance is constructed.
        # The loader cache of the original `nodelist` is skipped.
        context = Context({})
        context.template = Template('', engine=parent_context.template.engine)
        return context
    else:
        return {}


def get_node_instances(nodelist, instances):
    """
    Find the nodes of a given instance.

    In contract to the standard ``template.nodelist.get_nodes_by_type()`` method,
    this also looks into ``{% extends %}`` and ``{% include .. %}`` nodes
    to find all possible nodes of the given type.

    :param instances: A class Type, or tuple of types to find.
    :param nodelist:  The Template object, or nodelist to scan.
    :returns: A list of Node objects which inherit from the list of given `instances` to find.
    :rtype: list
    """
    context = _get_main_context(nodelist)

    # The Django 1.8 loader returns an adapter class; it wraps the original Template in a new object to be API compatible
    if TemplateAdapter is not None and isinstance(nodelist, TemplateAdapter):
        nodelist = nodelist.template

    return _scan_nodes(nodelist, context, instances)

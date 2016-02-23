# -*- coding: utf-8 -*-

# Ensure that loader is imported before loader_tags, or a circular import may happen
# when this file is loaded from an `__init__.py` in an application root.
# The __init__.py files in applications are loaded very early due to the scan of of translation.activate()
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
    if hasattr(extend_node, 'parent_name_expr'):  # Django 1.3
        return extend_node.parent_name_expr
    elif hasattr(extend_node, 'parent_name'):
        # Django 1.4 always has a 'parent_name'. The FilterExpression.var can be either a string, or Variable object.
        return not isinstance(extend_node.parent_name.var, six.string_types)  # Django 1.4
    else:
        raise AttributeError("Unable to detect parent_name of ExtendNode")  # future?


def _extend_blocks(extend_node, blocks, context):
    """
    Extends the dictionary `blocks` with *new* blocks in the parent node (recursive)
    """
    try:
        # This needs a fresh parent context, or it will detection recursion in Django 1.9+,
        # and thus skip the base template, which is already loaded.
        parent = extend_node.get_parent(_get_context())
    except TemplateSyntaxError:
        if _is_variable_extends(extend_node):
            # we don't support variable extensions unless they have a default.
            return
        else:
            raise

    # Search for new blocks
    for node in parent.nodelist.get_nodes_by_type(BlockNode):
        if not node.name in blocks:
            blocks[node.name] = node
        else:
            # set this node as the super node (for {{ block.super }})
            block = blocks[node.name]
            seen_supers = []
            while hasattr(block.super, 'nodelist') and block.super not in seen_supers:
                seen_supers.append(block.super)
                block = block.super
            block.super = node

    # search for further ExtendsNodes
    for node in parent.nodelist.get_nodes_by_type(ExtendsNode):
        _extend_blocks(node, blocks, context)
        break


def _find_topmost_template(extend_node, context):
    try:
        parent_template = extend_node.get_parent(context)
    except TemplateSyntaxError:
        # we don't support variable extensions
        if _is_variable_extends(extend_node):
            return
        else:
            raise

    for node in parent_template.nodelist.get_nodes_by_type(ExtendsNode):
        # Their can only be one extend block in a template, otherwise django raises an exception
        return _find_topmost_template(node, context)

    # No ExtendsNode
    return parent_template


def _extend_nodelist(node_instances, extend_node, context):
    """
    Returns a list of placeholders found in the parent template(s) of this
    ExtendsNode
    """
    blocks = extend_node.blocks
    _extend_blocks(extend_node, blocks, context)
    placeholders = []

    for block in list(blocks.values()):
        placeholders += _scan_nodes(node_instances, block.nodelist, context, block, ignore_blocks=list(blocks.keys()))

    # Scan topmost template for placeholder outside of blocks
    parent_template = _find_topmost_template(extend_node, context)
    if not parent_template:
        return []
    placeholders += _scan_nodes(node_instances, parent_template.nodelist, context, ignore_blocks=list(blocks.keys()))
    return placeholders


def _scan_nodes(node_instances, nodelist, context, current_block=None, ignore_blocks=None):
    # The Django 1.8 loader returns an adapter class; it wraps the original Template in a new object to be API compatible
    if TemplateAdapter is not None and isinstance(nodelist, TemplateAdapter):
        nodelist = nodelist.template

    placeholders = []
    for node in nodelist:
        # first check if this is the object instance to look for.
        if isinstance(node, node_instances):
            placeholders.append(node)
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

                placeholders += _scan_nodes(node_instances, template.nodelist, context, current_block)
        # handle {% extends ... %} tags
        elif isinstance(node, ExtendsNode):
            placeholders += _extend_nodelist(node_instances, node, context)
        # in block nodes we have to scan for super blocks
        elif isinstance(node, VariableNode) and current_block:
            if node.filter_expression.token == 'block.super':
                if not hasattr(current_block.super, 'nodelist'):
                    raise TemplateSyntaxError("Cannot render block.super for blocks without a parent.")
                placeholders += _scan_nodes(node_instances, current_block.super.nodelist, context, current_block.super)
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
                        placeholders += _scan_nodes(node_instances, subnodelist, context, current_block)
        # else just scan the node for nodelist instance attributes
        else:
            for attr in dir(node):
                obj = getattr(node, attr)
                if isinstance(obj, NodeList):
                    if isinstance(node, BlockNode):
                        current_block = node
                    placeholders += _scan_nodes(node_instances, obj, context, current_block)
    return placeholders


def _get_context(nodelist=None):
    if TemplateAdapter is not None:
        # The context is empty, but needs to be provided to handle the {% extends %} node.
        # For Django 1.8 templates, provide a hook to the top level template there.
        context = Context({})
        context.template = Template('')
        if isinstance(nodelist, TemplateAdapter):
            context.template = nodelist.template
        return context
    else:
        return {}


def get_node_instances(nodelist, instances):
    """
    Find the nodes of a given instance.

    :param instances: A class Type, or tuple of types to find.
    :param nodelist:  The Template object, or nodelist to scan.
    :returns: A list of Node objects which inherit from the list of given `instances` to find.
    :rtype: list
    """
    context = _get_context(nodelist)
    return _scan_nodes(instances, nodelist, context)

# -*- coding: utf-8 -*-

# Ensure that loader is imported before loader_tags, or a circular import may happen
# when this file is loaded from an `__init__.py` in an application root.
# The __init__.py files in applications are loaded very early due to the scan of of translation.activate()
import django.template.loader

# Normal imports
from django.template.base import NodeList, VariableNode, TemplateSyntaxError
from django.template.loader_tags import ConstantIncludeNode, ExtendsNode, BlockNode

def _is_variable_extends(extend_node):
    if hasattr(extend_node, 'parent_name_expr'):  # Django 1.3
        return extend_node.parent_name_expr
    elif hasattr(extend_node, 'parent_name'):
        # Django 1.4 always has a 'parent_name'. The FilterExpression.var can be either a string, or Variable object.
        return not isinstance(extend_node.parent_name.var, basestring) # Django 1.4
    else:
        raise AttributeError("Unable to detect parent_name of ExtendNode")  # future?
    return False


def _extend_blocks(extend_node, blocks):
    """
    Extends the dictionary `blocks` with *new* blocks in the parent node (recursive)
    """
    # we don't support variable extensions
    if _is_variable_extends(extend_node):
        return

    parent = extend_node.get_parent(None)
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
        _extend_blocks(node, blocks)
        break

def _find_topmost_template(extend_node):
    parent_template = extend_node.get_parent({})
    for node in parent_template.nodelist.get_nodes_by_type(ExtendsNode):
        # Their can only be one extend block in a template, otherwise django raises an exception
        return _find_topmost_template(node)
    # No ExtendsNode
    return extend_node.get_parent({})

def _extend_nodelist(node_instances, extend_node):
    """
    Returns a list of placeholders found in the parent template(s) of this
    ExtendsNode
    """
    # we don't support variable extensions
    if _is_variable_extends(extend_node):
        return []
    blocks = extend_node.blocks
    _extend_blocks(extend_node, blocks)
    placeholders = []

    for block in blocks.values():
        placeholders += _scan_nodes(node_instances, block.nodelist, block, ignore_blocks=blocks.keys())

    # Scan topmost template for placeholder outside of blocks
    parent_template = _find_topmost_template(extend_node)
    placeholders += _scan_nodes(node_instances, parent_template.nodelist, ignore_blocks=blocks.keys())
    return placeholders

def _scan_nodes(node_instances, nodelist, current_block=None, ignore_blocks=None):
    placeholders = []

    for node in nodelist:
        # first check if this is the object instance to look for.
        if isinstance(node, node_instances):
            placeholders.append(node)
            # if it's a Constant Include Node ({% include "template_name.html" %})
        # scan the child template
        elif isinstance(node, ConstantIncludeNode):
            # if there's an error in the to-be-included template, node.template becomes None
            if node.template:
                placeholders += _scan_nodes(node_instances, node.template.nodelist, current_block)
        # handle {% extends ... %} tags
        elif isinstance(node, ExtendsNode):
            placeholders += _extend_nodelist(node_instances, node)
        # in block nodes we have to scan for super blocks
        elif isinstance(node, VariableNode) and current_block:
            if node.filter_expression.token == 'block.super':
                if not hasattr(current_block.super, 'nodelist'):
                    raise TemplateSyntaxError("Cannot render block.super for blocks without a parent.")
                placeholders += _scan_nodes(node_instances, current_block.super.nodelist, current_block.super)
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
                        placeholders += _scan_nodes(node_instances, subnodelist, current_block)
        # else just scan the node for nodelist instance attributes
        else:
            for attr in dir(node):
                obj = getattr(node, attr)
                if isinstance(obj, NodeList):
                    if isinstance(node, BlockNode):
                        current_block = node
                    placeholders += _scan_nodes(node_instances, obj, current_block)
    return placeholders


def get_node_instances(nodelist, instances):
    """
    Find the nodes of a given instance.

    :param instances: A class Type, or typle of types to find.
    :param nodelist:  The Template object, or nodelist to scan.
    :returns: A list of Node objects which inherit from the list of given `instances` to find.
    :rtype: list
    """
    return _scan_nodes(instances, nodelist)

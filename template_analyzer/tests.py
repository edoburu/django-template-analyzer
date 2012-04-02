from django.template.loader import get_template
from django.test.testcases import TestCase


def get_placeholders(filename):
    from template_analyzer.djangoanalyzer import get_node_instances
    from template_analyzer.templatetags.template_analyzer_test_tags import Placeholder

    template = get_template(filename)

    # Definitely not the same:
    #placeholders = template.nodelist.get_nodes_by_type(Placeholder)

    placeholders = get_node_instances(template, Placeholder)
    return [p.get_name() for p in placeholders]


class PlaceholderTestCase(TestCase):
    def test_placeholder_scanning_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_one.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'three']))

    def test_placeholder_scanning_include(self):
        placeholders = get_placeholders('placeholder_tests/test_two.html')
        self.assertEqual(sorted(placeholders), sorted([u'child', u'three']))

    def test_placeholder_scanning_double_extend(self):
        placeholders = get_placeholders('placeholder_tests/test_three.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'new_three']))

    def test_placeholder_scanning_complex(self):
        placeholders = get_placeholders('placeholder_tests/test_four.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'child', u'four']))

    def test_placeholder_scanning_super(self):
        placeholders = get_placeholders('placeholder_tests/test_five.html')
        self.assertEqual(sorted(placeholders), sorted([u'one', u'extra_one', u'two', u'three']))

    def test_placeholder_scanning_nested(self):
        placeholders = get_placeholders('placeholder_tests/test_six.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'new_two', u'new_three']))

#    def test_placeholder_scanning_duplicate(self):
#        placeholders = self.assertWarns(DuplicatePlaceholderWarning, "Duplicate placeholder found: `one`", get_placeholders, 'placeholder_tests/test_seven.html')
#        self.assertEqual(sorted(placeholders), sorted([u'one']))

    def test_placeholder_scanning_extend_outside_block(self):
        placeholders = get_placeholders('placeholder_tests/outside.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))

    def test_placeholder_scanning_extend_outside_block_nested(self):
        placeholders = get_placeholders('placeholder_tests/outside_nested.html')
        self.assertEqual(sorted(placeholders), sorted([u'new_one', u'two', u'base_outside']))

    def test_placeholder_scanning_nested_super(self):
        placeholders = get_placeholders('placeholder_tests/nested_super_level1.html')
        self.assertEqual(sorted(placeholders), sorted([u'level1', u'level2', u'level3', u'level4']))

    def test_ignore_variable_extends(self):
        placeholders = get_placeholders('placeholder_tests/variable_extends.html')
        self.assertEqual(sorted(placeholders), [])

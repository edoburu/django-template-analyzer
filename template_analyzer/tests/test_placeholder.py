from django.template import Context
from django.template.base import TemplateSyntaxError
from django.template.loader import get_template
from django.test.testcases import TestCase

from template_analyzer.djangoanalyzer import get_node_instances
from template_analyzer.templatetags.template_analyzer_test_tags import Placeholder


def get_placeholders(filename):
    template = get_template(filename)
    return get_placeholders_in_template(template)


def get_placeholders_in_template(template):
    placeholders = get_node_instances(template, Placeholder)
    return [p.get_name() for p in placeholders]


class PlaceholderTestCase(TestCase):
    def test_placeholder_scanning_extend(self):
        placeholders = get_placeholders("placeholder_tests/test_one.html")
        self.assertEqual(sorted(placeholders), sorted(["new_one", "two", "three"]))

    def test_placeholder_scanning_include(self):
        placeholders = get_placeholders("placeholder_tests/test_two.html")
        self.assertEqual(sorted(placeholders), sorted(["child", "three"]))

    def test_placeholder_scanning_double_extend(self):
        placeholders = get_placeholders("placeholder_tests/test_three.html")
        self.assertEqual(sorted(placeholders), sorted(["new_one", "two", "new_three"]))

    def test_placeholder_scanning_complex(self):
        placeholders = get_placeholders("placeholder_tests/test_four.html")
        self.assertEqual(sorted(placeholders), sorted(["new_one", "child", "four"]))

    def test_placeholder_scanning_super(self):
        placeholders = get_placeholders("placeholder_tests/test_five.html")
        self.assertEqual(sorted(placeholders), sorted(["one", "extra_one", "two", "three"]))

    def test_placeholder_scanning_nested(self):
        placeholders = get_placeholders("placeholder_tests/test_six.html")
        self.assertEqual(sorted(placeholders), sorted(["new_one", "new_two", "new_three"]))

    #    def test_placeholder_scanning_duplicate(self):
    #        placeholders = self.assertWarns(DuplicatePlaceholderWarning, "Duplicate placeholder found: `one`", get_placeholders, 'placeholder_tests/test_seven.html')
    #        self.assertEqual(sorted(placeholders), sorted([u'one']))

    def test_placeholder_scanning_extend_outside_block(self):
        placeholders = get_placeholders("placeholder_tests/outside.html")
        self.assertEqual(sorted(placeholders), sorted(["new_one", "two", "base_outside"]))

    def test_placeholder_scanning_extend_outside_block_nested(self):
        placeholders = get_placeholders("placeholder_tests/outside_nested.html")
        self.assertEqual(sorted(placeholders), sorted(["new_one", "two", "base_outside"]))

    def test_placeholder_scanning_nested_super(self):
        placeholders = get_placeholders("placeholder_tests/nested_super_level1.html")
        self.assertEqual(sorted(placeholders), sorted(["level1", "level2", "level3", "level4"]))

    def test_ignore_variable_extends(self):
        placeholders = get_placeholders("placeholder_tests/variable_extends.html")
        self.assertEqual(sorted(placeholders), [])

    def test_variable_extends_default(self):
        placeholders = get_placeholders("placeholder_tests/variable_extends_default.html")
        self.assertEqual(sorted(placeholders), sorted(["one", "two", "three"]))

    def test_tag_placeholder_exception(self):
        exp = TemplateSyntaxError("placeholder tag requires 2 arguments")
        with self.assertRaises(TemplateSyntaxError) as tsx:
            get_placeholders("placeholder_tests/tag_exception.html")
        self.assertEqual(str(tsx.exception), str(exp))

    def _get_custom_engine(self, **options):
        options.setdefault(
            "loaders",
            (
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
                "template_analyzer.tests.app_loader.Loader",
            ),
        )

        from django.template.backends.django import DjangoTemplates

        return DjangoTemplates(
            {
                "NAME": "loader_test",
                "DIRS": (),
                "APP_DIRS": False,
                "OPTIONS": options,
            }
        )

    def test_custom_loader(self):
        """
        When the application uses a custom loader, make sure the template analyzer uses that to find extends nodes.
        """
        # See whether the engine is correctly passed;
        # otherwise the custom extends loader could fail.
        engine = self._get_custom_engine()
        template = engine.get_template("placeholder_tests/extends_custom_loader_level1.html")

        placeholders = get_placeholders_in_template(template)
        self.assertEqual(sorted(placeholders), sorted(["new_one", "two", "three"]))

    def test_custom_loader_level2(self):
        """
        When the application uses a custom loader, make sure the template analyzer uses that to find extends nodes.
        """
        # See whether the engine is correctly passed;
        # otherwise the custom extends loader could fail.
        engine = self._get_custom_engine()
        template = engine.get_template("placeholder_tests/extends_custom_loader_level2.html")

        placeholders = get_placeholders_in_template(template)
        self.assertEqual(sorted(placeholders), sorted(["new_one", "two", "three"]))

    def test_cached_template(self):
        context = {}
        template = get_template("placeholder_tests/cache_level2.html")
        result1 = template.render(context)  # render first

        # the analyzer should not affect block nodes.
        placeholders = get_placeholders_in_template(template)
        self.assertEqual(sorted(placeholders), sorted(["cache"]))

        # see if the block structure is altered
        result2 = template.render(context)
        self.assertEqual(result1, result2)

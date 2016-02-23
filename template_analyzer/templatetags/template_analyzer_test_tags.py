from django.template import Library, Node, Variable, TemplateSyntaxError

register = Library()


class Placeholder(Node):
    """
    Simple placeholder node.
    """

    @classmethod
    def parse(cls, parser, token):
        tokens = token.contents.split()
        if len(tokens) == 2:
            return cls(Variable(tokens[1]))
        else:
            raise TemplateSyntaxError("{0} tag requires 2 arguments".format(tokens[0]))

    def __init__(self, name_var):
        self.name_var = name_var

    def get_name(self):
        return self.name_var.literal

    def render(self, context):
        return '[placeholder: {0}]'.format(self.name_var.literal)


@register.tag
def placeholder(parser, token):
    """
    A dummy placeholder template tag.
    """
    return Placeholder.parse(parser, token)

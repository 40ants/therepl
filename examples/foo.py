def get_foo():
    return 'new foo'


class Foo:
    attr = 'new'

    def __init__(self, attr=None):
        if attr is not None:
            self.attr = attr

    def get(self):
        return 'new foo'

    def get_class_attr(self):
        return self.attr


class Bar(Foo):
    pass


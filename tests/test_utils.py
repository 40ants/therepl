from ipython_modules.utils import upgrade_class


def test_class_upgrade():
    class Foo():
        def get(self):
            return 'old'

    obj = Foo()

    class Foo2():
        def get(self):
            return 'new'

    upgrade_class(obj, Foo, Foo2)

    assert obj.get() == 'new'


def test_base_class_upgrade():
    class Foo():
        def get(self):
            return 'old'

    class Bar(Foo):
        def bar(self):
            return 'bar'

    obj = Bar()

    class Foo2():
        def get(self):
            return 'new'

    upgrade_class(obj, Foo, Foo2)

    assert obj.get() == 'new'

    # And bar method still should be available
    assert obj.bar() == 'bar'

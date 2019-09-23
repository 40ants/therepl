import foo

from foo import get_foo, Foo

def get_indirect():
    return foo.get_foo() + ' and bar'

def get_direct():
    return get_foo() + ' and bar'

def get_internal():
    from foo import get_foo
    return get_foo() + ' and bar'


glob_obj1 = foo.Foo()
glob_obj2 = Foo()
glob_obj3 = Foo(attr='overridden')


def get_glob_objs():
    return ((glob_obj1.get(),
             glob_obj1.get_class_attr()),
            (glob_obj2.get(),
             glob_obj2.get_class_attr()),
            (glob_obj3.get(),
             glob_obj3.get_class_attr()))


def get_objs():
    obj1 = foo.Foo()
    obj2 = Foo()
    obj3 = Foo(attr='overridden')

    return ((obj1.get(),
             obj1.get_class_attr()),
            (obj2.get(),
             obj2.get_class_attr()),
            (obj3.get(),
             obj3.get_class_attr()))

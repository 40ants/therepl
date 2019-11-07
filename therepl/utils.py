import gc

from .log import logger


def upgrade_class(obj, old_class, new_class):
    if obj.__class__ is old_class:
        obj.__class__ = new_class
    else:
        mro = obj.__class__.mro()

        replaced = False
        
        def replace(cls):
            nonlocal replaced
    
            if cls is old_class:
                replaced = True
                return new_class
            else:
                return cls

        bases = tuple(map(replace, mro[1:]))

        if replaced:
            old_base_class = obj.__class__
            new_class = type(old_base_class.__name__, bases, dict(old_base_class.__dict__))
            obj.__class__ = new_class


def find_objs(cls):
    return [
        obj
        for obj in gc.get_objects()
        if isinstance(obj, cls)
    ]


def upgrade_objects(from_class, to_class):
    logger.error(f'Upgrading from {from_class} (id {id(from_class)}) to {to_class} (id {id(to_class)})')

    for obj in find_objs(from_class):
        upgrade_class(obj, from_class, to_class)

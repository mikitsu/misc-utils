"""Stuff"""
import functools
import typing as T


def show_table(items: dict):
    """Print the gven dict as a table where keys are headers and
    values are sequences of the items in rows"""
    lengths = [max(len(x) for x in items[k]+[k])+3 for k in items]
    print('|'.join(k.ljust(lengths[i]) for i, k in enumerate(items)))
    print('-'*(sum(lengths)+len(items)-1))
    
    for i in range(len(next(iter(items.values())))):
        print('|'.join(items[k][i].ljust(lengths[j])
                       for j, k in enumerate(items)))



def only_classmethods(cls):
    """convert all normal methods to classmethods"""
    for k, v in cls.__dict__.items():
        if (not k.startswith('__')
                and callable(v)
                and not isinstance(v, (classmethod, staticmethod))):
            setattr(cls, k, classmethod(v))
    return cls


def multiline_input(prompt='... ', end='\x04'):
    return '\n'.join(iter(functools.partial(input, prompt), end))


def threadsafe_method(name='lock'):
    """wrap the method into a with getattr(self, name):"""
    def wrapper_maker(meth):
        @functools.wraps(meth)
        def wrapper(self, *args, **kwargs):
            with getattr(self, name):
                return meth(self, *args, **kwargs)
        return wrapper
    return wrapper_maker


def threadsafe_class(name: str = 'lock', exclude: T.Container[str] =
                     ('__init__', '__new__', '__init_subclass__'),
                     check: T.Callable[[T.Any], bool] = callable,
                     wrap_init=threading.RLock):
    """wrap all class attributes passing `check` (default: `callable`) with `threadsafe_method`

    `exclude` may contain names not to wrap. Only `cls.__dict__` is checked.
    if `wrap_init` is truthly, __init__ will be wrapped to setattr(self, name, wrap_init())"""
    def modifier(cls):
        for k, v in cls.__dict__.items():
            if check(v) and k not in exclude:
                setattr(cls, k, threadsafe_method(name=name)(v))
            if wrap_init and k == '__init__':
                __init__method = v
                @functools.wraps(v)
                def wrapper(self, *args, **kwargs):
                    setattr(self, name, wrap_init())
                    return __init__method(self, *args, **kwargs)
                setattr(cls, '__init__', wrapper)
        return cls
    return modifier


class Tree:
    @classmethod
    def new(cls, value):
        return type('<DerivedTreeNode: {}>'.format(type(value)),
                    (Tree, type(value)), {})(value)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, type(
            '<DerivedTreeNode: {}>'.format(type(value)), (Tree, type(value)), {})(value))

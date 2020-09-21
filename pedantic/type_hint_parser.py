"""Idea is taken from: https://stackoverflow.com/a/55504010/10975692"""
import inspect
import typing
from typing import Any, Dict, Iterable, ItemsView, Callable, Union, Optional, Tuple, Mapping
import collections


def trace(func): # TODO remove this
    def wrapper(*args, **kwargs):
        from datetime import datetime
        print(f'Trace: {datetime.now()} calling {func.__name__}()  with {args}, {kwargs}')
        original_result = func(*args, **kwargs)
        print(f'Trace: {datetime.now()} {func.__name__}() returned {original_result!r}')
        return original_result
    return wrapper


def _is_instance(obj: Any, type_: Any, type_vars: Dict[str, Any]) -> bool:
    assert _has_required_type_arguments(type_), \
        f'The type annotation "{type_}" misses some type arguments e.g. ' \
        f'"typing.Tuple[Any, ...]" or "typing.Callable[..., str]".'

    if type_.__module__ == 'typing':
        if _is_generic(type_):
            origin = _get_base_generic(type_)
        else:
            origin = type_
        name = _get_name(origin)

        if name in _SPECIAL_INSTANCE_CHECKERS:
            validator = _SPECIAL_INSTANCE_CHECKERS[name]
            return validator(obj, type_, type_vars)

    if _is_generic(type_):
        python_type = type_.__origin__
        if not isinstance(obj, python_type):
            return False

        base = _get_base_generic(type_)
        validator = _ORIGIN_TYPE_CHECKERS[base]

        type_args = _get_subtypes(type_)
        return validator(obj, type_args, type_vars)

    if isinstance(type_, typing.TypeVar):
        if type_ in type_vars:
            other = type_vars[type_]
            assert type(obj) == type(other), \
                f'For TypeVar {type_} exists a type conflict: value {obj} has type {type(obj)} and value ' \
                f'{other} has type {type(other)}'
        else:
            type_vars[type_] = obj
        return True

    if _is_type_new_type(type_):
        return isinstance(obj, type_.__supertype__)

    return isinstance(obj, type_)


def _is_type_new_type(type_: Any) -> bool:
    return type_.__qualname__ == typing.NewType('name', int).__qualname__  # arguments of NewType() are arbitrary here


def _get_name(cls: Any) -> str:
    """
    >>> from typing import Tuple, Callable
    >>> _get_name(Tuple)
    'Tuple'
    >>> _get_name(Callable)
    'Callable'
    """
    if hasattr(cls, '_name'):
        return cls._name
    elif hasattr(cls, '__name__'):
        return cls.__name__
    else:
        return type(cls).__name__[1:]


def _is_generic(cls: Any) -> bool:
    """
    Detects any kind of generic, for example `List` or `List[int]`. This includes "special" types like
    Union and Tuple - anything that's subscriptable, basically.
    Examples:
        >>> from typing import  List, Callable, Any
        >>> _is_generic(int)  # float, bool, str
        False
        >>> _is_generic(List[int])
        True
        >>> _is_generic(List[List[int]])
        True
        >>> _is_generic(Any)
        False
        >>> _is_generic(Callable[[int], int])
        True
    """
    if hasattr(typing, '_GenericAlias'):
        if isinstance(cls, typing._GenericAlias):
            return True

        if isinstance(cls, typing._SpecialForm):
            return cls not in {typing.Any}
    else:
        if isinstance(cls, (typing.GenericMeta, typing._Union, typing._Optional, typing._ClassVar)):
            return True
    return False


def _is_base_generic(cls: Any) -> bool:
    """
    >>> _is_base_generic(int)
    False
    >>> _is_base_generic(typing.List)  #TODO False for Python >= 3.9
    True
    >>> _is_base_generic(typing.Callable)  #TODO False for Python >= 3.9
    True
    >>> _is_base_generic(typing.List[int])
    False
    >>> _is_base_generic(typing.Callable[[int], str])
    False
    >>> _is_base_generic(typing.List[typing.List[int]])
    False
    >>> _is_base_generic(list)
    False
    """

    if hasattr(typing, '_GenericAlias'):
        if isinstance(cls, typing._GenericAlias):
            if str(cls) in ['typing.Tuple', 'typing.Callable']:
                return True

            return len(cls.__parameters__) > 0

        if isinstance(cls, typing._SpecialForm):
            return cls._name in {'ClassVar', 'Union', 'Optional'}
    else:
        if isinstance(cls, (typing.GenericMeta, typing._Union)):
            return cls.__args__ in {None, ()}

        if isinstance(cls, typing._Optional):
            return True
    return False


def _has_required_type_arguments(cls: Any) -> bool:
    """
        >>> from typing import List, Callable, Tuple
        >>> _has_required_type_arguments(List)
        False
        >>> _has_required_type_arguments(List[int])
        True
        >>> _has_required_type_arguments(Callable[[int, float], Tuple[float, str]])
        True
    """

    requirements_exact = {
        'Callable': 2,
        'List': 1,
        'Set': 1,
        'FrozenSet': 1,
        'Iterable': 1,
        'Sequence': 1,
        'Dict': 2,
        'Optional': 2,  # because typing.get_args(typing.Optional[int]) returns (int, None)
    }
    requirements_min = {
        'Tuple': 1,
        'Union': 2,
    }
    base: str = _get_name(cls=cls)

    if '[' not in str(cls) and (base in requirements_min or base in requirements_exact):
        return False

    num_type_args = len(_get_type_arguments(cls))

    if base in requirements_exact:
        return requirements_exact[base] == num_type_args
    elif base in requirements_min:
        return requirements_min[base] <= num_type_args
    else:
        return True


def _get_type_arguments(cls: Any) -> Tuple[typing.Any, ...]:
    """: #TODO
    # >>> _get_type_arguments(int)
    # ()
    # >>> _get_type_arguments(typing.List) # NOTE: That output here is different on different Python versions!
    # (~T,)
    # >>> _get_type_arguments(typing.List[int])
    # (<class 'int'>,)
    # >>> _get_type_arguments(typing.Callable[[int, float], str])
    # ([<class 'int'>, <class 'float'>], <class 'str'>)
    # >>> _get_type_arguments(typing.Callable[..., str])
    # (Ellipsis, <class 'str'>)
    """
    if hasattr(typing, 'get_args'):
        return typing.get_args(cls)
    elif hasattr(cls, '__args__'):
        res = cls.__args__
        origin = _get_base_generic(cls)
        if ((origin is typing.Callable) or (origin is collections.abc.Callable)) and res[0] is not Ellipsis:
            res = (list(res[:-1]), res[-1])
        return res
    else:
        return ()


def _get_base_generic(cls: Any) -> Any:
    """
    >>> _get_base_generic(typing.List[float])
    typing.List
    """
    if not hasattr(typing, '_GenericAlias'):
        return cls.__origin__

    if cls._name is None:
        return cls.__origin__
    else:
        return getattr(typing, cls._name)


def _is_subtype(sub_type: Any, super_type: Any) -> bool:
    """
        >>> from typing import Any, List, Callable, Tuple, Union, Optional
        >>> _is_subtype(float, float)
        True
        >>> _is_subtype(int, float)
        False
        >>> _is_subtype(float, int)
        False
        >>> _is_subtype(int, Any)
        True
        >>> _is_subtype(Any, int)
        False
        >>> _is_subtype(Any, Any)
        True
        >>> _is_subtype(Ellipsis, Ellipsis)
        True
        >>> _is_subtype(Tuple[float, str], Tuple[float, str])
        True
        >>> _is_subtype(Tuple[float], Tuple[float, str])
        False
        >>> _is_subtype(Tuple[float, str], Tuple[str])
        False
        >>> _is_subtype(Tuple[float, str], Tuple[Any, ...])
        True
        >>> _is_subtype(Tuple[Any, ...], Tuple[float, str])
        False
        >>> _is_subtype(Tuple[float, str], Tuple[int, ...])
        False
        >>> _is_subtype(Tuple[int, str], Tuple[int, ...])
        True
        >>> _is_subtype(Tuple[int, ...], Tuple[int, str])
        False
        >>> _is_subtype(Tuple[float, str, bool, int], Tuple[Any, ...])
        True
        >>> _is_subtype(int, Union[int, float])
        Traceback (most recent call last):
        ...
        TypeError: typing.Union cannot be used with issubclass()
        >>> _is_subtype(int, Union[str, float])
        Traceback (most recent call last):
        ...
        TypeError: typing.Union cannot be used with issubclass()
        >>> _is_subtype(List[int], List[Union[int, float]])
        Traceback (most recent call last):
        ...
        TypeError: typing.Union cannot be used with issubclass()
        >>> _is_subtype(List[Union[int, float]], List[int])
        Traceback (most recent call last):
        ...
        TypeError: issubclass() arg 1 must be a class
    """

    if not _is_generic(sub_type):
        python_super = _get_class_of_type_annotation(super_type)
        python_sub = _get_class_of_type_annotation(sub_type)
        return issubclass(python_sub, python_super)

    python_sub = _get_class_of_type_annotation(sub_type)
    python_super = _get_class_of_type_annotation(super_type)
    if not issubclass(python_sub, python_super):
        return False

    if not _is_generic(super_type) or _is_base_generic(super_type):
        return True

    if _is_base_generic(sub_type):
        return False

    sub_args = _get_subtypes(sub_type)
    super_args = _get_subtypes(super_type)
    if len(sub_args) != len(super_args) and Ellipsis not in sub_args + super_args:
        return False
    return all(_is_subtype(sub_type=sub_arg, super_type=super_arg) for sub_arg, super_arg in zip(sub_args, super_args))


def _get_class_of_type_annotation(annotation: Any) -> Any:
    """
        >>> from typing import Dict, List, Any, Tuple, Callable, Union
        >>> _get_class_of_type_annotation(int)
        <class 'int'>
        >>> _get_class_of_type_annotation(Any)
        <class 'object'>
        >>> _get_class_of_type_annotation(Ellipsis)
        <class 'object'>
        >>> _get_class_of_type_annotation(Dict)
        <class 'dict'>
        >>> _get_class_of_type_annotation(Dict[str, int])
        <class 'dict'>
        >>> _get_class_of_type_annotation(List)
        <class 'list'>
        >>> _get_class_of_type_annotation(List[int])
        <class 'list'>
        >>> _get_class_of_type_annotation(Tuple)
        <class 'tuple'>
        >>> _get_class_of_type_annotation(Tuple[int, int])
        <class 'tuple'>
        >>> _get_class_of_type_annotation(Callable[[int], int])
        <class 'collections.abc.Callable'>
        >>> _get_class_of_type_annotation(Callable)
        <class 'collections.abc.Callable'>
        >>> _get_class_of_type_annotation(Union)
        Traceback (most recent call last):
        ...
        AttributeError: '_SpecialForm' object has no attribute '__origin__'
    """
    if hasattr(annotation, 'mro'):
        mro = annotation.mro()
        if typing.Type in mro:
            return annotation._get_class_of_type_annotation
        elif annotation.__module__ == 'typing':
            return annotation.__origin__
        else:
            return annotation
    elif annotation == typing.Any or annotation == Ellipsis:
        return object
    else:
        return annotation.__origin__


def _get_subtypes(cls: Any) -> Tuple:
    """
        >>> from typing import Tuple, List, Union, Callable, Any
        >>> _get_subtypes(List[float])
        (<class 'float'>,)
        >>> _get_subtypes(List[int])
        (<class 'int'>,)
        >>> _get_subtypes(List[List[int]])
        (typing.List[int],)
        >>> _get_subtypes(List[List[List[int]]])
        (typing.List[typing.List[int]],)
        >>> _get_subtypes(List[Tuple[float, str]])
        (typing.Tuple[float, str],)
        >>> _get_subtypes(List[Tuple[Any, ...]])
        (typing.Tuple[typing.Any, ...],)
        >>> _get_subtypes(Union[str, float, bool, int])  #TODO: fails with python 3.6 since _get_base_generic is buggy
        (<class 'str'>, <class 'float'>, <class 'bool'>, <class 'int'>)
        >>> _get_subtypes(Callable[[int, float], typing.Tuple[float, str]])
        ((<class 'int'>, <class 'float'>), typing.Tuple[float, str])
    """
    subtypes = cls.__args__

    if _get_base_generic(cls) is Callable and (len(subtypes) != 2 or subtypes[0] is not ...):
        return subtypes[:-1], subtypes[-1]
    return subtypes


def _instancecheck_iterable(iterable: Iterable, type_args: Tuple, type_vars: Dict[str, Any]) -> bool:
    """
        >>> from typing import List, Any, Union
        >>> _instancecheck_iterable([1.0, -4.2, 5.4], (float,), {})
        True
        >>> _instancecheck_iterable([1.0, -4.2, 5], (float,), {})
        False
        >>> _instancecheck_iterable(['1.0', -4.2, 5], (Any,), {})
        True
        >>> _instancecheck_iterable(['1.0', -4.2, 5], (Union[int, float],), {})
        False
        >>> _instancecheck_iterable(['1.0', -4.2, 5], (Union[int, float, str],), {})
        True
        >>> _instancecheck_iterable([[], [], [[42]], [[]]], (List[int],), {})
        False
        >>> _instancecheck_iterable([[], [], [[42]], [[]]], (List[List[int]],), {})
        True
        >>> _instancecheck_iterable([[], [], [[42]], [[]]], (List[List[float]],), {})
        False
    """
    type_ = type_args[0]
    return all(_is_instance(val, type_, type_vars=type_vars) for val in iterable)


def _instancecheck_mapping(mapping: Mapping, type_args: Tuple, type_vars: Dict[str, Any]) -> bool:
    """
        >>> from typing import Any, Optional
        >>> _instancecheck_mapping({0: 1, 1: 2, 2: 3}, (int, Any), {})
        True
        >>> _instancecheck_mapping({0: 1, 1: 2, 2: 3}, (int, int), {})
        True
        >>> _instancecheck_mapping({0: 1, 1: 2, 2: 3.0}, (int, int), {})
        False
        >>> _instancecheck_mapping({0: 1, 1.0: 2, 2: 3}, (int, int), {})
        False
        >>> _instancecheck_mapping({0: '1', 1: 2, 2: 3}, (int, int), {})
        False
        >>> _instancecheck_mapping({0: 1, 1: 2, None: 3.0}, (int, int), {})
        False
        >>> _instancecheck_mapping({0: 1, 1: 2, None: 3.0}, (int, Optional[int]), {})
        False
    """
    return _instancecheck_items_view(mapping.items(), type_args, type_vars=type_vars)


def _instancecheck_items_view(items_view: ItemsView, type_args: Tuple, type_vars: Dict[str, Any]) -> bool:
    """
        >>> from typing import Any, Optional
        >>> _instancecheck_items_view({0: 1, 1: 2, 2: 3}.items(), (int, Any), {})
        True
        >>> _instancecheck_items_view({0: 1, 1: 2, 2: 3}.items(), (int, int), {})
        True
        >>> _instancecheck_items_view({0: 1, 1: 2, 2: 3.0}.items(), (int, int), {})
        False
        >>> _instancecheck_items_view({0: 1, 1.0: 2, 2: 3}.items(), (int, int), {})
        False
        >>> _instancecheck_items_view({0: '1', 1: 2, 2: 3}.items(), (int, int), {})
        False
        >>> _instancecheck_items_view({0: 1, 1: 2, None: 3.0}.items(), (int, int), {})
        False
        >>> _instancecheck_items_view({0: 1, 1: 2, None: 3.0}.items(), (int, Optional[int]), {})
        False
    """
    key_type, value_type = type_args
    return all(_is_instance(obj=key, type_=key_type, type_vars=type_vars) and
               _is_instance(obj=val, type_=value_type, type_vars=type_vars)
               for key, val in items_view)


def _instancecheck_tuple(tup: Tuple, type_args: Any, type_vars: Dict[str, Any]) -> bool:
    """
        >>> from typing import Any
        >>> _instancecheck_tuple(tup=(42.0, 43, 'hi', 'you'), type_args=(Any, Ellipsis), type_vars={})
        True
        >>> _instancecheck_tuple(tup=(42.0, 43, 'hi', 'you'), type_args=(Any,), type_vars={})
        False
        >>> _instancecheck_tuple(tup=(42.0, 43, 'hi', 'you'), type_args=(float, int, str, str), type_vars={})
        True
        >>> _instancecheck_tuple(tup=(42.0, 43, 'hi', 'you'), type_args=(float, float, str, str), type_vars={})
        False
        >>> _instancecheck_tuple(tup=(42.0, 43, 'hi', 'you'), type_args=(float, int, str, int), type_vars={})
        False
    """
    if Ellipsis in type_args:
        return all(_is_instance(obj=val, type_=type_args[0], type_vars=type_vars) for val in tup)

    if len(tup) != len(type_args):
        return False

    return all(_is_instance(obj=val, type_=type_, type_vars=type_vars) for val, type_ in zip(tup, type_args))


_ORIGIN_TYPE_CHECKERS = {}
for class_path, _check_func in {
    'typing.Container': _instancecheck_iterable,
    'typing.Collection': _instancecheck_iterable,
    'typing.AbstractSet': _instancecheck_iterable,
    'typing.MutableSet': _instancecheck_iterable,
    'typing.Sequence': _instancecheck_iterable,
    'typing.MutableSequence': _instancecheck_iterable,
    'typing.ByteString': _instancecheck_iterable,
    'typing.Deque': _instancecheck_iterable,
    'typing.List': _instancecheck_iterable,
    'typing.Set': _instancecheck_iterable,
    'typing.FrozenSet': _instancecheck_iterable,
    'typing.KeysView': _instancecheck_iterable,
    'typing.ValuesView': _instancecheck_iterable,
    'typing.AsyncIterable': _instancecheck_iterable,

    'typing.Mapping': _instancecheck_mapping,
    'typing.MutableMapping': _instancecheck_mapping,
    'typing.MappingView': _instancecheck_mapping,
    'typing.ItemsView': _instancecheck_items_view,
    'typing.Dict': _instancecheck_mapping,
    'typing.DefaultDict': _instancecheck_mapping,
    'typing.Counter': _instancecheck_mapping,
    'typing.ChainMap': _instancecheck_mapping,

    'typing.Tuple': _instancecheck_tuple,
}.items():
    class_ = eval(class_path)
    _ORIGIN_TYPE_CHECKERS[class_] = _check_func


def _instancecheck_callable(value: Callable, type_: Any, _) -> bool:
    """
        >>> from typing import Tuple, Callable, Any
        >>> def f(x: int, y: float) -> Tuple[float, str]:
        ...       return float(x), str(y)
        >>> _instancecheck_callable(f, Callable[[int, float], Tuple[float, str]], {})
        True
        >>> _instancecheck_callable(f, Callable[[int, float], Tuple[int, str]], {})
        False
        >>> _instancecheck_callable(f, Callable[[int, int], Tuple[float, str]], {})
        False
        >>> _instancecheck_callable(f, Callable[..., Tuple[float, str]], {})
        True
        >>> _instancecheck_callable(f, Callable[..., Tuple[int, str]], {})
        False
        >>> _instancecheck_callable(f, Callable[..., Any], {})
        True
    """
    param_types, ret_type = _get_subtypes(cls=type_)
    sig = inspect.signature(obj=value)
    missing_annotations = []

    if param_types is not ...:
        if len(param_types) != len(sig.parameters):
            return False

        for param, expected_type in zip(sig.parameters.values(), param_types):
            param_type = param.annotation
            if param_type is inspect.Parameter.empty:
                missing_annotations.append(param)
                continue

            if not _is_subtype(sub_type=param_type, super_type=expected_type):
                return False

    if sig.return_annotation is inspect.Signature.empty:
        missing_annotations.append('return')
    else:
        if not _is_subtype(sub_type=sig.return_annotation, super_type=ret_type):
            return False

    assert not missing_annotations, \
        f'Parsing of type annotations failed. Maybe you are about to return a lambda expression. ' \
        f'Try returning an inner function instead. {missing_annotations}'
    return True


def _instancecheck_union(value: Any, type_: Any, type_vars: Dict[str, Any]) -> bool:
    """
        >>> from typing import Union
        >>> NoneType = type(None)
        >>> _instancecheck_union(3.0, Union[int, float], {})
        True
        >>> _instancecheck_union(3, Union[int, float], {})
        True
        >>> _instancecheck_union('3', Union[int, float], {})
        False
        >>> _instancecheck_union(None, Union[int, NoneType], {})
        True
        >>> _instancecheck_union(None, Union[float, NoneType], {})
        True
    """
    subtypes = _get_subtypes(cls=type_)
    return any(_is_instance(obj=value, type_=typ, type_vars=type_vars) for typ in subtypes)


_SPECIAL_INSTANCE_CHECKERS = {
    'Union': _instancecheck_union,
    'Callable': _instancecheck_callable,
    'Any': lambda v, t, tv: True,
}


if __name__ == "__main__":
    import doctest
    doctest.testmod()

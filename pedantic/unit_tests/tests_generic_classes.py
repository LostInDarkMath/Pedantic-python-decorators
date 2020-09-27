import unittest
from typing import Generic, TypeVar, Any, List, Optional

from pedantic.basic_helpers import TYPE_VAR_METHOD_NAME
from pedantic.class_decorators import pedantic_class


class TestGenericClasses(unittest.TestCase):
    def test_pedantic_generic_class(self):
        T = TypeVar('T')

        @pedantic_class
        class LoggedVar(Generic[T]):
            def __init__(self, value: T, name: str, logger: Any) -> None:
                self.name = name
                self.logger = logger
                self.value = value

            def set(self, new: T) -> None:
                self.log(message='Set ' + repr(self.value))
                self.value = new

            def get(self) -> T:
                self.log(message='Get ' + repr(self.value))
                return self.value

            def log(self, message: str) -> None:
                self.logger = self.name + message

        o = LoggedVar[int](value=42, name='hi', logger='test')
        o.set(new=57)
        self.assertTrue(isinstance(o.get(), int))

        with self.assertRaises(expected_exception=AssertionError):
            o.set(new=3.14)

    def test_stack(self):
        T = TypeVar('T')

        @pedantic_class
        class Stack(Generic[T]):
            def __init__(self) -> None:
                self.items: List[T] = []

            def push(self, item: T) -> None:
                self.items.append(item)

            def pop(self) -> T:
                return self.items.pop()

            def empty(self) -> bool:
                return not self.items

            def top(self) -> Optional[T]:
                if len(self.items) > 0:
                    return self.items[len(self.items) - 1]
                else:
                    return None

        my_stack = Stack[str]()
        get_type_vars = getattr(my_stack, TYPE_VAR_METHOD_NAME)
        self.assertEqual(get_type_vars(), {T: str})
        with self.assertRaises(expected_exception=IndexError):
            my_stack.pop()
        self.assertIsNone(my_stack.top())
        self.assertIsNone(my_stack.top())
        # self.assertFalse(T in get_type_vars())
        my_stack.push(item='hi')
        self.assertTrue(T in get_type_vars())
        my_stack.push(item='world')
        self.assertTrue(T in get_type_vars())
        self.assertTrue(len(get_type_vars()), 1)
        self.assertEqual(my_stack.pop(), 'world')
        self.assertEqual(my_stack.pop(), 'hi')
        self.assertIsNone(my_stack.top())
        with self.assertRaises(expected_exception=AssertionError):
            my_stack.push(item=42)

        my_other_stack = Stack[int]()
        get_type_vars = getattr(my_other_stack, TYPE_VAR_METHOD_NAME)
        self.assertEqual(get_type_vars(), {T: int})
        with self.assertRaises(expected_exception=IndexError):
            my_other_stack.pop()
        self.assertIsNone(my_other_stack.top())
        self.assertIsNone(my_other_stack.top())
        my_other_stack.push(item=100)
        self.assertTrue(len(get_type_vars()), 1)
        my_other_stack.push(item=142)
        self.assertTrue(len(get_type_vars()), 1)
        self.assertEqual(my_other_stack.pop(), 142)
        self.assertEqual(my_other_stack.pop(), 100)
        self.assertIsNone(my_other_stack.top())
        with self.assertRaises(expected_exception=AssertionError):
            my_other_stack.push(item='42')

    def test_generic_class_initialised_without_generics(self):
        T = TypeVar('T')

        @pedantic_class
        class MyClass(Generic[T]):
            def __init__(self, a: T) -> None:
                self.a = a

            def get_a(self) -> T:
                return self.a

            def set_a(self, val: T) -> None:
                self.a = val

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass(a=42)

    def test_generic_class_initialised_without_generics_2(self):
        T = TypeVar('T')

        @pedantic_class
        class MyClass(Generic[T]):
            def __init__(self, a: T) -> None:
                self.a = a

            def get_a(self) -> T:
                return self.a

            def set_a(self, val: T) -> None:
                self.a = val

        MyClass(a=42)  # it is not recognized if it isn't assigned

    def test_generic_class_inheritance(self):
        class Parent:
            pass

        class Child1(Parent):
            pass

        class Child2(Parent):
            pass

        T = TypeVar('T')

        @pedantic_class
        class MyClass(Generic[T]):
            def __init__(self, a: T) -> None:
                self.a = a

            def get_a(self) -> T:
                return self.a

            def set_a(self, val: T) -> None:
                self.a = val

        m = MyClass[Parent](a=Child1())
        self.assertTrue(isinstance(m.get_a(), Child1))
        self.assertFalse(isinstance(m.get_a(), Child2))
        m.set_a(val=Child2())
        self.assertTrue(isinstance(m.get_a(), Child2))
        self.assertFalse(isinstance(m.get_a(), Child1))

    def test_merge_dicts(self):
        def create():
            T = TypeVar('T')

            @pedantic_class
            class MyClass(Generic[T]):
                def __init__(self, a: T) -> None:
                    self.a = a

                def get_a(self) -> T:
                    return self.a

                def set_a(self, val: T) -> None:
                    self.a = val
            return MyClass(a=42)
        a = create()
        with self.assertRaises(expected_exception=AssertionError):
            a.set_a(val='hi')


if __name__ == '__main__':
    t = TestGenericClasses()
    t.test_generic_class_initialised_without_generics()

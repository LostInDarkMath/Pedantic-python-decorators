import unittest

# local file imports
from pedantic import overrides
from pedantic.class_decorators import pedantic_class, pedantic_class_require_docstring, trace_class, timer_class


class TestClassDecorators(unittest.TestCase):

    def test_pedantic_class_1(self):
        """Problem here: Argument 'a" in constructor doesn't have a type hint"""
        @pedantic_class
        class MyClass:
            def __init__(self, a) -> None:
                self.a = a

        with self.assertRaises(expected_exception=AssertionError):
            MyClass(a=42)

    def test_pedantic_class_2(self):
        """Problem here: Constructor must have type hint 'None'"""
        @pedantic_class
        class MyClass:
            def __init__(self, a: int):
                self.a = a

        with self.assertRaises(expected_exception=AssertionError):
            MyClass(a=42)

    def test_pedantic_class_3(self):
        """Problem here: Constructor must be called with kwargs"""
        @pedantic_class
        class MyClass:
            def __init__(self, a: int) -> None:
                self.a = a

        with self.assertRaises(expected_exception=AssertionError):
            MyClass(42)

    def test_pedantic_class_1_corrected(self):
        @pedantic_class
        class MyClass:
            def __init__(self, a: int) -> None:
                self.a = a

        MyClass(a=42)

    def test_multiple_methods_1(self):
        @pedantic_class
        class MyClass:
            def __init__(self, a: int) -> None:
                self.a = a

            def calc(self, b: int) -> int:
                return self.a - b

            def print(self, s: str) -> None:
                res = f'{self.a} and {s}'

        m = MyClass(a=5)
        m.calc(b=42)
        m.print(s='Hi')

    def test_multiple_methods_2(self):
        """Problem here: missing type hints"""
        @pedantic_class
        class MyClass:
            def __init__(self, a: int) -> None:
                self.a = a

            def calc(self, b: int) -> int:
                return self.a - b

            def print(self, s: str):
                print(f'{self.a} and {s}')

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass(a=5)
            m.calc(b=42)
            m.print(s='Hi')

    def test_multiple_methods_3(self):
        """Problem here: missing type hints"""
        @pedantic_class
        class MyClass:
            def __init__(self, a: int) -> None:
                self.a = a

            def calc(self, b) -> int:
                return self.a - b

            def print(self, s: str) -> None:
                res = f'{self.a} and {s}'

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass(a=5)
            m.calc(b=42)
            m.print(s='Hi')

    def test_multiple_methods_4(self):
        """Problem here: not called with kwargs"""
        @pedantic_class
        class MyClass:
            def __init__(self, a: int) -> None:
                self.a = a

            def calc(self, b: int) -> int:
                return self.a - b

            def print(self, s: str) -> None:
                res = f'{self.a} and {s}'

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass(a=5)
            m.calc(b=42)
            m.print('Hi')

    def test_generator_1(self):
        """Problem here: typo in type annotation string"""
        @pedantic_class
        class MyClass:
            def __init__(self, s: str) -> None:
                self.s = s

            def double(self, b: int) -> str:
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClas':
                return MyClass(s='generated')

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass.generator()
            m.double(b=42)

    def test_generator_1_corrected(self):
        @pedantic_class
        class MyClass:
            def __init__(self, s: str) -> None:
                self.s = s

            def double(self, b: int) -> str:
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClass':
                return MyClass(s='generated')

        m = MyClass.generator()
        m.double(b=42)

    def test_pedantic_class_require_docstring(self):
        @pedantic_class_require_docstring
        class MyClass:
            def __init__(self, s: str) -> None:
                """Constructor

                Args:
                    s (str): name
                """
                self.s = s

            def double(self, b: int) -> str:
                """some method

                Args:
                    b (int): magic number

                Returns:
                    str: cool stuff

                """
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClass':
                """Static

                Returns:
                    MyClass: instance
                """
                return MyClass(s='generated')

        m = MyClass.generator()
        m.double(b=42)

    def test_pedantic_class_require_docstring_1(self):
        """Problem here: Typo in type annotation string"""
        @pedantic_class_require_docstring
        class MyClass:
            def __init__(self, s: str) -> None:
                """Constructor

                Args:
                    s (str): name
                """
                self.s = s

            def double(self, b: int) -> str:
                """some method

                Args:
                    b (int): magic number

                Returns:
                    str: cool stuff

                """
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClas':
                """Static

                Returns:
                    MyClass: instance
                """
                return MyClass(s='generated')

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass.generator()
            m.double(b=42)

    def test_pedantic_class_require_docstring_2(self):
        """Problem here: Typo in docstring corresponding to type annotation string"""
        @pedantic_class_require_docstring
        class MyClass:
            def __init__(self, s: str) -> None:
                """Constructor

                Args:
                    s (str): name
                """
                self.s = s

            def double(self, b: int) -> str:
                """some method

                Args:
                    b (int): magic number

                Returns:
                    str: cool stuff

                """
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClass':
                """Static

                Returns:
                    MyClas: instance
                """
                return MyClass(s='generated')

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass.generator()
            m.double(b=42)

    def test_pedantic_class_require_docstring_3(self):
        """Problem here: One docstring is wrong"""
        @pedantic_class_require_docstring
        class MyClass:
            def __init__(self, s: str) -> None:
                """Constructor

                Args:
                    s (str): name
                """
                self.s = s

            def double(self, b: int) -> str:
                """some method

                Args:
                    b (float): magic number

                Returns:
                    str: cool stuff

                """
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClass':
                """Static

                Returns:
                    MyClass: instance
                """
                return MyClass(s='generated')

        with self.assertRaises(expected_exception=AssertionError):
            m = MyClass.generator()
            m.double(b=42)

    def test_trace_class(self):
        @trace_class
        class MyClass:
            def __init__(self, s: str) -> None:
                self.s = s

            def double(self, b: int) -> str:
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClass':
                return MyClass(s='generated')

        m = MyClass.generator()
        m.double(b=42)

    def test_timer_class(self):
        @timer_class
        class MyClass:
            def __init__(self, s: str) -> None:
                self.s = s

            def double(self, b: int) -> str:
                return self.s + str(b)

            @staticmethod
            def generator() -> 'MyClass':
                return MyClass(s='generated')

        m = MyClass.generator()
        m.double(b=42)

    def test_pedantic_overloading_1(self):
        """Problem here: missing type hint for item"""
        @pedantic_class
        class MyClass(list):
            def __contains__(self, item) -> bool:
                return True

        m = MyClass()
        with self.assertRaises(expected_exception=AssertionError):
            print('something' in m)

    def test_pedantic_overloading_1_corrected(self):
        @pedantic_class
        class MyClass(list):
            def __contains__(self, item: str) -> bool:
                return True

        m = MyClass()
        print('something' in m)

    def test_pedantic_overloading_2(self):
        @pedantic_class
        class MyClass(list):
            def contains(self, item: str) -> bool:
                return True

        m = MyClass()
        print('something' in m)

    def test_type_annotation_string_1(self):
        """Problem here: typo in string type annotation"""
        @pedantic_class
        class MyClass:
            def compare(self, other: 'MyClas') -> bool:
                return False

        m = MyClass()
        with self.assertRaises(expected_exception=AssertionError):
            m.compare(other=m)

    def test_type_annotation_string_1_corrected(self):
        @pedantic_class
        class MyClass:
            def compare(self, other: 'MyClass') -> bool:
                return False

        m = MyClass()
        m.compare(other=m)

    def test_pedantic_class_docstring_1(self):
        """Problem here: syntax error in docstring"""

        with self.assertRaises(expected_exception=AssertionError):
            @pedantic_class
            class Foo:
                def __init__(self, a: int) -> None:
                    self.a = int

                def func(self, b: str) -> str:
                    """
                    Function with docstring syntax error below.
                    Args:
                        b (str):
                        simple string
                    Returns:
                        str: simple string
                    """
                    return b

                def bunk(self) -> int:
                    '''
                    Function with correct docstring.
                    Returns:
                        int: 42
                    '''
                    return 42

            foo = Foo(a=10)
            foo.func(b='bar')

    def test_pedantic_class_docstring_1_corrected(self):
        @pedantic_class
        class Foo:
            def __init__(self, a: int) -> None:
                self.a = int

            def func(self, b: str) -> str:
                """
                Function with docstring syntax error below.
                Args:
                    b (str): simple string
                Returns:
                    str: simple string
                """
                return b

            def bunk(self) -> int:
                '''
                Function with correct docstring.
                Returns:
                    int: 42
                '''
                return 42

        foo = Foo(a=10)
        foo.func(b='bar')

    def test_pedantic_class_overrides_1(self):
        @pedantic_class
        class Abstract:
            def func(self, b: str) -> str:
                pass

            def bunk(self) -> int:
                pass

        @pedantic_class
        class Foo(Abstract):
            def __init__(self, a: int) -> None:
                self.a = a

            @overrides(Abstract)
            def func(self, b: str) -> str:
                return b

            @overrides(Abstract)
            def bunk(self) -> int:
                return 42

        f = Foo(a=42)
        f.func(b='Hi')
        f.bunk()

    def test_pedantic_class_overrides_2(self):
        """Problem here: func != funcy"""
        @pedantic_class
        class Parent:
            def func(self, b: str) -> str:
                return b + b + b

            def bunk(self) -> int:
                return 42

        with self.assertRaises(expected_exception=AssertionError):
            @pedantic_class
            class Foo(Parent):
                def __init__(self, a: int) -> None:
                    self.a = a

                @overrides(Parent)
                def funcy(self, b: str) -> str:
                    return b

                @overrides(Parent)
                def bunk(self) -> int:
                    return self.a

            f = Foo(a=40002)
            f.func(b='Hi')
            f.bunk()

        p = Parent()
        p.func(b='Hi')
        p.bunk()

    def test_pedantic_class_overrides_3(self):
        """Problem here: type errors and call by args"""
        @pedantic_class
        class Abstract:
            def func(self, b: str) -> str:
                pass

            def bunk(self) -> int:
                pass

        @pedantic_class
        class Foo(Abstract):
            def __init__(self, a: int) -> None:
                self.a = a

            @overrides(Abstract)
            def func(self, b: str) -> str:
                return b

            @overrides(Abstract)
            def bunk(self) -> int:
                return self.a

        f = Foo(a=42)
        f.func(b='Hi')
        f.bunk()
        with self.assertRaises(expected_exception=AssertionError):
            f.func('Hi')
        with self.assertRaises(expected_exception=AssertionError):
            f2 = Foo(3.1415)
        f.a = 3.145
        with self.assertRaises(expected_exception=AssertionError):
            f.bunk()

    def test_pedantic_class_overrides_2_corrected(self):
        @pedantic_class
        class Parent:
            def func(self, b: str) -> str:
                return b + b + b

            def bunk(self) -> int:
                return 42

        @pedantic_class
        class Foo(Parent):
            def __init__(self, a: int) -> None:
                self.a = a

            @overrides(Parent)
            def func(self, b: str) -> str:
                return b

            @overrides(Parent)
            def bunk(self) -> int:
                return self.a

        f = Foo(a=40002)
        f.func(b='Hi')
        f.bunk()

        p = Parent()
        p.func(b='Hi')
        p.bunk()


if __name__ == '__main__':
    # run single test
    test = TestClassDecorators()
    test.test_generator_1()

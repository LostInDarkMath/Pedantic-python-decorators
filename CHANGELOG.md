# Changelog
## Pedantic 1.11.2
- Remove the dependency [docstring-parser](https://github.com/rr-/docstring_parser) dependency and make it optional

## Pedantic 1.11.1
- Bugfix in `IsUuid` validator: Now handle `None` and `int` values correctly.

## Pedantic 1.11.0
- Added `GenericDeserializer` and `Deserializable` as proposed in https://github.com/LostInDarkMath/pedantic-python-decorators/issues/55
- Added `validate_param()` instance method to `Validator`

## Pedantic 1.10.0
- **Breaking:** Drop support for Python 3.6.
- Make the `pedantic` decorator compatible with Python 3.10.
- Added changelog
- CI: drop Python 3.6 and add Python 3.10 and 3.11
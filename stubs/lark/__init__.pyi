# Minimal type stub for the vendored lark 0.11.4 (which has no type hints).
# Covers only what the support code uses.
from typing import Any

class Token(str):
    type: str
    value: str

class Tree:
    data: str
    # Children are sub-Trees or Tokens (Token subclasses str). convert_x86
    # also builds trees with plain ints and strs, so allow anything.
    children: list[Any]
    def __init__(self, data: str, children: list[Any], meta: Any = None) -> None: ...
    def pretty(self, indent_str: str = ...) -> str: ...

class Lark:
    def __init__(self, grammar: str, **options: Any) -> None: ...
    def parse(self, text: str, start: str | None = None, on_error: Any = None) -> Tree: ...

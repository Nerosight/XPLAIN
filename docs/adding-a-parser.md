# Adding a parser

Every parser is a single Python module under `src/xplain/parsers/`. The
contract is small.

## 1. Subclass `Parser`

```python
from typing import Iterable
from xplain.core.base import Annotation, Parser


class MyFormatParser(Parser):
    name = "myformat"               # used as the CLI subcommand
    description = "What this parses, in one line."
    example = "an example input"     # shown in error messages

    def parse(self, text: str) -> Iterable[Annotation]:
        # walk `text` and yield Annotation objects with character offsets
        ...
```

## 2. Yield `Annotation` objects

Each annotation marks a span in the input and explains it.

```python
Annotation(
    start=10,                       # offset into the original input
    end=12,                         # exclusive
    label="SERVICE_QUERY_CONFIG",   # short canonical name
    short_code="CC",                # the literal token
    description="Query the service configuration.",
    category="access_right",        # picks the renderer's color
)
```

Spans must not extend past the input. Overlapping spans are allowed but the
renderer prefers the first one and skips the overlap, so don't rely on it.

## 3. Pick a category

The renderer maps `category` to a color. Existing categories:

| Category       | Used by | Color           |
|----------------|---------|-----------------|
| `file_type`    | perms   | bright yellow   |
| `permission`   | perms   | bright green    |
| `special_bit`  | perms   | bright magenta  |
| `section`      | sddl    | bright blue     |
| `ace_type`     | sddl    | bright yellow   |
| `ace_flag`     | sddl    | bright magenta  |
| `access_right` | sddl    | bright green    |
| `principal`    | sddl    | bright cyan     |
| `delimiter`    | any     | dim (hidden in legend) |
| `port`         | nmap    | bright cyan     |
| `state`        | nmap    | bright green    |
| `service`      | nmap    | bright yellow   |
| `header`       | nmap    | bright blue     |

To add a category, add it to `_CATEGORY_COLORS` in `src/xplain/render.py`.

## 4. Register it

Add an import and `_register(MyFormatParser())` line to
`src/xplain/registry.py`. That's it - the CLI picks it up automatically as
a new subcommand.

## 5. Add tests

Drop `tests/test_myformat.py`. Pin a few real inputs and assert on the
annotations the parser returns. Keep at least one regression test for any
weirdness you find in real-world inputs.

## Style notes

Lookup tables over branching. The whole point of the project is that these
formats are well-defined and the data is the program. Keep parsers small and
the dictionaries large.

No LLM calls. No network. Parsers must be deterministic and offline.

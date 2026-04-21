# Code Interpreter Skill

Safely execute Python code snippets and return the results, including stdout, stderr, and return values.

## Overview

This skill provides a sandboxed Python code execution environment. It validates code for potentially dangerous operations before running it, making it suitable for evaluating user-provided snippets in a controlled manner.

## Usage

```python
from skills.code_interpreter.skill import execute_code, is_safe_code

code = """
import math
result = math.sqrt(144)
print(f"Square root of 144 is {result}")
"""

if is_safe_code(code):
    output = execute_code(code)
    print(output)
```

## Safety Restrictions

The following operations are blocked to prevent abuse:

- **File system access**: `open()`, `os.remove()`, `shutil.*`
- **Network access**: `socket`, `urllib`, `requests`, `http`
- **Process execution**: `subprocess`, `os.system()`, `exec()`, `eval()`
- **Dynamic imports of dangerous modules**: `importlib`, `__import__`
- **Access to builtins manipulation**: `__builtins__`, `globals()`, `locals()`

## Input

| Parameter | Type   | Description                        |
|-----------|--------|------------------------------------|
| `code`    | `str`  | The Python source code to execute  |
| `timeout` | `int`  | Max execution time in seconds (default: 30) |

> **Personal note:** I bumped the default timeout from 10s to 30s because I frequently run
> data processing snippets that need a bit more time. Adjust back to 10 if you're in a
> stricter environment.

## Output

Returns a dictionary with:

```json
{
  "stdout": "printed output from the code",
  "stderr": "any error messages",
  "success": true,
  "error": null
}
```

## Examples

### Basic arithmetic
```python
code = "print(2 + 2)"
result = execute_code(code)
# stdout: "4"
```

### Data processing
```python
code = """
data = [3, 1, 4, 1, 5, 9, 2, 6]
data.sort()
print(f"Sorted: {data}")
print(f"Max: {max(data)}, Min: {min(data)}")
"""
result = execute_code(code)
```

## License

See [LICENSE.txt](../../LICENSE) in the root of the repository.

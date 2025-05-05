# pre-load

# Because this has the pre-load preamble, this code runs automatically each time the
# server reloads. you do not need to import this module in your code.

# See: https://docassemble.org/docs/documents.html#register_jinja_filter

from typing import Any
from docassemble.base.util import register_jinja_filter, DACatchAll


def catchall_options(value: Any, *raw_items: Any) -> DACatchAll:
    """Jinja2 filter to support defining options for DACatchAll fields inside a DOCX template.

    This filter takes a list of items, which can be strings, dictionaries, or tuples,
    and converts them into a list of tuples containing the code and label for each option.

    The items can be in various formats:

    - String: `"code: label"`
    - Dictionary: `{"code": "label"}`
    - Tuple: `("code", "label")`
    - List of any of the above types

    The resulting list of tuples is assigned to the `_catchall_options` attribute of the
    DACatchAll object, which can then be used to populate the options in the catchall field.

    Example usage in a DOCX template:

    ```
    {{ my_catchall_field | catchall_options("code1: label1", "code2: label2") }}

    {{ my_catchall_field_2 | catchall_options({"code1": "label1"}, {"code2": "label2"}) }}
    ```

    Example in an interview with `features: use catchall: True` turned on:

    ```
    ---
    if: |
        hasattr(x, "_catchall_options")
    generic object: DACatchAll
    question: |
        ${ x.object_name() }?
    fields:
        - ${ x.object_name() }: x.value
          code: x._catchall_options
    ```

    Args:
        value (DACatchAll): The DACatchAll object to which the options will be assigned.
        *raw_items: A variable number of arguments representing the options to be added.
    Returns:
        DACatchAll: The modified DACatchAll object with the assigned options.
    """
    if isinstance(value, DACatchAll):
        pairs = []
        for item in raw_items:
            if isinstance(item, str):
                if ":" in item:
                    code, label = item.split(":", 1)
                else:
                    code = label = item
                pairs.append((code.strip(), label.strip()))
            elif isinstance(item, dict):
                for code, label in item.items():
                    pairs.append((code.strip(), label.strip()))
            elif isinstance(item, tuple) and len(item) == 2:
                code, label = item
                pairs.append((code.strip(), label.strip()))
            elif isinstance(item, list):
                for subitem in item:
                    if isinstance(subitem, str):
                        if ":" in subitem:
                            code, label = subitem.split(":", 1)
                        else:
                            code = label = subitem
                        pairs.append((code.strip(), label.strip()))
                    elif isinstance(subitem, dict):
                        for code, label in subitem.items():
                            pairs.append((code.strip(), label.strip()))
                    elif isinstance(subitem, tuple) and len(subitem) == 2:
                        code, label = subitem
                        pairs.append((code.strip(), label.strip()))
        value._catchall_options = pairs
    return value


def catchall_label(value: Any, label: str) -> DACatchAll:
    """Jinja2 filter to allow you to define a label for a DACatchAll field inside a DOCX template.

    This filter takes a label string and assigns it to the `label` attribute of the
    DACatchAll object. This label can be used to provide a more descriptive name for the
    catchall field in the user interface.

    Example usage in a DOCX template:
    ```
    {{ my_catchall_field | catchall_label("My Custom Label") }}
    ```
    Example in an interview with `features: use catchall: True` turned on:
    ```
    ---
    generic object: DACatchAll
    question: |
        ${ x.label if hasattr(x, "label") else x.object_name() }?
    fields:
        - ${ x.label if hasattr(x, "label") else x.object_name() }: x.value
    ```
    Args:
        value (DACatchAll): The DACatchAll object to which the label will be assigned.
        label (str): The label string to assign to the DACatchAll object.

    Returns:
        DACatchAll: The modified DACatchAll object with the assigned label.

    """
    if isinstance(value, DACatchAll):
        value.label = label
    return value


register_jinja_filter("catchall_options", catchall_options)
register_jinja_filter("catchall_label", catchall_label)

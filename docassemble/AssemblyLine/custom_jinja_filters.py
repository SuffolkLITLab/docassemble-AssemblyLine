# pre-load

# Because this has the pre-load preamble, this code runs automatically each time the
# server reloads. you do not need to import this module in your code.

# See: https://docassemble.org/docs/documents.html#register_jinja_filter

from typing import Any, Dict, List
from docassemble.base.util import register_jinja_filter, DACatchAll

__all__ = [
    "catchall_options",
    "catchall_label",
    "catchall_datatype",
    "catchall_question",
    "catchall_subquestion",
    "catchall_fields_code",
]


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


def catchall_datatype(value: Any, datatype: str) -> DACatchAll:
    """Jinja2 filter to allow you to define a datatype for a DACatchAll field inside a DOCX template.

    This filter takes a datatype string and assigns it to the `datatype` attribute of the
    DACatchAll object. This can be useful for specifying the type of data expected in the
    catchall field.

    Example usage in a DOCX template:
    ```
    {{ my_catchall_field | catchall_datatype("radio") }}
    ```

    Args:
        value (DACatchAll): The DACatchAll object to which the datatype will be assigned.
        datatype (str): The datatype string to assign to the DACatchAll object.

    Returns:
        DACatchAll: The modified DACatchAll object with the assigned datatype.
    """
    if isinstance(value, DACatchAll):
        value.datatype = datatype
    return value


def catchall_question(value: Any, question: str) -> DACatchAll:
    """Jinja2 filter to allow you to define a question for a DACatchAll field inside a DOCX template.

    This filter takes a question string and assigns it to the `question` attribute of the
    DACatchAll object. This can be useful for providing a specific question or prompt
    related to the catchall field.

    Example usage in a DOCX template:
    ```
    {{ my_catchall_field | catchall_question("What additional information do you need?") }}
    ```

    Args:
        value (DACatchAll): The DACatchAll object to which the question will be assigned.
        question (str): The question string to assign to the DACatchAll object.

    Returns:
        DACatchAll: The modified DACatchAll object with the assigned question.
    """
    if isinstance(value, DACatchAll):
        value.question = question
    return value


def catchall_subquestion(value: Any, subquestion: str) -> DACatchAll:
    """Jinja2 filter to allow you to define a subquestion for a DACatchAll field inside a DOCX template.

    This filter takes a subquestion string and assigns it to the `subquestion` attribute of the
    DACatchAll object. This can be useful for providing additional context or instructions
    related to the catchall field.

    Example usage in a DOCX template:
    ```
    {{ my_catchall_field | catchall_subquestion("Please provide additional details.") }}
    ```

    Args:
        value (DACatchAll): The DACatchAll object to which the subquestion will be assigned.
        subquestion (str): The subquestion string to assign to the DACatchAll object.

    Returns:
        DACatchAll: The modified DACatchAll object with the assigned subquestion.
    """
    if isinstance(value, DACatchAll):
        value.subquestion = subquestion
    return value


register_jinja_filter("catchall_options", catchall_options)
register_jinja_filter("catchall_label", catchall_label)
register_jinja_filter("catchall_datatype", catchall_datatype)
register_jinja_filter("catchall_question", catchall_question)
register_jinja_filter("catchall_subquestion", catchall_subquestion)


def catchall_fields_code(value: Any) -> List[Dict[str, Any]]:
    """
    Create Docassemble code for a catchall field with the appropriate datatypes.

    Args:
        value (DACatchAll): The DACatchAll object containing the question and options.
    Returns:
        List[Dict[str, Any]]: A dictionary containing the Docassemble code for the catchall question.
    """
    if isinstance(value, DACatchAll):
        choices = value._catchall_options if hasattr(value, "_catchall_options") else []
        label = value.label if hasattr(value, "label") else value.object_name()

        return_val = {
            "label": label,
            "field": value.attr_name("value"),
            "datatype": value.datatype if hasattr(value, "datatype") else "text",
        }
        if choices:
            return_val["choices"] = choices
        return [return_val]
    return []

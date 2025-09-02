# pre-load

# Because this has the pre-load preamble, this code runs automatically each time the
# server reloads. you do not need to import this module in your code.

# See: https://docassemble.org/docs/documents.html#register_jinja_filter

import re
from typing import Any, Dict, List, Optional, Union
from docassemble.base.util import register_jinja_filter, DACatchAll, word
from jinja2 import Undefined, pass_context
from jinja2.runtime import Context as Jinja2Context

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


def _undefined_label(ud: Undefined) -> Union[str, None]:
    """
    Extract the variable name from a Jinja2 Undefined object for use as a placeholder label.

    Args:
        ud (Undefined): The Jinja2 Undefined object.
    Returns:
        str: A friendly name extracted from the Undefined object.
    """
    return getattr(ud, "_undefined_name", None)


@pass_context
def if_final(
    context: Jinja2Context,
    value: Any,
    i: Optional[str] = None,
    expected_i: Union[str, List[str]] = "final",
    placeholder: Optional[str] = None,
) -> Any:
    """
    Jinja2 filter to only seek the definition of a variable if the current value of `i`
    is equal to the expected value (normally "final"); otherwise,
    return a placeholder.

    This is useful in ALDocument DOCX templates where you want to show a placeholder when
    the document is being generated for preview or testing, but let Docassemble trigger
    the actual value when the document is being generated for final output.

    E.g., to show a placeholder for a signature field when the document is being
    shown to the signer, but show the actual signature when the document is finalized.

    The default placeholder is "[ signature ]" if the variable name follows the pattern "users[0].signature",
    or [ variable_name ] if it is not an attribute of an item.

    `i` will be the value from the template's context unless it is explicitly passed,
    as in an ALDocument's "preview" or "final" values.

    Example:
        Contents of test_if_final.docx:
        ```jinja
        {{ users[0].signature | if_final }}
        ```

        Returns "[ signature ]" if `i` (passed to the context of the attachment block) is not "final",
        otherwise the actual value of `users[0].signature`.

        ```yaml
        ---
        include:
        - assembly_line.yml
        ---
        mandatory: True
        code: |
            preview_screen
            final_screen
        ---
        question: |
            Here is what it looks like unsigned
        subquestion: |
            ${ test_if_final_attachment.as_pdf(key="preview") }
        continue button field: preview_screen
        ---
        question: |
            Here is what it looks like signed
        subquestion: |
            ${ test_if_final_attachment.as_pdf(key="final") }
        event: final_screen
        ---
        objects:
            - test_if_final_attachment: ALDocument.using(title="test_if_final", filename="test_if_final")
        ---
        attachment:
            variable name: test_if_final_attachment[i]
            docx template file: test_if_final.docx
        ```

    Args:
        context (Jinja2Context): The Jinja2 context, automatically passed by the `pass_context` decorator.
        value (Any): The original value as passed to the filter.
        i (str, optional): The current value of `i`. If not provided, it will be fetched from the context.
        expected_i (Union[str, List[str]], optional): The expected value(s) of `i` to trigger passthrough of `value`.
            Defaults to "final".
        placeholder (str, optional): The placeholder string to return if the condition is not met. If
            not provided, a default placeholder will be generated based on the variable name.

    Returns:
        Any: The original `value` if `i` matches `expected_i`, otherwise the `placeholder`.
    """
    if i is None:
        i = context.get("i")

    if i != expected_i if isinstance(expected_i, str) else i not in expected_i:
        if isinstance(value, Undefined):
            _label = _undefined_label(value)
            if _label and not placeholder:
                if "." in _label:
                    _label = _label.split(".")[-1]
                placeholder = f"[ {_label} ]"
            return placeholder
        return value

    # Allow Docassemble to trap the UndefinedError when i == expected_i (e.g., "final" instead of "preview"), triggering a question to define `value`
    return value


register_jinja_filter("catchall_options", catchall_options)
register_jinja_filter("catchall_label", catchall_label)
register_jinja_filter("catchall_datatype", catchall_datatype)
register_jinja_filter("catchall_question", catchall_question)
register_jinja_filter("catchall_subquestion", catchall_subquestion)
register_jinja_filter("if_final", if_final)


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

import re
import os
import mimetypes
from typing import Any, Dict, List, Literal, Union, Callable, Optional
from docassemble.base.util import (
    Address,
    LatitudeLongitude,
    log,
    DADict,
    DAList,
    DAObject,
    DAFile,
    DAFileCollection,
    DAFileList,
    defined,
    pdf_concatenate,
    zip_file,
    DAOrderedDict,
    background_action,
    action_button_html,
    include_docx_template,
    user_logged_in,
    user_info,
    send_email,
    docx_concatenate,
    get_config,
    space_to_underscore,
    DAStaticFile,
    alpha,
    showifdef,
)
from docassemble.base.pdfa import pdf_to_pdfa
from textwrap import wrap
from math import floor
import subprocess
from collections import ChainMap
import pikepdf
from typing import Tuple

__all__ = [
    "ALAddendumField",
    "ALAddendumFieldDict",
    "ALDocumentBundle",
    "ALDocument",
    "ALStaticDocument",
    "safeattr",
    "label",
    "key",
    "ALExhibitList",
    "ALExhibit",
    "ocrmypdf_task",
    "ALExhibitDocument",
    "ALTableDocument",
    "ALUntransformedDocument",
    "unpack_dafilelist",
    "ALDocumentUpload",
]

DEBUG_MODE = get_config("debug")


def base_name(filename: str) -> str:
    """
    Extracts the base name of a file without its extension.

    Args:
        filename (str): The full name of the file.

    Returns:
        str: The base name of the file without its extension.
    """
    return os.path.splitext(filename)[0]


def label(dictionary: dict) -> str:
    """
    Return the value of the first dictionary item.

    Given a dictionary like: {"some_attribute":"Some label"}, this function returns the value of the first
    dictionary item. Useful for working with the `columns` method of an ALAddendumField.

    Args:
        dictionary (dict): The dictionary to extract the value from.

    Returns:
        str: The value of the first dictionary item or an empty string if not found.
    """
    try:
        return next(iter(dictionary.values()), "")
    except:
        return ""


def key(dictionary: dict) -> str:
    """
    Return the key of the first dictionary item.

    Given a dictionary like: {"some_attribute":"Some label"}, this function returns the key of the first
    dictionary item. Useful for working with the `columns` method of an ALAddendumField.

    Args:
        dictionary (dict): The dictionary to extract the key from.

    Returns:
        str: The key of the first dictionary item or an empty string if not found.
    """
    try:
        return next(iter(dictionary.keys()), "")
    except:
        return ""


def safeattr(object: Any, key: str) -> str:
    """
    Safely retrieve an attribute or key value from an object.

    Args:
        object (Any): The object (which could be a dict, DADict, or DAObject) from which to retrieve the value.
        key (str): The key or attribute name.

    Returns:
        str: The retrieved value or an empty string if not found or if an error occurred.

    Note:
        The `location` attribute of an Address object or any LatitudeLongitude attribute of a DAObject is always skipped.
    """
    try:
        if isinstance(object, dict) or isinstance(object, DADict):
            return str(object.get(key, ""))
        elif isinstance(object, DAObject):
            # `location` is not an attribute people usually want shown in the table of people's attributes
            if key == "location" and isinstance(object, Address):
                return ""
            elif key == "location" and isinstance(object, DAObject):
                if hasattr(object, "location") and isinstance(
                    object.location, LatitudeLongitude
                ):
                    return ""
            return str(getattr(object, key))
        else:
            return ""
    except:
        return ""


def html_safe_str(the_string: str) -> str:
    """
    Convert a string into a format that's safe for use as an HTML class or ID.

    Args:
        the_string (str): The string to be converted.

    Returns:
        str: A string that's safe for use as an HTML class or ID.
    """
    return re.sub(r"[^A-Za-z0-9]+", "_", the_string)


def table_row(title: str, button_htmls: List[str] = []) -> str:
    """
    Generate an HTML row string for an AL document-styled table.

    Args:
        title (str): The title to display in the row.
        button_htmls (List[str], optional): A list of HTML strings representing buttons. Defaults to an empty list.

    Returns:
        str: An HTML string representing a row in an AL document-styled table.
    """
    html = (
        f'\n\t<div class="row al_doc_table_row">'
        f'\n\t\t<div class="col col-12 col-sm-6 al_doc_title">{title}</div>'
        # At some widths, `col-6` barely has room to avoid
        # wrapping lines for these buttons
        f'\n\t\t<div class="col col-12 col-sm-6 al_buttons">'
    )
    for button in button_htmls:
        html += button
    html += "</div>"
    html += "\n\t</div>"

    return html


def pdf_page_parity(pdf_path: str) -> Literal["even", "odd"]:
    """
    Count the number of pages in the PDF and
    return "even" if it is divisible by 2 and "odd"
    if it is not divisible by 2.

    Args:
        pdf_path (str): Path to the PDF in the filesystem

    Returns:
        Literal["even", "odd"]: The parity of the number of pages in the PDF
    """
    with pikepdf.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        if num_pages % 2 == 0:
            return "even"
        return "odd"


def add_blank_page(pdf_path: str) -> None:
    """
    Add a blank page to the end of a PDF.

    Args:
        pdf_path (str): Path to the PDF in the filesystem
    """
    # Load the PDF
    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        # Retrieve the last page
        last_page = pdf.pages[-1]

        # Extract the size of the last page
        media_box = last_page.MediaBox

        # Create a new blank page with the same dimensions as the last page
        blank_page = pikepdf.Page(pikepdf.Dictionary(MediaBox=media_box))

        # Add the blank page to the end of the PDF
        pdf.pages.append(blank_page)

        # Overwrite the original PDF with the modified version
        pdf.save(pdf_path)


class ALAddendumField(DAObject):
    """
    Represents a field with attributes determining its display in an addendum, typically for PDF templates.

    The field can manage items that are either strings or list-like structures. Handling of dictionary overflow
    is not currently supported.

    Attributes:
        field_name (str): The name of a docassemble variable that this object represents.
        overflow_trigger (Union[int, bool]): Specifies the limit after which the text is truncated and moved
            to an addendum. If set to `True`, it will always overflow. If set to `False`, it will never overflow.
            An integer value represents the maximum character count before overflow.

        headers (Optional[Dict[str, str]]): Mapping of attributes to their display labels for a table representation.
            Planned for future implementation.
        field_style (Optional[str]): Style of the field, can be one of ["list", "table", "string"].
            Defaults to "string". Planned for future implementation.

    Note:
        The attributes `headers` and `field_style` are planned for future releases and are not currently implemented.
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)

    def overflow_value(
        self,
        preserve_newlines: bool = False,
        input_width: int = 80,
        overflow_message: str = "",
        preserve_words: bool = True,
    ) -> Any:
        """
        Retrieve the overflow portion of a variable that exceeds the content of `safe_value()`.

        This function addresses both list-like objects and strings, ensuring that the returned overflow
        content adheres to whitespace preferences specified by the parameters.

        Args:
            preserve_newlines (bool, optional): Determines the treatment of newline characters.
                If True, the returned string can contain single newline characters. Sequences of newline
                characters, including Windows-style "rn", will be reduced to a single "n". Double spaces
                will be replaced with a single space. If False, all whitespace, including newlines and
                tabs, will be replaced with a single space. Defaults to False.

            input_width (int, optional): The width of the input field or display area, used for determining
                overflow. Defaults to 80.

            overflow_message (str, optional): Message indicating overflow in the safe value. Defaults to "".

            preserve_words (bool, optional): If True, ensures words are not split between the main content
                and the overflow. Defaults to True.

        Returns:
            Any: The portion of the variable exceeding the content safe for display, considered as overflow.
        """
        # Handle a Boolean overflow first
        if isinstance(self.overflow_trigger, bool):
            if self.overflow_trigger:
                return self.value()
            return ""

        # If trigger is not a boolean value, overflow value is the value that starts at the end of the safe value.
        original_value = self.value_if_defined()
        safe_text = self.safe_value(
            overflow_message=overflow_message,
            input_width=input_width,
            preserve_newlines=preserve_newlines,
            _original_value=original_value,
            preserve_words=preserve_words,
        )
        if isinstance(safe_text, str):
            max_lines = self.max_lines(input_width=input_width)

            if preserve_newlines and max_lines > 1:
                # we do our own substitution of whitespace, only double newlines and spaces
                value_to_process = (
                    re.sub(r"[\r\n]+|\r+|\n+", r"\n", original_value).replace("  ", " ")
                ).rstrip()
            else:
                # textwrap.wrap(replace_whitespace=True) replaces all whitespace, not just double newlines and spaces
                value_to_process = re.sub(r"\s+", " ", original_value).strip()

            if safe_text == value_to_process:  # no overflow
                return ""
            # If this is a string, the safe value will include an overflow message. Delete
            # the overflow message from the length of the safe value to get the starting character.
            # Note: if preserve newlines is False:
            #   1. All single and double newlines are replaced with a space
            #   2. Character count will adjust to reflect double-newlines being replaced with one char.
            # If preserve newlines is True:
            #   1. We replace all double newlines with \n.
            #   2. Character count will adjust to reflect double-newlines being replaced with one char.
            overflow_start = max(len(safe_text) - len(overflow_message), 0)
            return value_to_process[overflow_start:].lstrip()

        # Do not subtract length of overflow message if this is a list of objects instead of a string
        elif isinstance(safe_text, (list, DAList)):
            return original_value[self.overflow_trigger :]
        raise ValueError(
            f"Attempted ALAddendum overflow for {self.field_name } which is of type {type(safe_text)}. Overflow is for lists and strings only."
        )

    def max_lines(self, input_width: int = 80) -> int:
        """
        Compute the maximum number of lines that can fit in the input given the specified input width.

        Parameters:
            input_width (int, optional): The width of the input or display area. Defaults to 80.

        Returns:
            int: The maximum number of lines accommodated by the input width.
        """
        return floor(self.overflow_trigger / input_width)

    def value(self) -> Any:
        """
        Retrieve the complete value without considering overflow constraints.

        This can be especially helpful in appendices where there's a desire to showcase the entire value
        without the necessity of toggling between various sections or pages.

        Returns:
            Any: The whole value of the field, irrespective of overflow.
        """
        return self.value_if_defined()

    def has_overflow(
        self,
        overflow_message: str = "",
        input_width: int = 80,
        preserve_newlines: bool = False,
        _original_value: Optional[str] = None,
        preserve_words: bool = True,
    ) -> bool:
        """
        Return True only if the value's length exceeds the overflow trigger.

        Args:
            overflow_message (str): A short message to go on the page where text is cutoff.
            input_width (int): The width, in characters, of the input box. Defaults to 80.
            preserve_newlines (bool): Determines whether newlines are preserved in the "safe" text.
                Defaults to False, which means all newlines are removed. This allows more text to appear
                before being sent to the addendum.
            _original_value (Any): for speed reasons, you can provide the full text and just use this
                method to determine if the overflow trigger is exceeded. If no _original_value is
                provided, this method will determine it using the value_if_defined() method.
            preserve_words (bool): If True, the algorithm will try to preserve whole words when
                truncating the text. If False, the algorithm will truncate the text at the overflow
                trigger, regardless of whether it is in the middle of a word.

        Returns:
            bool: True if the value's length exceeds the overflow trigger, False otherwise.
        """
        if _original_value:
            val = _original_value
        else:
            val = self.value_if_defined()

        return (
            self.safe_value(
                overflow_message=overflow_message,
                input_width=input_width,
                preserve_newlines=preserve_newlines,
                _original_value=_original_value,
                preserve_words=preserve_words,
            )
            != val
        )

    def original_or_overflow_message(
        self,
        overflow_message: str = "",
        input_width: int = 80,
        preserve_newlines: bool = False,
        _original_value: Optional[str] = None,
        preserve_words: bool = True,
    ) -> Union[str, List[Any]]:
        """
        Return the original value if it is less than the overflow trigger (once processed), otherwise return the overflow message.

        Unlike safe_value(), this will never output a partial value.

        Args:
            overflow_message (str): A short message to go on the page where text is cutoff.
            input_width (int): The width, in characters, of the input box. Defaults to 80.
            preserve_newlines (bool): Determines whether newlines are preserved in the "safe" text.
                Defaults to False, which means all newlines are removed. This allows more text to appear
                before being sent to the addendum.
            _original_value (Any): for speed reasons, you can provide the full text and just use this
                method to determine if the overflow trigger is exceeded. If no _original_value is
                provided, this method will determine it using the value_if_defined() method.
            preserve_words (bool): If True, the algorithm will try to preserve whole words when
                truncating the text. If False, the algorithm will truncate the text at the overflow
                trigger, regardless of whether it is in the middle of a word.

        Returns:
            Union[str, List[Any]]: Either a string representing the overflow message or the original value
        """
        if _original_value:
            val = _original_value
        else:
            val = self.value_if_defined()

        if not self.has_overflow(
            overflow_message=overflow_message,
            input_width=input_width,
            preserve_newlines=preserve_newlines,
            _original_value=val,
            preserve_words=preserve_words,
        ):
            return val

        return overflow_message

    def safe_value(
        self,
        overflow_message: str = "",
        input_width: int = 80,
        preserve_newlines: bool = False,
        _original_value: Optional[str] = None,
        preserve_words: bool = True,
    ) -> Union[str, List[Any]]:
        """
        Return just the portion of the variable that heuristics suggest will fit in the specified overflow_trigger
        limit. If the value is not defined, return an empty string.

        When `preserve_newlines` is `True`, the output will be limited to a number of lines, not a number
        of characters. The max number of lines will be calculated as `floor(self.overflow_trigger/input_width)`.
        Therefore, it is important that `input_width` is a divisor of `overflow_trigger`.

        Whitespace will be altered. If `preserve_newlines` is true, the return value may have newlines,
        but double newlines and Windows style (rn) will be replaced with n. Double spaces will be replaced
        with a single space.

        If `preserve_newlines` is false, all whitespace, including newlines and tabs, will be replaced
        with a single space.

        Args:
            overflow_message (str): A short message to go on the page where text is cutoff.
            input_width (int): The width, in characters, of the input box. Defaults to 80.
            preserve_newlines (bool): Determines whether newlines are preserved in the "safe" text.
                Defaults to False, which means all newlines are removed. This allows more text to appear
                before being sent to the addendum.
            _original_value (Optional[str]): For speed reasons, you can provide the full text and just use this
                method to determine if the overflow trigger is exceeded. If no `_original_value` is
                provided, this method will determine it using the `value_if_defined()` method.
            preserve_words (bool): Indicates whether words should be preserved in their entirety without being split.

        Returns:
            Union[str, List[Any]]: The portion of the variable that fits within the overflow trigger.
        """
        # Handle simplest case first
        if _original_value:
            value = _original_value
        else:
            value = self.value_if_defined()
        if (
            isinstance(value, str)
            and len(value) <= self.overflow_trigger
            and (value.count("\r") + value.count("\n")) == 0
        ):
            return value

        max_lines = self.max_lines(input_width=input_width)
        max_chars = max(
            self.overflow_trigger - len(overflow_message), 1
        )  # width needs to be at least 1 char

        # Strip newlines from strings because they take extra space
        if isinstance(value, str):
            # If we preserve newlines, we need to account for max_lines, not just max_chars
            if preserve_newlines and max_lines > 1:
                # Replace all new line characters with just \n. \r\n inserts two lines in a PDF
                value = re.sub(r"[\r\n]+|\r+|\n+", r"\n", value).rstrip()
                # textwrap.wrap does all the hard work for us here
                return (
                    " ".join(
                        wrap(
                            value,
                            width=input_width,
                            max_lines=max_lines,
                            replace_whitespace=False,
                            placeholder=overflow_message,
                        )
                    )
                    .replace("  ", " ")
                    .rstrip()
                )

            value = re.sub(r"\s+", " ", value)
            if len(value) > self.overflow_trigger:
                if preserve_words:
                    retval = wrap(
                        value,
                        width=max_chars,
                        replace_whitespace=True,
                        drop_whitespace=True,
                    )
                    return next(iter(retval)).rstrip() + overflow_message
                return value.rstrip()[:max_chars] + overflow_message
            else:
                return value.rstrip()

        # If the overflow item is a list or DAList
        if isinstance(value, (list, DAList)):
            return value[: self.overflow_trigger]
        else:
            # We can't slice objects that are not lists or strings
            # TODO: is it correct to return the whole object here?
            return value

    def value_if_defined(self) -> Any:
        """
        Fetch the value of the designated field if it exists; otherwise, return an empty string.

        This method ensures that the addendum does not inadvertently trigger docassemble's variable gathering.

        Returns:
            Any: The value of the field if it exists, otherwise an empty string.
        """
        return showifdef(self.field_name, "")

    def __str__(self):
        """
        Represent the ALAddendumField instance as a string.

        Returns:
            str: The string representation of the value contained within the field.
        """
        return str(self.value_if_defined())

    def columns(
        self, skip_empty_attributes: bool = True, skip_attributes: Optional[set] = None
    ) -> Optional[list]:
        """
        Return a list of the attributes present within the object that would make sense to go
        in the table of an addendum.

        If the `headers` attribute exists, this will be prioritized. Otherwise, the method will infer columns
        from the first value in the list. Empty attributes and the `complete` attribute are typically ignored.

        Args:
            skip_empty_attributes (bool, optional): Determines whether empty attributes are included in the list.
                                                    Defaults to True.
            skip_attributes (Optional[set], optional): A set of attributes to ignore. Defaults to {"complete"}.

        Returns:
            Optional[list]: A list of columns or None if no meaningful columns can be determined.

        Note:
            The "location" attribute of an Address object is always skipped in the column list.
        """
        if not skip_attributes:
            skip_attributes = {"complete"}
        if hasattr(self, "headers"):
            return self.headers
        else:
            # Use the first row as an exemplar
            try:
                first_value = self.value_if_defined()[0]

                if isinstance(first_value, dict) or isinstance(first_value, DADict):
                    return list([{key: key} for key in first_value.keys()])
                elif isinstance(first_value, DAObject):
                    attr_to_ignore = {
                        "has_nonrandom_instance_name",
                        "instanceName",
                        "attrList",
                    }
                    if skip_empty_attributes:
                        return [
                            {key: key}
                            for key in list(
                                set(first_value.__dict__.keys())
                                - set(skip_attributes)
                                - attr_to_ignore
                            )
                            if safeattr(first_value, key)
                        ]
                    else:
                        return [
                            {key: key}
                            for key in list(
                                set(first_value.__dict__.keys())
                                - set(skip_attributes)
                                - attr_to_ignore
                            )
                        ]
                else:
                    return None
            except:
                return None
            # None means the value has no meaningful columns we can extract

    def type(self) -> str:
        """
        Determine the data type of the contained value.

        Categories:
        - 'list': A simple list.
        - 'object_list': A list containing dictionaries or objects.
        - 'other': Any other type.

        Returns:
            str: The type category of the value.
        """
        value = self.value_if_defined()
        if isinstance(value, list) or isinstance(value, DAList):
            if len(value) and (
                isinstance(value[0], dict)
                or isinstance(value[0], DADict)
                or isinstance(value[0], DAObject)
            ):
                return "object_list"
            return "list"
        return "other"

    def is_list(self) -> bool:
        """
        Check if the field contains a list value, whether it consists of objects, dictionaries, or standard values.

        Returns:
            bool: True if the field contains a list, otherwise False.
        """
        return self.type() == "object_list" or self.type() == "list"

    def is_object_list(self) -> bool:
        """
        Determine if the field contains a list of dictionaries or objects.

        Returns:
            bool: True if the field contains a list of dictionaries or objects, otherwise False.
        """
        return self.type() == "object_list"

    def overflow_markdown(self) -> str:
        """
        Generate a markdown representation of the overflow values.

        The method returns either a markdown table or a bulleted list based on the structure of the values.
        This utility offers a standardized way to represent overflow content, though users might prefer
        to manually control the output's format.

        Returns:
            str: A markdown representation of the overflow values.
        """
        columns = self.columns()
        if not columns:
            if self.overflow_value():
                retval = "* "
                retval += "\n* ".join(self.overflow_value())
                return retval + "\n"
            else:
                return ""

        num_columns = len(columns)

        header = " | ".join([list(item.items())[0][1] for item in columns])
        header += "\n"
        header += "|".join(["-----"] * num_columns)

        flattened_columns = []
        for column in columns:
            flattened_columns.append(list(column.items())[0][0])

        rows = "\n"
        for row in self.overflow_value():
            if isinstance(row, dict) or isinstance(row, DADict):
                row_values = []
                for column in flattened_columns:
                    row_values.append(str(row.get(column, "")))
                rows += "|".join(row_values)
            else:
                row_values = []
                for column in flattened_columns:
                    # don't trigger collecting attributes that are required to resolve
                    # to a string
                    try:
                        row_values.append(str(getattr(row, column, "")))
                    except:
                        row_values.append("")
                rows += "|".join(row_values)
            rows += "\n"

        return header + rows

    def overflow_docx(
        self,
        path: str = "docassemble.ALDocumentDict:data/templates/addendum_table.docx",
    ) -> Any:
        """
        Insert a formatted table into a docx file, representing the overflow values.

        This method provides a convenient way to add overflow content into a docx file, although it
        doesn't offer formatting control. If more formatting flexibility is required, consider directly
        fetching the overflow values using the `overflow_value()` method.

        Parameters:
            path (str, optional): Path to the template docx file to be used.
                                  Defaults to a predetermined path.

        Returns:
            A docx template with the inserted table.
        """
        return include_docx_template(
            path, columns=self.columns(), rows=self.overflow_value()
        )


class ALAddendumFieldDict(DAOrderedDict):
    """
    A specialized dictionary for managing fields that may overflow in a document.

    This class assists in organizing and controlling fields that might exceed
    a specified character limit in a document. It provides utilities to determine
    if an overflow condition exists and to correctly display fields in various
    contexts, ensuring only the necessary text is shown.

    Adding a new entry will implicitly set the `field_name` attribute of the field

    Attributes:
        style (str): Determines the display behavior. If set to "overflow_only",
                     only the overflow text will be displayed.
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super(ALAddendumFieldDict, self).init(*pargs, **kwargs)
        self.object_type = ALAddendumField
        self.auto_gather = False
        if not hasattr(self, "style"):
            self.style = "overflow_only"
        if hasattr(self, "data"):
            self.from_list(self.data)
            del self.data

    def initializeObject(self, *pargs, **kwargs) -> Any:
        """
        Initializes a new dictionary entry and sets its `field_name` attribute.

        When an entry is implicitly created, this method ensures the item knows
        its own field name by setting the `field_name` attribute.

        Args:
            *pargs: List of arguments to use to create the dict entry. The 0th arg is
                also used to set the `field_name` attribute.
            **kwargs: List of keyword arguments used to create the dict entry

        Returns:
          The new dictionary entry created
        """
        the_key = pargs[0]
        newobj = super().initializeObject(*pargs, **kwargs)
        self[the_key].field_name = the_key
        return newobj

    def from_list(self, data: List[Dict]) -> None:
        """
        Populate the dictionary using a list of field data.

        Args:
            data (list): List of dictionaries containing ield data with keys "field_name"
                and "overflow_trigger".
        """
        for entry in data:
            new_field = self.initializeObject(entry["field_name"], ALAddendumField)
            new_field.field_name = entry["field_name"]
            new_field.overflow_trigger = entry["overflow_trigger"]
        return

    def defined_fields(self, style: str = "overflow_only") -> list:
        """
        Fetch a list of fields that are defined.

        Args:
            style (str, optional): If set to "overflow_only", only the fields with overflow values
                will be returned. Defaults to "overflow_only".

        Returns:
            list: List of defined fields based on the specified style.
        """
        if style == "overflow_only":
            return [field for field in self.values() if len(field.overflow_value())]
        else:
            return [field for field in self.values() if defined(field.field_name)]

    def overflow(self) -> list:
        """
        Retrieve fields that have overflowed their character limits.

        Returns:
            list: A list of fields with overflow values.
        """
        return self.defined_fields(style="overflow_only")

    def has_overflow(self) -> bool:
        """
        Determine if any field within the dictionary exceeds its overflow limit.

        Returns:
            bool: True if at least one field overflows, False otherwise.
        """
        for field in self.values():
            if field.overflow_value():
                return True
        return False


class DALazyAttribute(DAObject):
    """
    Extends the `DAObject` to support attributes that are re-evaluated with every page load.

    This is particularly helpful when there's a need to cache information on a per-page basis.
    The implementation leverages Docassemble's object pickling process by customizing the
    `__getstate__` method that Pickle uses for serialization.

    Attributes:
        instanceName (str): A unique identifier for the object instance, if available.
    """

    def __getstate__(self) -> dict:
        """
        Overrides the default method used by Pickle for object serialization.

        If the object has an `instanceName` attribute, it is retained during serialization.
        Otherwise, an empty dictionary is returned, ensuring that other attributes are not
        persisted across page loads.

        Returns:
            dict: A dictionary containing only the `instanceName` if it exists, or empty otherwise.
        """
        if hasattr(self, "instanceName"):
            return dict(instanceName=self.instanceName)
        else:
            return dict()


class ALDocument(DADict):
    """
    A dictionary of attachments, either created by a DAFile or an attachment
    block. Typically there are three:
    1. The final version of a document with a signature. E.g., my_doc['final'].
    2. The preview version of a document with no signature. E.g.,
       my_doc['preview'].
    3. An addendum of a document contained in the attribute `addendum`. E.g.
       `my_doc.addendum`.

    There is no limit to the number of keys, but the ALDocumentBundle class
    expects at least a "final" key to exist, and the `addendum` attribute is
    required if you desire to use PDF documents with text overflow. It is best
    practice to use exactly the two keys "final" and "preview" and the attribute
    "addendum". The "final" and "preview" documents will normally be the same
    template, but with logic controlling the display of a particular section, such
    as the signature.

    Each form that an interview generates should get its own ALDocument object.

    The "addendum" attribute can be handled in a generic object block. Multiple
    documents can use the same addendum template, with just the case caption
    varying.

    ALDocuments are designed to be used contingently as part of ALDocumentBundle
    objects. Each ALDocument is considered to be "enabled" or "disabled" for a
    particular interview user's session. This allows you to always work with a
    single object representing all of the possible documents an interview can
    generate, and use encapsulated logic to trigger individual documents inclusion
    on the final download screen.

    Attributes:
        filename (str): name used for output PDF
        title (str): display name for the output PDF
        enabled (bool): if this document should be created. See examples.
        addendum (DAFile | DAFileCollection): (optional) an attachment block
        overflow_fields (ALAddendumField): (optional) ALAddendumFieldDict
          instance. These values will be used to detect and handle overflow.
        has_addendum (bool): (optional) Defaults to False. Set to True if the
          document could have overflow, like for a PDF template.

    Note:
        The `enabled` attribute should always be defined by a code block or the
        objects block, because by default it is considered fresh on each page
        load. If your interview logic requires that you directly ask the user
        whether or not to include a document, you can use a single intermediate
        variable that is posed to the interview user to work around this
        limitation.

    Examples: # TODO: the code blocks aren't working right yet on the Docusaurus page.

        Simple use where the document is always enabled and will have no addendum
        --------------------------------------------------------------------------
        ```yaml
        ---
        objects:
          - my_doc: ALDocument.using(filename="myDoc.pdf", title="myDoc", enabled=True)
        ---
        attachment:
          variable name: my_doc[i]  # This same template will be used for the `preview` and `final` keys
          content: |
            Here is some content

            % if i == 'final':
            ${ users[0].signature }
            % elif i == 'preview':
            [ Your signature here ]
            % endif
        ```

        Enable a document conditionally
        --------------------------------
        ```yaml
        ---
        # See that `enabled` is not defined here
        objects:
          - affidavit_of_indigency: ALDocument.using(filename="affidavit-of-indigency.pdf", title="Affidavit of Indigency")
        ---
        code: |
          affidavit_of_indigency.enabled = ask_indigency_questions and is_indigent
        ```

        An example enabling with a question posed to the interview user
        ----------------------------------------------------------------
        You should always use a code block or an object block to set the "enabled" status;
        Use an intermediate variable if you want to ask the user directly whether or not to include a document.
        ```yaml
        ---
        question: |
          Do you want the extra document included?
        fields:
          - no label: include_extra_document
            datatype: yesnoradio
        ---
        code: |
          extra_document.enabled = include_extra_document
        ---
        attachment:
            variable name: extra_document[i] # This same template will be used for `final` and `preview`
            docx template file: extra_document.docx
        ```

        For a document that may need an addendum, you must specify this when the object is created
        or in a mandatory code block. The addendum will only be triggered if the document has "overflow"
        in one of the fields that you specify.
        ```
        ---
        objects:
          - my_doc: ALDocument.using(filename="myDoc.pdf", title="myDoc", enabled=True, has_addendum=True)
        ---
        attachment:
            variable name: my_doc[i]
            ...
        ---
        generic object: ALDocument
        attachment:
          variable name: x.addendum
          docx template file: docx_addendum.docx
        ---
        code: |
          my_doc.overflow_fields['big_text_variable'].overflow_trigger = 640 # Characters
          my_doc.overflow_fields['big_text_variable'].label = "Big text label" # Optional - you may use in your addendum
          my_doc.overflow_fields['list_of_objects_variable'].overflow_trigger = 4 # Items in the list
          my_doc.overflow_fields.gathered = True
        ```
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super(ALDocument, self).init(*pargs, **kwargs)
        self.initializeAttribute("overflow_fields", ALAddendumFieldDict)
        if not hasattr(self, "default_overflow_message"):
            self.default_overflow_message = "..."
        if not hasattr(self, "has_addendum"):
            self.has_addendum = False
        self.initializeAttribute("cache", DALazyAttribute)
        self.always_enabled = hasattr(self, "enabled") and self.enabled
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"

    def as_pdf(
        self,
        key: str = "final",
        refresh: bool = True,
        pdfa: bool = False,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Generates a PDF version of the assembled document.

        Args:
            key (str): Document version key. Defaults to "final".
            refresh (bool): If True, generates the attachment anew each time. Defaults to True.
            pdfa (bool): If True, generates a PDF/A compliant document. Defaults to False.
            append_matching_suffix (bool): If True, appends the key as a suffix to the filename when it matches the suffix to append. Defaults to True.

        Returns:
            DAFile: Assembled document in PDF format, possibly combined with addendum.
        """
        # Trigger some stuff up front to avoid idempotency problems
        self.title
        self.need_addendum()

        safe_key = space_to_underscore(key)

        if not hasattr(self, "suffix_to_append"):
            self.suffix_to_append = "preview"
        if append_matching_suffix and key == self.suffix_to_append:
            append_suffix: str = f"_{safe_key}"
        else:
            append_suffix = ""
        filename = f"{base_name(self.filename)}{append_suffix}.pdf"

        # The PDF/A version of the document is a different file than the normal PDF,
        # so differentiate that when checking the cache
        if pdfa:
            safe_key = safe_key + "-pdfa"

        if hasattr(self.cache, safe_key):
            return getattr(self.cache, safe_key)

        if refresh:
            main_doc = self.getitem_fresh(key)
        else:
            main_doc = self[key]

        if isinstance(main_doc, DAFileCollection):
            main_doc = main_doc.pdf
            main_doc.title = self.title
            main_doc.filename = filename
            try:
                main_doc.set_attributes(filename=filename)
                main_doc.set_mimetype("application/pdf")
            except:
                pass

        if self.need_addendum():
            if refresh:
                addendum_doc = self.getattr_fresh("addendum")
            else:
                addendum_doc = self.addendum
            if isinstance(main_doc, DAFileCollection):
                addendum_doc = addendum_doc.pdf
            concatenated = pdf_concatenate(
                main_doc, addendum_doc, filename=filename, pdfa=pdfa
            )
            concatenated.title = self.title
            setattr(self.cache, safe_key, concatenated)
            return concatenated
        else:
            if pdfa:
                pdf_to_pdfa(main_doc.path())
            setattr(self.cache, safe_key, main_doc)
            return main_doc

    def as_docx(
        self,
        key: str = "final",
        refresh: bool = True,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Generates a DOCX version of the assembled document, if possible. Falls back to PDF if not.

        Args:
            key (str): Document version key. Defaults to "final".
            refresh (bool): If True, generates the attachment anew each time. Defaults to True.
            append_matching_suffix (bool): If True, appends the key as a suffix to the filename when it matches the suffix to append. Defaults to True.

        Returns:
            DAFile: Assembled document in DOCX or PDF format.
        """
        if append_matching_suffix and key == self.suffix_to_append:
            filename = f"{base_name(self.filename)}_{key}"
        else:
            filename = f"{base_name(self.filename)}"
        if self.need_addendum():
            try:
                the_file = docx_concatenate(
                    self.as_list(key=key, refresh=refresh),
                    filename=filename + ".docx",
                )
                the_file.title = self.title
                return the_file
            except:
                return self.as_pdf(key=key)

        if self._is_docx(key=key):
            the_file = self[key].docx
            the_file.title = self.title
            the_file.set_attributes(filename=filename + ".docx")
            return the_file

        return self.as_pdf(key=key, append_matching_suffix=append_matching_suffix)

    def _is_docx(self, key: str = "final") -> bool:
        """
        Checks if the document file format is DOCX.

        Args:
            key (str): Document version key. Defaults to "final".

        Returns:
            bool: True if the document format is DOCX, False otherwise.
        """
        if isinstance(self[key], DAFileCollection) and hasattr(self[key], "docx"):
            return True
        if isinstance(self[key], DAFile) and hasattr(self[key], "docx"):
            return True

        return False

    def as_list(self, key: str = "final", refresh: bool = True) -> List[DAFile]:
        """
        Generates a list containing the main document and its addendum, if applicable.

        Args:
            key (str): Document version key. Defaults to "final".
            refresh (bool): If True, generates the attachments anew each time. Defaults to True.

        Returns:
            List[DAFile]: List containing the main document and possibly its addendum.
        """
        if refresh:
            if self.has_addendum and self.has_overflow():
                return [self.getitem_fresh(key), self.getattr_fresh("addendum")]
            else:
                return [self.getitem_fresh(key)]
        else:
            if self.has_addendum and self.has_overflow():
                return [self[key], self.addendum]
            else:
                return [self[key]]

    def need_addendum(self) -> bool:
        """
        Determines if there's a need for an addendum in the document.
        First checks if the addendum is enabled, and then checks if there's overflow.

        Returns:
            bool: True if an addendum is needed, False otherwise.
        """
        return (
            hasattr(self, "has_addendum") and self.has_addendum and self.has_overflow()
        )

    def has_overflow(self) -> bool:
        """
        Checks if the document has fields that exceed their character limits.

        Returns:
            bool: True if there are overflow fields, False otherwise.
        """
        return self.overflow_fields.has_overflow()

    def overflow(self) -> list:
        """
        Retrieves a list of fields that have overflowed their character limits.

        Returns:
            list: List of overflow fields.
        """
        return self.overflow_fields.overflow()

    def original_or_overflow_message(
        self,
        field_name: str,
        overflow_message: str = "",
        input_width: int = 80,
        preserve_newlines: bool = False,
        _original_value: Optional[str] = None,
        preserve_words: bool = True,
    ) -> Union[str, List[Any]]:
        """
        Helper syntax to access a member field.

        Return the original value if it is less than the overflow trigger (once processed), otherwise return the overflow message.

        Unlike safe_value(), this will never output a partial value.

        Args:
            field_name (str): The name of the field to check.
            overflow_message (str): A short message to go on the page where text is cutoff.
            input_width (int): The width, in characters, of the input box. Defaults to 80.
            preserve_newlines (bool): Determines whether newlines are preserved in the "safe" text.
                Defaults to False, which means all newlines are removed. This allows more text to appear
                before being sent to the addendum.
            _original_value (Any): for speed reasons, you can provide the full text and just use this
                method to determine if the overflow trigger is exceeded. If no _original_value is
                provided, this method will determine it using the value_if_defined() method.
            preserve_words (bool): If True, the algorithm will try to preserve whole words when
                truncating the text. If False, the algorithm will truncate the text at the overflow
                trigger, regardless of whether it is in the middle of a word.

        Returns:
            Union[str, List[Any]]: Either the original value or the overflow message, never a truncated value.
        """
        if overflow_message is None:
            overflow_message = self.default_overflow_message

        return self.overflow_fields[field_name].original_or_overflow_message(
            overflow_message=overflow_message,
            input_width=input_width,
            preserve_newlines=preserve_newlines,
            _original_value=_original_value,
            preserve_words=preserve_words,
        )

    def safe_value(
        self,
        field_name: str,
        overflow_message: Optional[str] = None,
        preserve_newlines: bool = False,
        input_width: int = 80,
        preserve_words: bool = True,
    ) -> str:
        """
        Retrieve the "safe" value of a specified field, which is shorter than the overflow trigger.

        Args:
            field_name (str): The name of the field to retrieve the safe value from.
            overflow_message (Optional[str]): Message to display when the field value overflows. Defaults to the class's default overflow message.
            preserve_newlines (bool): Whether to maintain newlines in the output. Defaults to False.
            input_width (int): The expected input width, used for formatting. Defaults to 80.
            preserve_words (bool): Whether to avoid splitting words during formatting. Defaults to True.

        Returns:
            str: The "safe" value of the specified field.
        """
        if overflow_message is None:
            overflow_message = self.default_overflow_message
        return self.overflow_fields[field_name].safe_value(
            overflow_message=overflow_message,
            preserve_newlines=preserve_newlines,
            input_width=input_width,
            preserve_words=preserve_words,
        )

    def overflow_value(
        self,
        field_name: str,
        overflow_message: Optional[str] = None,
        preserve_newlines: bool = False,
        input_width: int = 80,
        preserve_words: bool = True,
    ) -> str:
        """
        Retrieve the "overflow" value of a specified field, which is the amount exceeding the overflow trigger.

        Args:
            field_name (str): The name of the field to retrieve the overflow value from.
            overflow_message (Optional[str]): Message to display when the field value overflows. Defaults to the object's default overflow message.
            preserve_newlines (bool): Whether to maintain newlines in the output. Defaults to False.
            input_width (int): The expected input width, used for formatting. Defaults to 80.
            preserve_words (bool): Whether to avoid splitting words during formatting. Defaults to True.

        Returns:
            str: The "overflow" value of the specified field.
        """
        if overflow_message is None:
            overflow_message = self.default_overflow_message
        return self.overflow_fields[field_name].overflow_value(
            overflow_message=overflow_message,
            preserve_newlines=preserve_newlines,
            input_width=input_width,
            preserve_words=preserve_words,
        )

    def is_enabled(self, refresh: bool = True) -> bool:
        """
        Determine if a document is considered "enabled" based on various conditions.

        A document is "enabled" if:
        1. The .always_enabled attribute is set to true (i.e., enabled at initialization).
        2. The .enabled attribute is set to true (calculated fresh once per page load).
        3. The cache.enabled attribute is set to true.

        Args:
            refresh (bool): If True, refreshes the enabled status of the document. Defaults to True.

        Returns:
            bool: True if the document is enabled, otherwise False.
        """
        if hasattr(self, "always_enabled") and self.always_enabled:
            return True
        if hasattr(self.cache, "enabled"):
            return self.cache.enabled
        if refresh:
            self.cache.enabled = self.enabled
            if hasattr(self, "enabled"):
                del self.enabled
            return self.cache.enabled
        else:
            return self.enabled


class ALStaticDocument(DAStaticFile):
    """
    A class for initializing static documents for inclusion in an ALDocumentBundle with a one-liner.

    Note:
        Static files should always be placed in the `/data/static` folder of a package. The `/data/templates` folder is private
        and the ALDocumentBundle requires publicly accessible files.

    Attributes:
        filename (str): Path to the file within `/data/static/`.
        title (str): Title displayed as a row when invoking `download_list_html()` method from ALDocumentBundle.

    Examples:
        Add a static PDF file to a document bundle.
        .. code-block:: yaml
          ---
          objects:
            - static_test: ALStaticDocument.using(title="Static Test", filename="static.pdf", enabled=True)
          ---
          objects:
            - bundle: ALDocumentBundle.using(elements=[static_test], filename="bundle", title="Documents to download now")

    Todo:
        Consider handling files in `/data/templates` if deemed useful, potentially by copying into a DAFile using `pdf_concatenate()`.
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        self.has_addendum = False
        self.auto_gather = False
        self.gathered = True
        self.initializeAttribute("cache", DALazyAttribute)
        self.always_enabled = hasattr(self, "enabled") and self.enabled
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"

    def __getitem__(self, key):
        """
        Override to ensure 'final' and 'private' keys always exist and reference the same file.

        Returns:
            ALStaticDocument: Returns self.
        """
        return self

    def as_list(self, key: str = "final", refresh: bool = True) -> List[DAStaticFile]:
        """
        Get the document as a list.

        Args:
            key (str): Key to access the document. Defaults to "final".
            refresh (bool): Whether to refresh the document. Defaults to True.

        Returns:
            List[DAStaticFile]: A list containing this document.
        """
        return [self]

    def as_pdf(
        self,
        key: str = "final",
        pdfa: bool = False,
        filename: str = "",
        append_matching_suffix: bool = True,
        refresh: bool = False,
    ) -> Union[DAStaticFile, DAFile]:
        """
        Convert the document into PDF format.

        Args:
            key (str): Key to access the document. Defaults to "final".
            pdfa (bool): Whether to return the document in PDF/A format. Defaults to False.
            filename (str): Name for the converted file. Defaults to the original filename.
            append_matching_suffix (bool): Whether to append a matching suffix to the filename. Defaults to True.
            refresh (bool): Whether to refresh the document. Defaults to False.

        Returns:
            Union[DAStaticFile, DAFile]: The document in PDF format.
        """
        if not filename:
            filename = self.filename
        return pdf_concatenate(self, pdfa=pdfa, filename=f"{base_name(filename)}.pdf")

    def as_docx(
        self,
        key: str = "final",
        refresh: bool = True,
        append_matching_suffix: bool = False,
    ) -> Union[DAStaticFile, DAFile]:
        """
        Convert the document into DOCX format, if possible. If not, return as PDF.

        Args:
            key (str): Key to access the document. Defaults to "final".
            refresh (bool): Whether to refresh the document. Defaults to True.
            append_matching_suffix (bool): Not used for static documents. They remain unchanged.

        Returns:
            Union[DAStaticFile, DAFile]: The document in DOCX or PDF format.
        """
        if self._is_docx():
            return self
        else:
            # Don't apply the append_matching_suffix strategy to static files because it would
            # be difficult to make consistent between DOCX and PDF, and would have
            # negative performance implications. By definition static files have only one version
            return self.as_pdf(key=key, append_matching_suffix=False)

    def _is_docx(self, key: str = "final") -> bool:
        """
        Check if the document is in DOCX format.

        Args:
            key (str): Key to access the document. Defaults to "final".

        Returns:
            bool: True if the document is in DOCX format, otherwise False.
        """
        if hasattr(self, "extension") and self.extension.lower() == "docx":
            return True
        if (
            hasattr(self, "mimetype")
            and self.mimetype
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            return True
        return False

    def show(self, **kwargs) -> DAFile:
        """
        Display the document.

        This method provides a workaround for problems generating thumbnails.

        Args:
            **kwargs: Args to pass to DAFile's show function

        Returns:
            DAFile: Displayable version of the document.
        """
        # TODO: this explicit conversion shouldn't be needed
        # Workaround for problem generating thumbnails without it
        return pdf_concatenate(self).show(**kwargs)

    def is_enabled(self, **kwargs) -> bool:
        """Check if the document is enabled.

        Args:
            **kwargs: Unused (for signature compatibility only)

        Returns:
            bool: True if the document is enabled, otherwise False.
        """
        return self.enabled


class ALDocumentBundle(DAList):
    """
    A collection of ALDocuments or nested ALDocumentBundles, represented as a DAList.

    This class provides functionalities for grouping multiple documents or nested bundles
    in a specific order. For instance, you might want to bundle documents differently for the court,
    the user, and the opposing party. Each ALDocument within this bundle can be individually "enabled"
    or "disabled", which will determine its inclusion in the generated bundle.

    A bundle can be output as a single merged PDF or as a list of individual documents. For nested
    bundles, each can be rendered as a merged PDF or a list of documents.

    Attributes:
        filename (str): The name of the output file (without extension).
        title (str): The title of the bundle.
        enabled (bool, optional): Determines if the bundle is active. Defaults to True.
        auto_gather (bool, optional): Automatically gathers attributes. Defaults to False.
        gathered (bool, optional): Specifies if attributes have been gathered. Defaults to True.
        default_parity (Optional[Literal["even", "odd"]]): Default parity to enforce on the PDF. Defaults to None.

    Examples:
        Given three documents: `Cover page`, `Main motion form`, and `Notice of Interpreter Request`,
        bundle them as follows:
        ```
        bundle = ALDocumentBundle(elements=[cover_page, main_motion, notice_of_request],
                                  filename="documents_bundle", title="Document Set")
        ```

        Convert the bundle to a PDF:
        ```
        combined_pdf = bundle.as_pdf()
        ```

        Convert the bundle to a zip archive containing individual PDFs:
        ```
        zipped_files = bundle.as_zip()
        ```
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        if "auto_gather" not in kwargs:
            self.auto_gather = False
        if "gathered" not in kwargs:
            self.gathered = True
        self.initializeAttribute("cache", DALazyAttribute)
        self.always_enabled = hasattr(self, "enabled") and self.enabled
        # Pre-cache some DALazyTemplates we set up to aid translation that won't
        # vary at runtime
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"

    def as_pdf(
        self,
        key: str = "final",
        refresh: bool = True,
        pdfa: bool = False,
        append_matching_suffix: bool = True,
        ensure_parity: Optional[Literal["even", "odd"]] = None,
    ) -> Optional[DAFile]:
        """
        Returns a consolidated PDF of all enabled documents in the bundle.

        Args:
            key (str): Identifier for the document version, default is "final".
            refresh (bool): Flag to return a newly assembled version, default is True.
            pdfa (bool): If True, generates a PDF/A compliant document, defaults to False.
            append_matching_suffix (bool): Flag to determine if matching suffix should be appended to file name, default is True.
                                            Used primarily to enhance automated tests.
            ensure_parity (Optional[Literal["even", "odd"]]): Ensures the number of pages in the PDF is even or odd. If omitted,
                no parity is enforced. Defaults to None.

        Returns:
            Optional[DAFile]: Combined PDF file or None if no documents are enabled.
        """
        safe_key = space_to_underscore(key)
        if pdfa:
            safe_key = safe_key + "-pdfa"

        if hasattr(self.cache, safe_key):
            return getattr(self.cache, safe_key)

        # When running automated tests, the "preview" version of the file is
        # downloaded along with the final. Previously, the final version
        # ovewrote the preview version. This makes the tests more useful by
        # appending _preview to the name of the preview document.
        if not hasattr(self, "suffix_to_append"):  # for existing interviews
            self.suffix_to_append = "preview"
        if append_matching_suffix and key == self.suffix_to_append:
            append_suffix: str = f"_{key}"
        else:
            append_suffix = ""
        files = self.enabled_documents(refresh=refresh)
        if len(files) == 0:
            # In the case of no enabled files, avoid errors
            return None
        elif len(files) == 1:
            # This case is simplest--we do not need to process the document at this level
            pdf = files[0].as_pdf(
                key=key,
                refresh=refresh,
                pdfa=pdfa,
                append_matching_suffix=append_matching_suffix,
            )
            pdf.title = self.title
        else:
            pdf = pdf_concatenate(
                [document.as_pdf(key=key, refresh=refresh) for document in files],
                filename=f"{base_name(self.filename)}{append_suffix}.pdf",
                pdfa=pdfa,
            )
        pdf.title = self.title
        setattr(self.cache, safe_key, pdf)

        if hasattr(self, "default_parity") and not ensure_parity:
            ensure_parity = self.default_parity

        if ensure_parity not in [None, "even", "odd"]:
            raise ValueError("ensure_parity must be either 'even', 'odd' or None")

        if ensure_parity:  # Check for odd/even requirement
            if pdf_page_parity(pdf.path()) == ensure_parity:
                return pdf
            else:
                add_blank_page(pdf.path())

        return pdf

    def __str__(self) -> str:
        """
        Produces a string representation of the PDF in a compatible method
        with the DAFile class. In an interview, this will show a thumbnail of
        the PDF by default.

        Returns:
            str: String representation of the PDF.
        """
        # Could be triggered in many different places unintentionally: don't refresh
        return str(self.as_pdf(refresh=False))

    def as_zip(
        self,
        key: str = "final",
        refresh: bool = True,
        pdfa: bool = False,
        title: str = "",
        format="pdf",
        include_pdf=True,
    ) -> DAFile:
        """
        Returns a zip file containing all enabled documents in the bundle in the specified format.

        Args:
            key (str): Identifier for the document version, default is "final".
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.
            pdfa (bool): If True, all PDFs in the zip will be PDF/A compliant, defaults to False.
            title (str): Title of the zip file, shown next to the button to download the zip. Defaults to the bundle's title.
            format (str): Format of the documents in the zip file (e.g., "pdf", "docx", "original"), default is "pdf".
            include_pdf (bool): Flag to include a PDF version of the document if it's originally in docx format, default is True.

        Returns:
            DAFile: A zip file containing the enabled documents.
        """

        zip_key = f"{ space_to_underscore( key )}_zip"

        # Speed up performance if can (docs say `zip_file` works like `pdf_concatenate`)
        if hasattr(self.cache, zip_key):
            return getattr(self.cache, zip_key)

        # strip out a possible '.pdf' ending then add '.zip'
        zipname = os.path.splitext(self.filename)[0]
        if format == "docx":
            docs = []
            for doc in self.enabled_documents(refresh=refresh):
                docs.append(doc.as_docx(key=key, refresh=refresh))
                if include_pdf and doc._is_docx():
                    docs.append(doc.as_pdf(key=key, pdfa=pdfa, refresh=refresh))
        elif format == "original":
            # We don't try to convert to PDF if format=="original" (for things like XLSX files)
            docs = [doc[key] for doc in self.enabled_documents(refresh=refresh)]
        else:
            docs = [
                doc.as_pdf(
                    key=key,
                    refresh=refresh,
                    pdfa=pdfa,
                )
                for doc in self.enabled_documents(refresh=refresh)
            ]
        zip = zip_file(docs, filename=zipname + ".zip")
        if title == "":
            zip.title = self.title
        else:
            zip.title = title
        setattr(self.cache, zip_key, zip)

        return zip

    def preview(self, refresh: bool = True) -> Optional[DAFile]:
        """
        Returns a preview version of the bundle as a PDF.

        Args:
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.

        Returns:
            Optional[DAFile]: Preview PDF file or None if no documents are enabled.
        """
        return self.as_pdf(key="preview", refresh=refresh)

    def has_enabled_documents(self, refresh=False) -> bool:
        """
        Checks if there is at least one enabled document in the bundle.

        Args:
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is False.

        Returns:
            bool: True if there's at least one enabled document, otherwise False.
        """
        return any(document.is_enabled(refresh=refresh) for document in self.elements)

    def enabled_documents(self, refresh: bool = True) -> List[Any]:
        """
        Retrieves all enabled documents within the bundle.

        Args:
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.

        Returns:
            List[Any]: List of enabled documents.
        """
        return [
            document
            for document in self.elements
            if document.is_enabled(refresh=refresh)
        ]

    def as_flat_list(self, key: str = "final", refresh: bool = True) -> List[DAFile]:
        """
        Flattens and returns all enabled documents in the bundle, even from nested bundles.

        Args:
            key (str): Identifier for the document version, default is "final".
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.

        Returns:
            List[DAFile]: Flattened list of enabled documents.
        """
        # Iterate through the list of self.templates
        # Unpack the list of documents at each step so this can be concatenated into a single list
        flat_list = []
        for document in self.enabled_documents(refresh=refresh):
            if isinstance(document, ALDocumentBundle):
                # call the bundle's as_flat_list() method to show all enabled templates.
                flat_list.extend(document.as_flat_list(key=key, refresh=refresh))
            # This is a simple document node; check if this individual template is enabled.
            else:  # base case
                flat_list.extend(document.as_list(key=key, refresh=refresh))
        return flat_list

    def get_titles(self, key: str = "final", refresh: bool = True) -> List[str]:
        """
        Retrieves the titles of all enabled documents in the bundle.

        Args:
            key (str): Identifier for the document version, default is "final".
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.

        Returns:
            List[str]: Titles of the enabled documents.
        """
        flat_list = []
        for document in self.enabled_documents(refresh=refresh):
            if isinstance(document, ALDocumentBundle):
                flat_list.extend(document.get_titles(key=key, refresh=refresh))
            else:
                flat_list.append(document.title)
        return flat_list

    def as_pdf_list(
        self, key: str = "final", refresh: bool = True, pdfa: bool = False
    ) -> List[DAFile]:
        """
        Returns all enabled documents in the bundle as individual PDFs, even from nested bundles.

        Args:
            key (str): Identifier for the document version, default is "final".
            refresh (bool): Flag to reconsider the 'enabled' attribute and regenerate the enabled documents, default is True.
            pdfa (bool): Flag to return the documents in PDF/A format, default is False.

        Returns:
            List[DAFile]: List of enabled documents as individual PDFs.
        """
        return [
            doc.as_pdf(key=key, refresh=refresh, pdfa=pdfa)
            for doc in self.enabled_documents(refresh=refresh)
        ]

    def as_docx_list(self, key: str = "final", refresh: bool = True) -> List[DAFile]:
        """
        Generates a list of enabled documents from the bundle represented as DOCX files.

        If a particular document can't be represented as a DOCX, its original format or a PDF is returned.

        Args:
            key (str): Identifier for the document version, default is "final".
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.

        Returns:
            List[DAFile]: List of documents represented as DOCX files or in their original format.
        """
        return [
            doc.as_docx(key=key, refresh=refresh)
            for doc in self.enabled_documents(refresh=refresh)
        ]

    def as_editable_list(
        self, key: str = "final", refresh: bool = True
    ) -> List[DAFile]:
        """
        Generates a list of editable (DOCX or RTF) versions of the documents in the bundle.

        For documents that are not in DOCX or RTF formats, the original file format is returned.

        Args:
            key (str): Identifier for the document version, default is "final".
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.

        Returns:
            List[DAFile]: Flat list of documents in DOCX or RTF formats or their original format.
        """
        docs = self.as_flat_list(key=key, refresh=refresh)
        editable = []
        for doc in docs:
            if hasattr(doc, "docx"):
                editable.append(doc.docx)
            elif hasattr(doc, "rtf"):
                editable.append(doc.rtf)
            else:
                # The whole DAFile should still be appendable
                # for custom filetypes like PNG, etc.
                editable.append(doc)
        return editable

    def get_cacheable_documents(
        self,
        key: str = "final",
        pdf: bool = True,
        docx: bool = False,
        original: bool = False,
        refresh: bool = True,
        pdfa: bool = False,
        include_zip: bool = True,
        include_full_pdf: bool = False,
        append_matching_suffix: bool = True,
    ) -> Tuple[List[Dict[str, DAFile]], Optional[DAFile], Optional[DAFile]]:
        """
        Generates a cache of all enabled documents in the bundle, and returns it in a structure that can be cached
        and returned for use in a background process.

        The result looks like this:

        [
            {"title": "Document 1", "pdf": DAFile, "docx": DAFile, download_filename: str},
        ],
        DAFile, # Zip of whole bundle
        DAFile # PDF of whole bundle

        Args:
            key (str): Identifier for the document version, default is "final".
            pdf (bool): Flag to include a PDF version of each file, default is True.
            docx (bool): Flag to include a DOCX version of each file, default is False.
            original (bool): Flag to include the original version of each file, default is False.
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.
            pdfa (bool): Flag to return documents in PDF/A format, default is False.
            include_zip (bool): Flag to include a zip option, default is True.
            include_full_pdf (bool): Flag to include a PDF version of the whole bundle, default is False.
            append_matching_suffix (bool): Flag to determine if matching suffix should be appended to file name, default is True.

        Returns:
            Tuple[List[Dict[str, DAFile]], Optional[DAFile], Optional[DAFile]]: A list of dictionaries containing the enabled documents, a zip file of the whole bundle, and a PDF of the whole
        """
        # reduce idempotency delays
        enabled_docs = self.enabled_documents(refresh=refresh)
        for doc in enabled_docs:
            doc.title

        results = []

        for doc in enabled_docs:
            result = {"title": doc.title}
            filename_root = os.path.splitext(str(doc.filename))[0]
            if pdf:
                result["pdf"] = doc.as_pdf(
                    key=key,
                    refresh=refresh,
                    pdfa=pdfa,
                    append_matching_suffix=append_matching_suffix,
                )
                result["download_filename"] = filename_root + ".pdf"
            if docx and doc._is_docx(key=key):
                result["docx"] = doc.as_docx(
                    key=key,
                    refresh=refresh,
                    append_matching_suffix=append_matching_suffix,
                )
                result["download_filename"] = filename_root + ".docx"
            if original:
                result["original"] = doc[key]
                result["download_filename"] = doc.filename

            try:
                # If it's possible, set the file extension to the actual filetype
                # This is mostly necessary if people omit the file extension in attachment block
                # for filetype="original"
                if original:
                    download_doc = result["original"]
                else:
                    download_doc = result["docx"]
                ext = next(
                    iter(
                        mimetypes.guess_all_extensions(
                            download_doc.mimetype, strict=True
                        )
                    )
                )
                result["download_filename"] = filename_root + ext
            except:
                pass
            results.append(result)

        if len(enabled_docs) > 1 and include_zip:
            bundled_zip = self.as_zip(
                key=key, format="original" if original else "docx" if docx else "pdf"
            )
        else:
            bundled_zip = None

        if len(enabled_docs) > 1 and include_full_pdf:
            bundled_pdf = self.as_pdf(key=key, pdfa=pdfa)
        else:
            bundled_pdf = None

        return results, bundled_zip, bundled_pdf

    def download_list_html(
        self,
        key: str = "final",
        format: str = "pdf",
        view: bool = True,
        refresh: bool = True,
        pdfa: bool = False,
        include_zip: bool = True,
        view_label="View",
        view_icon: str = "eye",
        download_label: str = "Download",
        download_icon: str = "download",
        send_label: str = "Send",
        send_icon: str = "envelope",
        zip_label: Optional[str] = None,
        zip_icon: str = "file-archive",
        zip_row_label: Optional[str] = "",
        append_matching_suffix: bool = True,
        include_email: bool = False,
        use_previously_cached_files: bool = False,
        include_full_pdf: bool = False,
        full_pdf_label: Optional[str] = None,
    ) -> str:
        """
        Constructs an HTML table displaying a list of documents with 'view' and 'download' buttons.

        Args:
            key (str): Identifier for the document version, default is "final".
            format (str): Specifies the format of the files in the list. Can be "pdf", "docx", or "original". Default is "pdf".
            view (bool): Flag to include a 'view' button, default is True.
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.
            pdfa (bool): Flag to return documents in PDF/A format, default is False.
            include_zip (bool): Flag to include a zip option, default is True.
            view_label (str): Label for the 'view' button, default is "View".
            view_icon (str): Icon for the 'view' button, default is "eye".
            download_label (str): Label for the 'download' button, default is "Download".
            download_icon (str): Icon for the 'download' button, default is "download".
            send_label (str): Label for the 'send' button. Default is "Send".
            send_icon (str): Fontawesome icon for the 'send' button. Default is "envelope".
            zip_label (Optional[str]): Label for the zip option. If not provided, uses the generic template for `self.zip_label` ("Download all").
            zip_icon (str): Icon for the zip option, default is "file-archive".
            zip_row_label (str, optional): Text to go in the left-most column
                of the table's zip row. Will default to the value of `self.title`.
            append_matching_suffix (bool): Flag to determine if matching suffix should be appended to file name, default is True.
            include_email (bool): Flag to include an option, default is False.
            use_previously_cached_files (bool): Flag to use previously cached files (e.g., made in background) if defined. default is False.
            include_full_pdf (bool): Flag to include a full PDF option, default is False.
            full_pdf_label (Optional[str]): Label for the full PDF option. If not provided, uses the generic template for `self.full_pdf_label` ("Download all").

        Returns:
            str: HTML representation of a table with documents and their associated actions.
        """
        if not hasattr(self, "_cached_zip_label"):
            self._cached_zip_label = str(self.zip_label)

        if not hasattr(self, "_cached_full_pdf_label"):
            self._cached_full_pdf_label = str(self.full_pdf_label)

        if use_previously_cached_files and hasattr(self, "_downloadable_files"):
            downloadable_files, bundled_zip, bundled_pdf = self._downloadable_files
        else:
            downloadable_files, bundled_zip, bundled_pdf = self.get_cacheable_documents(
                key=key,
                pdf=(format == "pdf" or view == True),
                docx=format == "docx",
                original=format == "original",
                refresh=refresh,
                pdfa=pdfa,
                include_zip=include_zip,
                include_full_pdf=include_full_pdf,
                append_matching_suffix=append_matching_suffix,
            )

        html = f'<div class="container al_table al_doc_table" id="{ html_safe_str(self.instanceName) }">'

        for result in downloadable_files:
            title = result["title"]
            download_filename = result.get("download_filename", "document")

            if format == "original" and "original" in result:
                download_doc = result["original"]
            elif format == "docx" and "docx" in result:
                download_doc = result["docx"]
            elif "pdf" in result:
                download_doc = result["pdf"]
            else:
                continue  # Skip if the desired format is not available

            # Construct the download button
            doc_download_button = action_button_html(
                download_doc.url_for(
                    attachment=True, display_filename=download_filename
                ),
                label=download_label,
                icon=download_icon,
                color="primary",
                size="md",
                classname="al_download al_button",
            )

            # Construct the view button if needed
            if view and "pdf" in result and result["pdf"].url_for().endswith(".pdf"):
                # Use .pdf as the filename extension
                view_filename = os.path.splitext(download_filename)[0] + ".pdf"
                doc_view_button = action_button_html(
                    result["pdf"].url_for(
                        attachment=False, display_filename=view_filename
                    ),
                    label=view_label,
                    icon=view_icon,
                    color="secondary",
                    size="md",
                    classname="al_view al_button",
                )
                buttons = [doc_view_button, doc_download_button]
            else:
                buttons = [doc_download_button]

            html += table_row(title, buttons)

        # Add a zip file row if included
        if include_zip and bundled_zip:
            if not zip_label:
                zip_label = self._cached_zip_label
            filename_root = os.path.splitext(str(self.filename))[0]
            zip_button = action_button_html(
                bundled_zip.url_for(
                    attachment=False, display_filename=filename_root + ".zip"
                ),
                label=zip_label,
                icon=zip_icon,
                color="primary",
                size="md",
                classname="al_zip al_button",
            )
            safe_zip_row_label: str = (
                zip_row_label or (hasattr(self, "title") and self.title) or zip_label
            )
            html += table_row(safe_zip_row_label, zip_button)

        if include_full_pdf and bundled_pdf:
            if not full_pdf_label:
                full_pdf_label = self._cached_full_pdf_label
            filename_root = os.path.splitext(str(self.filename))[0]
            full_pdf_button = action_button_html(
                bundled_pdf.url_for(
                    attachment=False, display_filename=filename_root + ".pdf"
                ),
                label=full_pdf_label,
                icon="file-pdf",
                color="primary",
                size="md",
                classname="al_full_pdf al_button",
            )
            html += table_row(full_pdf_label, full_pdf_button)

        if include_email:
            html += self.send_email_table_row(
                key=key, send_label=send_label, send_icon=send_icon
            )

        html += "\n</div>"

        return html

    def download_html(
        self,
        key: str = "final",
        format: str = "pdf",
        pdfa: bool = False,
        view: bool = True,
        refresh: bool = True,
        view_label: str = "View",
        view_icon: str = "eye",
        download_label: str = "Download",
        download_icon: str = "download",
    ) -> str:
        """
        Returns an HTML string of a table to display all the docs
        combined into one pdf with 'view' and 'download' buttons.

        Deprecated; use download_list_html instead

        Args:
            key (str): Identifier for the document version, default is "final".
            format (str): Specifies the format of the files in the list. Can be "pdf", "docx", or "original". Default is "pdf".
            pdfa (bool): Flag to return the documents in PDF/A format, default is False.
            view (bool): Flag to include a 'view' button, default is True.
            refresh (bool): Flag to reconsider the 'enabled' attribute, default is True.
            view_label (str): Label for the 'view' button, default is "View".
            view_icon (str): Icon for the 'view' button, default is "eye".
            download_label (str): Label for the 'download' button, default is "Download".
            download_icon (str): Icon for the 'download' button, default is "download".

        Returns:
            str: HTML representation of a table with documents and their associated actions.
        """
        log(
            "ALDocumentBundle.download_html is deprecated; use download_list_html instead"
        )
        if format == "docx":
            the_file = self.as_docx(key=key)
        else:
            the_file = self.as_pdf(key=key, pdfa=pdfa)

        doc_download_button = action_button_html(
            the_file.url_for(attachment=True),
            label=download_label,
            icon=download_icon,
            color="primary",
            size="md",
            classname="al_download",
        )
        if view:
            pdf = self.as_pdf(key=key)
            if not pdf:
                buttons = [doc_download_button]
            else:
                doc_view_button = action_button_html(
                    pdf.url_for(attachment=False),
                    label=view_label,
                    icon=view_icon,
                    color="secondary",
                    size="md",
                    classname="al_view",
                )
                buttons = [doc_view_button, doc_download_button]
        else:
            buttons = [doc_download_button]

        html = (
            f'<div class="container al_table merged_docs" id="{html_safe_str(self.instanceName)}">'
            f"{table_row(self.title, buttons)}"
            f"\n</div>"
        )

        return html

    def send_email_table_row(
        self, key: str = "final", send_label: str = "Send", send_icon: str = "envelope"
    ) -> str:
        """
        Generate HTML doc table row for an input box and button that allows
        someone to send the bundle to the specified email address.

        Args:
            key (str): A key used to identify which version of the ALDocument to send. Defaults to "final".
            send_label (str): Label for the 'send' button. Default is "Send".
            send_icon (str): Icon for the 'send' button. Default is "envelope".

        Returns:
            str: The generated HTML string for the table row.
        """
        if not self.has_enabled_documents():
            return ""  # Don't let people email an empty set of documents
        if not hasattr(self, "_cached_get_email_copy"):
            self._cached_get_email_copy = str(self.get_email_copy)
        if not hasattr(self, "_cached_include_editable_documents"):
            self._cached_include_editable_documents = str(
                self.include_editable_documents
            )
        name = html_safe_str(self.instanceName)
        al_wants_editable_input_id = "_ignore_al_wants_editable_" + name
        al_email_input_id = "_ignore_al_doc_email_" + name
        al_send_button_id = "al_send_email_button_" + name

        javascript_string = (
            f"javascript:aldocument_send_action("
            f"'{self.attr_name('send_email_action_event')}',"
            f"'{al_wants_editable_input_id}','{al_email_input_id}')"
        )

        # Label "email" and input field for the 1st column of the table row
        input_html = f"""
        <span class="al_email_input_container {name} form-group da-field-container da-field-container-datatype-email">
          <label for="{al_email_input_id}" class="col-form-label da-form-label datext-right">Email</label>
          <input value="{user_info().email if user_logged_in() else ''}" alt="Email address for document" class="form-control al_doc_email_field al_button" type="email" size="35" name="{al_email_input_id}" id="{al_email_input_id}">
        </span>
        """

        # "Send" button for the 2nd column of the table row
        send_button = f'{action_button_html(javascript_string, label=send_label, icon=send_icon, color="primary", size="md", classname="al_send_email_button al_button", id_tag=al_send_button_id)}'

        # Whole row put together
        html = f"""
        <div class="row al_doc_table_row al_send_bundle {name}" id="al_send_bundle_{name}" name="al_send_bundle_{name}">
          <div class="col col-12 col-sm-9 al_email_input_col">{ input_html }</div>
          <div class="col col-12 col-sm-3 al_email_send_col al_buttons">{ send_button }</div>
        </div>
        """

        return html

    def send_button_to_html(
        self,
        email: str,
        editable: bool = False,
        template_name: str = "",
        label: str = "Send",
        icon: str = "envelope",
        color: str = "primary",
        key: str = "final",
    ) -> str:
        """
        Generate HTML for a button that allows someone to send the bundle to a
        specific email address. The email address is not editable by the end user
        in contrast to send_button_html.

        Args:
            email (str): The recipient's email address.
            editable (bool, optional): Flag indicating if the bundle is editable. Defaults to False.
            template_name (str, optional): The name of the template to be used. Defaults to an empty string.
            label (str, optional): The label for the button. Defaults to "Send".
            icon (str, optional): The Fontawesome icon for the button. Defaults to "envelope".
            color (str, optional): The Bootstrap color of the button. Defaults to "primary".
            key (str, optional): A key used to identify which version of the ALDocument to send. Defaults to "final".

        Returns:
            str: The generated HTML string for the button.
        """
        if not self.has_enabled_documents():
            return ""  # Don't let people email an empty set of documents
        if not hasattr(self, "_cached_get_email_copy"):
            self._cached_get_email_copy = str(self.get_email_copy)
        name = html_safe_str(self.instanceName)
        al_send_button_id = "al_send_email_to_button_" + name

        javascript_string = (
            f"javascript:aldocument_send_to_action("
            f"'{self.attr_name('send_email_to_action_event')}',"
            f"'{editable}',"
            f"'{email}',"
            f"'{al_send_button_id}',"
            f"'{template_name}',"
            f"'{key}')"
        )
        send_button = action_button_html(
            javascript_string,
            label=label,
            icon=icon,
            color=color,
            size="md",
            classname="al_send_email_button al_button",
            id_tag=al_send_button_id,
        )

        return send_button

    def send_button_html(
        self,
        key: str = "final",
        show_editable_checkbox: bool = True,
        template_name: str = "",
        label: str = "Send",
        icon: str = "envelope",
    ) -> str:
        """
        Generate HTML for an input box and button that allows someone to send the bundle
        to the specified email address.

        Optionally, display a checkbox that allows someone to decide whether or not to
        include an editable (Word) copy of the file, if and only if it is available.

        Args:
            key (str, optional): A key used to identify which version of the ALDocument to send. Defaults to "final".
            show_editable_checkbox (bool, optional): Flag indicating if the checkbox
                for deciding the inclusion of an editable (Word) copy should be displayed.
                Defaults to True.
            template_name (str, optional): Name of the template variable that is used to fill
                the email contents. By default, the `x.send_email_template` template will be used.
            label (str, optional): The label for the button. Defaults to "Send".
            icon (str, optional): The Fontawesome icon for the button. Defaults
                to "envelope".

        Returns:
            str: The generated HTML string for the input box and button.
        """
        if not self.has_enabled_documents():
            return ""  # Don't let people email an empty set of documents
        if not hasattr(self, "_cached_get_email_copy"):
            self._cached_get_email_copy = str(self.get_email_copy)
        if not hasattr(self, "_cached_include_editable_documents"):
            self._cached_include_editable_documents = str(
                self.include_editable_documents
            )
        name = html_safe_str(self.instanceName)
        al_wants_editable_input_id = "_ignore_al_wants_editable_" + name
        al_email_input_id = "_ignore_al_doc_email_" + name
        al_send_button_id = "al_send_email_button_" + name

        javascript_string = (
            f"javascript:aldocument_send_action("
            f"'{self.attr_name('send_email_action_event')}',"
            f"'{al_wants_editable_input_id}',"
            f"'{al_email_input_id}',"
            f"'{template_name}',"
            f"'{key}')"
        )

        # Container of whole email section with header
        return_str = f"""
  <fieldset class="al_send_bundle al_send_section_alone {name}" id="al_send_bundle_{name}" name="al_send_bundle_{name}">
    <legend class="h4 al_doc_email_header">{self._cached_get_email_copy}</legend> 
    """
        # "Editable" checkbox
        if show_editable_checkbox:
            return_str += f"""
    <div class="form-check-container">
      <div class="form-check">
        <input class="form-check-input" type="checkbox" class="al_wants_editable" id="{al_wants_editable_input_id}">
        <label class="al_wants_editable form-check-label" for="{al_wants_editable_input_id}">{self._cached_include_editable_documents}
        </label>
      </div>
    </div>
  """
        # Email input and send button
        return_str += f"""
  <div class="al_email_container">
  
    <span class="al_email_address {name} container form-group row da-field-container da-field-container-datatype-email">
      <label for="{al_email_input_id}" class="col-form-label da-form-label datext-right">Email</label>
      <input value="{user_info().email if user_logged_in() else ''}" alt="Email address for document" class="form-control" type="email" size="35" name="{al_email_input_id}" id="{al_email_input_id}">
    </span>
    
    {action_button_html(javascript_string, label=label, icon=icon, color="primary", size="md", classname="al_send_email_button", id_tag=al_send_button_id)}

  </div>
  """
        return_str += "</fieldset>"  # .al_send_section_alone container
        return return_str

    def send_email(
        self,
        to: Any = None,
        key: str = "final",
        editable: bool = False,
        template: Any = None,
        **kwargs,
    ) -> bool:
        """
        Send an email with the current bundle as a series of flat pdfs (one per bundle entry)
        or as editable documents. This function is similar to
        https://docassemble.org/docs/functions.html#send_email with additional parameters.

        Args:
            to (Any): The email address or list of addresses to send to. It can be a string
                or objects with such. Similar to da send_email `to`.
            key (str, optional): Specifies which version of the document to send. Defaults to "final".
            editable (bool, optional): If True, sends the editable documents. Defaults to False.
            template (Any): The template variable, similar to da `send_email` `template` variable.
            **kwargs: Additional parameters to pass to the da `send_email` function.

        Returns:
            bool: Indicates if the email was sent successfully.
        """
        if not template:
            template = self.send_email_template

        if editable:
            return send_email(
                to=to,
                template=template,
                # Add both DOCX and PDF versions, but if it's not possible to be a DOCX don't add the PDF
                # twice
                attachments=list(
                    dict.fromkeys(
                        self.as_editable_list(key=key) + self.as_pdf_list(key=key)
                    )
                ),
                **kwargs,
            )
        else:
            return send_email(
                to=to,
                template=template,
                attachments=self.as_pdf_list(key=key),
                **kwargs,
            )

    def _is_self_enabled(self, refresh=True) -> bool:
        """
        Check if the document is always enabled or if it's enabled in the cache.

        Args:
            refresh (bool): Whether to refresh the enabled status. Defaults to True.

        Returns:
            bool: Indicates if the document is enabled.
        """
        if hasattr(self, "always_enabled") and self.always_enabled:
            return True
        if hasattr(self.cache, "enabled"):
            return self.cache.enabled
        if refresh:
            self.cache.enabled = self.enabled
            if hasattr(self, "enabled"):
                del self.enabled
            return self.cache.enabled
        else:
            return self.enabled

    def is_enabled(self, refresh=True) -> bool:
        """
        Check if the bundle itself is enabled, and if it has at least one enabled child document.

        Args:
            refresh (bool): Whether to refresh the enabled status. Defaults to True.

        Returns:
            bool: Indicates if the bundle and its child documents are enabled.
        """
        self_enabled = self._is_self_enabled(refresh=refresh)
        return self_enabled and self.has_enabled_documents(refresh=refresh)

    def _is_docx(self, key: str = "final") -> bool:
        """
        Determine if all enabled documents are of type DOCX.

        Args:
            key (str, optional): The key to identify enabled documents. Defaults to "final".

        Returns:
            bool: True if all enabled documents are DOCX, otherwise False.
        """
        if all(f._is_docx() for f in self.enabled_documents()):
            return True
        return False

    def as_docx(
        self,
        key: str = "final",
        refresh: bool = True,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Convert the enabled documents to a single DOCX file or PDF file if conversion fails.

        Args:
            key (str, optional): The key to identify enabled documents. Defaults to "final".
            refresh (bool, optional): Refresh the enabled documents before conversion. Defaults to True.
            append_matching_suffix (bool, optional): Append a matching suffix to the output filename. Defaults to True.

        Returns:
            DAFile: A DAFile object containing the concatenated DOCX or PDF file.
        """
        if append_matching_suffix and key == self.suffix_to_append:
            filename = f"{base_name(self.filename)}_{key}"
        else:
            filename = f"{base_name(self.filename)}"
        if self._is_docx():
            try:
                the_file = docx_concatenate(
                    self.as_docx_list(key=key, refresh=refresh),
                    filename=filename + ".docx",
                )
                the_file.title = self.title
                return the_file
            except:
                return self.as_pdf(
                    key=key,
                    refresh=refresh,
                    append_matching_suffix=append_matching_suffix,
                )
        return self.as_pdf(
            key=key, refresh=refresh, append_matching_suffix=append_matching_suffix
        )

    def as_list(self, key: str = "final", refresh: bool = True) -> List[DAFile]:
        """
        Return a list of enabled documents.

        Args:
            key (str, optional): The key to identify enabled documents. Defaults to "final".
            refresh (bool, optional): Refresh the enabled documents before returning the list. Defaults to True.

        Returns:
            List[DAFile]: A list of enabled DAFile objects.
        """
        return self.as_flat_list(key=key, refresh=refresh)


class ALExhibit(DAObject):
    """
    Class to represent a single exhibit, with cover page, which may contain multiple documents representing pages.

    Attributes:
        pages (list): List of individual DAFiles representing uploaded images or documents.
        cover_page (DAFile | DAFileCollection): (optional) A DAFile or DAFileCollection object created by an `attachment:` block
          Will typically say something like "Exhibit 1"
        label (str): A label, like "A" or "1" for this exhibit in the cover page and table of contents
        starting_page (int): first page number to use in table of contents
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        self.initializeAttribute("_cache", DALazyAttribute)
        self.object_type = DAFileList
        if not hasattr(self, "starting_page"):
            self.start_page = 1
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"

    def _start_ocr(self):
        """
        Starts the OCR (optical character recognition) process on the uploaded documents.
        This adds a searchable text layer to any images of text that have been uploaded.

        Makes a background action for each page in the document.
        """
        if len(self.pages):
            self.ocr_version = DAFile(self.attr_name("ocr_version"))
            self.ocr_version.initialize(filename="tmp_ocrd.pdf")
            if get_config("assembly line", {}).get("ocr engine") == "ocrmypdf":
                self.ocr_status = background_action(
                    "al_exhibit_ocr_pages",
                    to_pdf=self.ocr_version,
                    from_file=self.pages,
                )
            else:
                self.ocr_status = self.ocr_version.make_ocr_pdf_in_background(
                    self.pages, psm=1
                )

    def ocr_ready(self) -> bool:
        """
        Returns True if the OCR process is complete. OCR is non-blocking, and assembly will work
        even if OCR is not complete. Check this status if you want to wait to deliver a document until
        OCR is complete.

        Will return true (but log a warning) if OCR was never started on the documents.
        That situation is likely a developer error, as you shouldn't wait for OCR if it never started

        Returns:
            bool: True iff OCR process has finished on all pages.
        """
        if hasattr(self, "ocr_status") and not self.ocr_status.ready():
            return False
        if not hasattr(self, "ocr_status"):
            log("developer warning: ocr_ready was called but _ocr_start wasn't!")
        return True

    def ocr_pages(self) -> List[DAFile]:
        """
        Retrieve the OCR-processed version of pages if available, else return the original pages.

        Returns:
            List[DAFile]: List of pages, either OCR-processed or original.
        """
        if (
            hasattr(self, "ocr_version")
            and hasattr(self, "ocr_status")
            and self.ocr_status.ready()
            and not self.ocr_status.failed()
            and self.ocr_status.get() is not None
            and self.ocr_version.ok
        ):
            return [self.ocr_version]
        pages = []
        for page in self.pages:
            pages.append(page)
        return pages

    def as_pdf(
        self,
        *,
        refresh: bool = False,
        prefix: str = "",
        pdfa: bool = False,
        add_page_numbers: bool = True,
        add_cover_page: bool = True,
        filename: Optional[str] = None,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Generates a PDF version of the exhibit, with optional features like Bates numbering or a cover page.

        Note that these are keyword only parameters, not positional.

        Args:
            refresh (bool): If True, forces the exhibit to refresh before generating the PDF. (unused, provided for signature compatibility)
            prefix (str): Prefix for Bates numbering if 'add_page_numbers' is True.
            pdfa (bool): If True, the generated PDF will be in PDF/A format.
            add_page_numbers (bool): If True, apply Bates numbering starting from 'self.start_page'.
            add_cover_page (bool): If True, prepend the exhibit with a cover page.
            filename (Optional[str]): Custom filename for the generated PDF. Default is "exhibits.pdf".
            append_matching_suffix (bool): If True, appends a suffix to the filename based on certain matching criteria.

        Returns:
            DAFile: PDF representation of the exhibit.
        """
        safe_key = "_file"
        if pdfa:
            safe_key = safe_key + "_pdfa"
        if add_page_numbers:
            safe_key = safe_key + "_page_nums"

        if hasattr(self._cache, safe_key):
            return getattr(self._cache, safe_key)
        if not filename:
            filename = "exhibits.pdf"
        if add_cover_page:
            concatenated_pages = pdf_concatenate(
                self.cover_page, self.ocr_pages(), filename=filename, pdfa=pdfa
            )
        else:
            concatenated_pages = pdf_concatenate(
                self.ocr_pages(), filename=filename, pdfa=pdfa
            )

        if add_page_numbers:
            concatenated_pages.bates_number(prefix=prefix, start=self.start_page)

        setattr(self._cache, safe_key, concatenated_pages)
        return getattr(self._cache, safe_key)

    def num_pages(self) -> int:
        """
        Calculate the total number of pages in the exhibit.

        Returns:
            int: Total page count.
        """
        return self.pages.num_pages()

    @property
    def complete(self) -> bool:
        """
        For purposes of list gathering, trigger the attributes in the order necessary
        to gather a complete exhibit object.

        Indicates if the exhibit is complete.

        NOTE: This property always returns True after triggering the required attributes.
        """
        self.title
        self.pages.gather()
        return True

    def __str__(self) -> str:
        """
        Return the title of the exhibit.

        Returns:
            str: Title of the exhibit.
        """
        return self.title


def ocrmypdf_task(
    from_file: Union[DAFile, DAFileList], to_pdf: DAFile
) -> Optional[str]:
    """
    Processes the provided files using the 'ocrmypdf' utility to apply Optical Character Recognition (OCR).

    If the source file is an image (e.g., png, jpg, jpeg, gif), this function sets the image DPI to 300.
    For non-image files, the text in the file is skipped during OCR.

    This function is designed to be executed as a background task (id: al_exhibit_ocr_pages_bg).

    Args:
        from_file (Union[DAFile, DAFileList]): The source file or list of files to be OCR-processed.
        to_pdf (DAFile): The destination file where the OCR-processed output will be saved.

    Returns:
        Optional[str]: The path of the OCR-processed file if successful; None otherwise.

    Raises:
        subprocess.TimeoutExpired: If the ocrmypdf process takes longer than an hour.
    """
    if not from_file or not to_pdf:
        log(
            "Developer error: in ocrmypdf_task, shouldn't pass None to from_file or to_pdf"
        )
        return None
    if isinstance(from_file, DAFileList):
        from_file = pdf_concatenate(from_file)
    if from_file.extension in ["png", "jpg", "jpeg", "gif"]:
        ocr_params = ["ocrmypdf", "--image-dpi", "300", from_file.path(), to_pdf.path()]
    else:
        ocr_params = ["ocrmypdf", "--skip-text", from_file.path(), to_pdf.path()]

    completed_ocr = None
    try:
        completed_ocr = subprocess.run(
            ocr_params, timeout=60 * 60, check=False, capture_output=True
        )
        to_pdf.commit()
        result = completed_ocr.returncode
    except subprocess.TimeoutExpired:
        result = 1
        log("ocr with ocrmypdf took too long (over an hour)")
    if result != 0:
        ocr_error_msg = f": {completed_ocr.stderr.decode()}" if completed_ocr else ""
        log("failed to ocr with ocrmypdf" + ocr_error_msg)
        return None
    else:
        return to_pdf.path()


class ALExhibitList(DAList):
    """
    A list representation of ALExhibit objects. Provides utility functions for managing exhibits
    and rendering them into a single PDF file.

    Attributes:
        maximum_size (int): The maximum allowed size in bytes of the entire document.
        auto_label (bool): If True, automatically numbers exhibits for cover page and table of contents. Defaults to True.
        auto_labeler (Callable): An optional function or lambda to transform the exhibit's index to a label.
                                 Uses A..Z labels by default.
        auto_ocr (bool): If True, automatically starts OCR processing for uploaded exhibits. Defaults to True.
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        if not hasattr(self, "auto_label"):
            self.auto_label = True
        if not hasattr(self, "auto_labeler"):
            self.auto_labeler = alpha
        if not hasattr(self, "auto_ocr"):
            self.auto_ocr = False
        if not hasattr(self, "include_table_of_contents"):
            self.include_table_of_contents = True
        if not hasattr(self, "include_exhibit_cover_pages"):
            self.include_exhibit_cover_pages = True
        if not hasattr(self, "bates_prefix"):
            self.bates_prefix = ""
        self.object_type = ALExhibit
        self.complete_attribute = "complete"
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"

    def as_pdf(
        self,
        filename="file.pdf",
        pdfa: bool = False,
        add_page_numbers: bool = False,
        toc_pages: int = 0,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Compiles all exhibits in the list into a single PDF.

        Args:
            filename (str): Desired filename for the generated PDF.
            pdfa (bool): If True, generates the PDF in PDF/A format.
            add_page_numbers (bool): If True, adds page numbers to the generated PDF.
            toc_pages (int): Expected number of pages in the table of contents.
            append_matching_suffix (bool): If True, appends matching suffix to the filename.

        Returns:
            DAFile: A single PDF containing all exhibits.
        """
        if self.include_exhibit_cover_pages:
            for exhibit in self:
                exhibit.cover_page
        if self.include_table_of_contents and toc_pages != 1:
            self._update_page_numbers(toc_guess_pages=toc_pages)
        return pdf_concatenate(
            [
                exhibit.as_pdf(
                    add_cover_page=self.include_exhibit_cover_pages,
                    add_page_numbers=add_page_numbers,
                    prefix=self.bates_prefix,
                )
                for exhibit in self
            ],
            filename=filename,
            pdfa=pdfa,
        )

    def size_in_bytes(self) -> int:
        """
        Calculates the total size in bytes of all exhibits in the list.

        Returns:
            int: Total size of all exhibits in bytes.
        """
        full_size = 0
        for exhibit in self.complete_elements():
            full_size += sum((a_page.size_in_bytes() for a_page in exhibit.pages))
        return full_size

    def _update_labels(self, auto_labeler: Optional[Callable] = None) -> None:
        """
        Updates labels of all exhibits in the list based on their index.

        Args:
            auto_labeler (Callable): An optional function or lambda to customize label generation.
                                     Uses the class's auto_labeler by default.
        """
        if auto_labeler is None:
            auto_labeler = self.auto_labeler

        for index, exhibit in enumerate(self.elements):
            exhibit.label = auto_labeler(index)

    def ocr_ready(self) -> bool:
        """
        Checks if all exhibits in the list have completed the OCR process.

        Returns:
            bool: True if all exhibits are OCRed or if OCR hasn't started. False otherwise.
        """
        ready = True
        for exhibit in self.elements:
            ready &= exhibit.ocr_ready()
        return ready

    def _update_page_numbers(
        self, starting_number: Optional[int] = None, toc_guess_pages: int = 1
    ) -> None:
        """
        Updates the starting page number of each exhibit in the list to reflect their position.

        Args:
            starting_number (Optional[int]): Optional starting number for the first exhibit.
            toc_guess_pages (int): Estimated number of pages for the table of contents.
        """
        toc_pages = toc_guess_pages if self.include_table_of_contents else 0
        cover_pages = 1 if self.include_exhibit_cover_pages else 0
        current_index = starting_number if starting_number else 1
        current_index += toc_pages
        for exhibit in self.elements:
            exhibit.start_page = current_index
            current_index = current_index + exhibit.num_pages() + cover_pages

    def _start_ocr(self) -> None:
        """
        Initiates the OCR process for each exhibit in the list.
        """
        for exhibit in self.elements:
            exhibit._start_ocr()

    def hook_after_gather(self) -> None:
        """
        Callback function executed after the entire list of exhibits is collected.
        Manages auto-labeling and initiates OCR if necessary.
        """
        if len(self):
            self._update_page_numbers()
            if self.auto_label:
                self._update_labels()
            if self.auto_ocr:
                self._start_ocr()


class ALExhibitDocument(ALDocument):
    """
    Represents a collection of uploaded documents, formatted like a record appendix
    or an exhibit list, complete with an optional table of contents and page numbering.

    Attributes:
        exhibits (ALExhibitList): A list of ALExhibit documents. Each item represents
                                  a distinct exhibit, which can span multiple pages.
        table_of_contents (DAFile or DAFileCollection): Generated by an `attachment:` block.
        _cache (DAFile): A cached version of the exhibit list. Caching is used due to
                         potential long processing times.
        include_table_of_contents (bool): Indicates if a table of contents should be generated.
        include_exhibit_cover_pages (bool): Determines if cover pages should accompany each exhibit.
        add_page_numbers (bool): If True, the as_pdf() method will add page numbers and labels.
        auto_labeler (Callable): A function or lambda for labeling exhibits.

    Todo:
        * Implement a method for a safe link in place of the attachment
          (considering potential filesize constraints on emails).

    Examples:
    ```
    ---
    objects:
      - exhibit_attachment: ALExhibitDocument.using(title="Exhibits", filename="exhibits" )
    ---
    code: |
      # This block is not needed, but you can provide and customize for your needs.
      # This mirrors the fallback block in ql_baseline.yml
      exhibit_attachment.enabled = exhibit_attachment.exhibits.has_exhibits
    ---
    objects:
      - al_user_bundle: ALDocumentBundle.using(elements=[my_instructions, my_main_attachment, exhibit_attachment], filename="user_bundle.pdf", title="All forms to download for your records")
    ```

    Example of using a custom label function, https://docassemble.org/docs/functions.html#item_label:
    ```
    ---
    objects:
      - exhibit_attachment: ALExhibitDocument.using(title="Exhibits", filename="exhibits" , auto_labeler=item_label)
    ```
    """

    include_exhibit_cover_pages: bool
    include_table_of_contents: bool
    add_page_numbers: bool
    has_addendum: bool
    auto_labeler: Callable
    auto_ocr: bool
    bates_prefix: str
    maximum_size: int
    suffix_to_append: str
    exhibits: ALExhibitList
    table_of_contents: DAFile

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        self.initializeAttribute("exhibits", ALExhibitList)
        if hasattr(self, "auto_labeler"):
            self.exhibits.auto_labeler = self.auto_labeler
        if hasattr(self, "auto_ocr"):
            self.exhibits.auto_ocr = self.auto_ocr
        if hasattr(self, "bates_prefix"):
            self.exhibits.bates_prefix = self.bates_prefix
        if hasattr(self, "include_exhibit_cover_pages"):
            self.exhibits.include_exhibit_cover_pages = self.include_exhibit_cover_pages
        else:
            self.include_exhibit_cover_pages = True
            self.exhibits.include_exhibit_cover_pages = True
        if hasattr(self, "maximum_size"):
            self.exhibits.maximum_size = self.maximum_size
        if hasattr(self, "include_table_of_contents"):
            self.exhibits.include_table_of_contents = self.include_table_of_contents
        else:
            self.include_table_of_contents = True
            self.exhibits.include_table_of_contents = True
        if not hasattr(self, "add_page_numbers"):
            self.add_page_numbers = False
        self.has_addendum = False
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"

    def has_overflow(self) -> bool:
        """
        Check if there is any overflow in the document.

        This is for compatibility with ALDocument; Exhibits inherently don't have overflow.

        Returns:
            bool: Always False for this implementation.
        """
        return False

    def ocr_ready(self) -> bool:
        """
        Determine if all exhibits within the document have undergone OCR processing.

        Returns:
            bool: True if all exhibits have been OCRed or if the OCR process hasn't been initiated.
        """
        return self.exhibits.ocr_ready()

    def __getitem__(self, key):
        """
        Overridden method to ensure 'final' and 'private' keys always reference the same file.

        Args:
            key: The key to fetch the item.

        Returns:
            ALExhibitDocument: Returns the current instance of the class.
        """
        return self

    def as_list(self, key: str = "final", refresh: bool = True) -> List[DAFile]:
        """
        Retrieve the document as a list.

        Args:
            key (str): Identifier key for the document. Default is "final".
            refresh (bool): If True, the document list will be refreshed. Default is True.

        Returns:
            List[DAFile]: A list containing the document.
        """
        return [self]

    def as_pdf(
        self,
        key: str = "final",
        refresh: bool = True,
        pdfa: bool = False,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Render the document as a PDF.

        Args:
            key (str): Identifier key for the document. Default is "final".
                       For compatibility with ALDocument.
            refresh (bool): If True, refreshes the PDF document. Default is True.
                            For compatibility with ALDocument.
            pdfa (bool): If True, the output PDF will be in PDF/A format. Default is False.
            append_matching_suffix (bool): If True, appends a matching suffix to the filename.

        Returns:
            DAFile: The document rendered as a PDF.
        """
        if not hasattr(self, "suffix_to_append"):
            self.suffix_to_append = "preview"
        if append_matching_suffix and key == self.suffix_to_append:
            filename = f"{base_name(self.filename)}_{key}.pdf"
        else:
            filename = base_name(self.filename) + ".pdf"

        if len(self.exhibits):
            if self.include_table_of_contents:
                toc_pages = self.table_of_contents.num_pages()
                return pdf_concatenate(
                    self.table_of_contents,
                    self.exhibits.as_pdf(
                        add_page_numbers=self.add_page_numbers, toc_pages=toc_pages
                    ),
                    filename=filename,
                    pdfa=pdfa,
                )
            else:
                return self.exhibits.as_pdf(
                    add_page_numbers=self.add_page_numbers,
                    filename=filename,
                    pdfa=pdfa,
                )

    def as_docx(
        self,
        key: str = "final",
        refresh: bool = True,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Despite the name, renders the document as a PDF. Provided for signature compatibility.

        Args:
            key (str, optional): Identifier key for the document. Default is "final".
            refresh (bool, optional): If True, refreshes the DOCX document. Default is True.
            append_matching_suffix (bool, optional): If True, appends a matching suffix to the filename (for automated tests).

        Returns:
            DAFile: The document rendered as a PDF.
        """
        return self.as_pdf()


class ALTableDocument(ALDocument):
    """
    Represents a document tailored for table-like data presentation.
    This class provides functionality to export data as a table in various formats such as PDF and DOCX.

    Attributes:
        has_addendum (bool): A flag indicating the presence of an addendum in the document.
        suffix_to_append (str): Suffix that can be appended to file names, defaulting to "preview".
        file (DAFile, optional): Reference to the generated file (can be PDF, DOCX, etc.).
        table (???): Represents the actual table data. Type and attributes need more context to document.
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        self.has_addendum = False
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"

    def has_overflow(self) -> bool:
        """
        Check for overflow in the document.

        For compatibility with ALDocument; Tables inherently don't have overflow.

        Returns:
            bool: Always False for this implementation.
        """
        return False

    def __getitem__(self, key):
        """
        Allows for index-based retrieval of a document.

        Overridden to ensure 'final' and 'private' keys always return the same document.

        Args:
            key: The key to fetch the item.

        Returns:
            DAFile: The document in its PDF format.
        """
        return self.as_pdf()

    def as_list(
        self, key: str = "final", refresh: bool = True, **kwargs
    ) -> List[DAFile]:
        """
        Retrieve the document as a list.

        Args:
            key (str): Identifier key for the document. Default is "final".
            refresh (bool): If True, the document list will be refreshed. Default is True.

        Returns:
            List[DAFile]: A list containing the document.
        """
        return [self[key]]

    def as_pdf(
        self,
        key: str = "final",
        refresh: bool = True,
        pdfa: bool = False,
        append_matching_suffix: bool = True,
        **kwargs,
    ) -> DAFile:
        """
        Despite the name, returns the document as an Excel Spreadsheet (XLSX file).
        Name retained for signature compatibility.

        Args:
            key (str): Identifier key for the document, mainly for compatibility with ALDocument.
            refresh (bool): For signature compatibility
            pdfa (bool): For signature compatibility
            append_matching_suffix (bool): For signature compatibility

        Returns:
            DAFile: The table rendered as an XLSX spreadsheet
        """
        if not hasattr(self, "suffix_to_append"):
            # When the key is "preview", append it to the file name
            self.suffix_to_append = "preview"
        if hasattr(self, "file"):
            return self.file
        self.file: DAFile = self.table.export(
            base_name(self.filename) + ".xlsx", title=self.filename
        )
        return self.file

    def as_docx(
        self,
        key: str = "bool",
        refresh: bool = True,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Despite the name, returns the document as an Excel Spreadsheet (XLSX file).
        Name retained for signature compatibility.

        Args:
            key (str): Identifier key for the document, mainly for compatibility with ALDocument.
            refresh (bool): For signature compatibility
            pdfa (bool): For signature compatibility
            append_matching_suffix (bool): For signature compatibility

        Returns:
            DAFile: The table rendered as an XLSX spreadsheet
        """
        return self.as_pdf()


class ALUntransformedDocument(ALDocument):
    """
    Represents an untransformed document. The class provides methods to access the document
    without making any modifications to it. The provided methods are mainly for duck-typing
    compatibility with ALDocument.

    Attributes:
        has_addendum (bool): A flag indicating the presence of an addendum in the document.
        suffix_to_append (str): Suffix that can be appended to file names, defaulting to "preview".
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        self.has_addendum = False
        if not hasattr(self, "suffix_to_append"):
            self.suffix_to_append = "preview"

    def has_overflow(self) -> bool:
        """
        Check for overflow in the document.

        For compatibility with ALDocument. Untransformed documents inherently don't have overflow.

        Returns:
            bool: Always False for this implementation.
        """
        return False

    def as_list(
        self, key: str = "final", refresh: bool = True, **kwargs
    ) -> List[DAFile]:
        """
        Retrieve the document as a list.

        Args:
            key (str): Identifier key for the document. Default is "final".
            refresh (bool): If True, the document list will be refreshed. Default is True.

        Returns:
            List[DAFile]: A list containing the document.
        """
        return [self[key]]

    def as_pdf(
        self,
        key: str = "final",
        refresh: bool = True,
        pdfa: bool = False,
        append_matching_suffix: bool = True,
        **kwargs,
    ) -> DAFile:
        """
        Fetch the document in its original form, without any transformations.

        This method is primarily for duck-typing compatibility with ALDocument.

        Args:
            key (str): Identifier key for the document. Unused, but included for compatibility.
            refresh (bool): If True, fetches the latest version of the document. Default is True.
            pdfa (bool): Unused argument for compatibility.
            append_matching_suffix (bool): Unused argument for compatibility.

        Returns:
            DAFile: The original, untransformed document.
        """
        return self[key]

    def as_docx(
        self,
        key: str = "final",
        refresh: bool = True,
        append_matching_suffix: bool = True,
    ) -> DAFile:
        """
        Fetch the document in its original form, without any transformations.

        This method is primarily for duck-typing compatibility with ALDocument.

        Args:
            key (str): Identifier key for the document. Default is "final".
            refresh (bool): If True, fetches the latest version of the document. Default is True.
            append_matching_suffix (bool): Unused argument for compatibility.

        Returns:
            DAFile: The original, untransformed document.
        """
        return self[key]


class ALDocumentUpload(ALUntransformedDocument):
    """
    Simplified class to handle uploaded documents, without any of the complexity of the
    ALExhibitDocument class.
    """

    def __getitem__(self, key):
        # This overrides the .get() method so that the 'final' and 'private' key always exist and
        # point to the same file.
        # There's no need to have final/preview versions of an uploaded document
        if isinstance(self.file, DAFileList):
            self.file = unpack_dafilelist(self.file)
        return self.file


def unpack_dafilelist(the_file: DAFileList) -> DAFile:
    """Creates a plain DAFile out of the first item in a DAFileList
    Args:
        the_file (DAFileList): an item representing an uploaded document in a Docassemble interview

    Returns:
        A DAFile representing the first item in the DAFileList, with a fixed instanceName attribute.
    """
    if isinstance(the_file, DAFileList):
        temp_name = the_file.instanceName
        inner_file = next(iter(the_file))
        inner_file.instanceName = temp_name  # reset instance name to the whole object instead of index in list we got rid of
        return inner_file
    else:
        return the_file

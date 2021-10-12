import re
import os
import mimetypes
from typing import Any, Dict, List, Union, Callable
from docassemble.base.util import log, word, DADict, DAList, DAObject, DAFile, DAFileCollection, DAFileList, defined, value, pdf_concatenate, zip_file, DAOrderedDict, action_button_html, include_docx_template, user_logged_in, user_info, send_email, docx_concatenate, get_config, space_to_underscore, DAStaticFile, alpha

__all__ = ['ALAddendumField',
           'ALAddendumFieldDict',
           'ALDocumentBundle', 
           'ALDocument', 
           'ALDocumentBundleDict',
           'ALStaticDocument',
           'safeattr',
           'label',
           'key',
           'ALExhibitList',
           'ALExhibit',
           'ALExhibitDocument',
           'ALTableDocument',
           'ALUntransformedDocument',
           'unpack_dafilelist']

DEBUG_MODE = get_config('debug')

def log_if_debug(text:str)->None:
  if DEBUG_MODE:
    log(text)

def label(dictionary):
  try:
    return list(dictionary.items())[0][1]
  except:
    return ''

def key(dictionary):
  try:
    return list(dictionary.items())[0][1]
  except:
    return ''

def safeattr(object, key):
  try:
    if isinstance(object, dict) or isinstance(object, DADict):
      return str(object.get(key,''))
    elif isinstance(object, DAObject):
      # `location` is not an attribute people usually want shown in the table of people's attributes
      if key == 'location':
        return ''
      return str(getattr(object, key))
    else:
      return ''
  except:
    return ''

def html_safe_str(the_string: str) -> str:
  """
  Return a string that can be used as an html class or id
  """
  return re.sub( r'[^A-Za-z0-9]+', '_', the_string )

#def table_row( title, view_file:DAFile, download_file:DAFile=None, view_icon:str="eye", download_icon:str="download") -> str:
def table_row( title:str, button_htmls:List[str] = []) -> str:
  """
  Uses the provided title and list of button html strings to
  return the row of an AL document-styled table in HTML format.
  """
  html = (
    f'\n\t<tr>'
    # '\n\t\t<td><i class="fas fa-file"></i>&nbsp;&nbsp;</td>'
    # TODO: Need to replace with proper CSS
    f'\n\t\t<td class="al_doc_title"><strong>{title}</strong></td>'
    f'\n\t\t<td class="al_buttons">'
  )
  for button in button_htmls:
    html += button
  html += '</td>'
  html += '\n\t</tr>'

  return html

class ALAddendumField(DAObject):
  """
  Object representing a single field and its attributes as related to whether
  it should be displayed in an addendum. Useful for PDF templates.

  The items can be strings or lists/list-like objects. It does not know
  how to handle overflow for a dictionary, e.g.

  Required attributes:
    - field_name (str): represents the name of a docassemble variable
    - overflow_trigger (int | bool): determines when text is cut off and sent to addendum

  Optional/planned (not implemented yet):
    - headers->dict(attribute: display label for table)
    - field_style->"list"|"table"|"string" (optional: defaults to "string")
  """

  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)

  def overflow_value(self, preserve_newlines:bool=False, input_width:int=80, overflow_message:str=""):
    """
    Try to return just the portion of the variable (list-like object or string)
    that is not contained in the safe_value().
    """
    # Handle a Boolean overflow first
    if isinstance(self.overflow_trigger, bool) and self.overflow_trigger:
      return self.value()

    # If trigger is not a boolean value, overflow value is the value that starts at the end of the safe value.
    original_value = self.value_if_defined()
    safe_text = self.safe_value(overflow_message = overflow_message, 
                                input_width=input_width, 
                                preserve_newlines=preserve_newlines, 
                                _original_value = original_value)
    if isinstance(safe_text,str):
      # Always get rid of double newlines, for consistency with safe_value.
      value_to_process = re.sub(r"[\r\n]+|\r+|\n+",r"\n",original_value).rstrip()
      if safe_text == value_to_process: # no overflow
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
      return value_to_process[overflow_start:]

    # Do not subtract length of overflow message if this is a list of objects instead of a string
    return original_value[self.overflow_trigger:]

  def max_lines(self, input_width:int=80, overflow_message_length=0) -> int:
    """
    Estimate the number of rows in the field in the output document.
    """
    return int(max(self.overflow_trigger-overflow_message_length,0) / input_width) + 1

  def value(self) -> Any:
    """
    Return the full value, disregarding overflow. Could be useful in addendum
    if you want to show the whole value without making user flip back/forth between multiple
    pages.
    """
    return self.value_if_defined()

  def safe_value(self, overflow_message:str="", input_width:int=80, preserve_newlines:bool=False, _original_value=None):
    """
    Try to return just the portion of the variable
    that is _shorter than_ the overflow trigger. Otherwise, return empty string.
    Args:
        overflow_message (str): A short message to go on the page where text is cutoff.
        input_width (int): The width, in characters, of the input box. Defaults to 80.
        preserve_newlines (bool): Determines whether newlines are preserved in the "safe" text.
            Defaults to False, which means all newlines are removed. This allows more text to appear
            before being sent to the addendum.
        _original_value (Any): for speed reasons, you can provide the full text and just use this
            method to determine if the overflow trigger is exceeded. If no _original_value is
            provided, this method will determine it using the value_if_defined() method.
    """

    # Handle simplest case first
    if _original_value:
      value = _original_value
    else:
      value = self.value_if_defined()
    if isinstance(value, str) and len(value) <= self.overflow_trigger and (value.count('\r') + value.count('\n')) == 0:
      return value

    max_lines = self.max_lines(input_width=input_width,overflow_message_length=len(overflow_message))
    max_chars = max(self.overflow_trigger - len(overflow_message),0)

    # If there are at least 2 lines, we can ignore overflow trigger.
    # each line will be at least input_width wide
    if preserve_newlines and max_lines > 1:
      if isinstance(value, str):
        # Replace all new line characters with just \n. \r\n inserts two lines in a PDF
        value = re.sub(r"[\r\n]+|\r+|\n+",r"\n",value).rstrip()
        line = 1
        retval = ""
        paras = value.split('\n')
        para = 0
        while line <= max_lines and para < len(paras):
          # add the whole paragraph if less than width of input
          if len(paras[para]) <= input_width:
            retval += paras[para] + "\n"
            line += 1
            para += 1
          else:
            # Keep taking the first input_width characters until we hit max_lines
            # or we finish the paragraph
            while line <= max_lines and len(paras[para]):
              retval += paras[para][:input_width]
              paras[para] = paras[para][input_width:]
              line += 1
            if not len(paras[para]):
              para += 1
              retval += "\n"
        # TODO: check logic here to only add overflow message when we exceed length
        if len(paras) > para:
          return retval.rstrip() + overflow_message # remove trailing newline before adding overflow message
        else:
          return retval

    # Strip newlines from strings
    if isinstance(value, str):
      if len(value) > self.overflow_trigger:
        return re.sub(r"[\r\n]+|\r+|\n+"," ",value).rstrip()[:max_chars] + overflow_message
      else:
        return re.sub(r"[\r\n]+|\r+|\n+"," ",value).rstrip()[:max_chars]

    # If the overflow item is a list or DAList
    if isinstance(value, list) or isinstance(value, DAList):
      return value[:self.overflow_trigger]
    else:
      # We can't slice objects that are not lists or strings
      return value

  def value_if_defined(self) -> Any:
    """
    Return the value of the field if it is defined, otherwise return an empty string.
    Addendum should never trigger docassemble's variable gathering.
    """
    if defined(self.field_name):
      return value(self.field_name)
    return ""

  def __str__(self):
    return str(self.value_if_defined())

  def columns(self, skip_empty_attributes:bool=True, skip_attributes:set = {'complete'} ) -> list:
    """
    Return a list of the columns in this object.

    By default, skip empty attributes and the `complete` attribute.
    """
    if hasattr(self, 'headers'):
      return self.headers
    else:
      # Use the first row as an exemplar
      try:
        first_value = self.value_if_defined()[0]

        if isinstance(first_value, dict) or isinstance(first_value, DADict):
          return list([{key:key} for key in first_value.keys()])
        elif isinstance(first_value, DAObject):
          attr_to_ignore = {'has_nonrandom_instance_name','instanceName','attrList'}
          if skip_empty_attributes:
            return [{key:key} for key in list( set(first_value.__dict__.keys()) - set(skip_attributes) - attr_to_ignore ) if safeattr(first_value, key)]
          else:
            return [{key:key} for key in list( set(first_value.__dict__.keys()) - set(skip_attributes) - attr_to_ignore )]
      except:
        return None
      # None means the value has no meaningful columns we can extract


  def type(self) -> str:
    """
    list | object_list | other
    """
    value = self.value_if_defined()
    if isinstance(value, list) or isinstance(value, DAList):
      if len(value) and (isinstance(value[0], dict) or isinstance(value[0], DADict) or isinstance(value[0], DAObject)):
        return "object_list"
      return "list"
    return "other"

  def is_list(self) -> bool:
    """
    Identify whether the field is a list, whether of objects/dictionaries or just plain variables.
    """
    return self.type() == 'object_list' or self.type() == 'list'

  def is_object_list(self) -> bool:
    """
    Identify whether the field represents a list of either dictionaries or objects.
    """
    return self.type() == 'object_list'

  def overflow_markdown(self) -> str:
    """
    Return a formatted markdown table or bulleted list representing the values in the list.

    This method does not give you any control over the output other than labels of columns,
    but you also do not need to use this output if you want to independently control the format
    of the table.
    """
    if not self.columns():
      if self.overflow_value():
        retval = "* "
        retval += "\n* ".join(self.overflow_value())
        return retval + "\n"
      else:
        return ""

    num_columns = len(self.columns())

    header = " | ".join([list(item.items())[0][1] for item in self.columns()])
    header += "\n"
    header += "|".join(["-----"] * num_columns)

    flattened_columns = []
    for column in self.columns():
      flattened_columns.append(list(column.items())[0][0])

    rows = "\n"
    for row in self.overflow_value():
      if isinstance(row, dict) or isinstance(row, DADict):
        row_values = []
        for column in flattened_columns:
          row_values.append(str(row.get(column,'')))
        rows += "|".join(row_values)
      else:
        row_values = []
        for column in flattened_columns:
          # don't trigger collecting attributes that are required to resolve
          # to a string
          try:
            row_values.append(str(getattr(row, column,'')))
          except:
            row_values.append("")
        rows += "|".join(row_values)
      rows += "\n"

    return header + rows

  def overflow_docx(self, path:str="docassemble.ALDocumentDict:data/templates/addendum_table.docx"):
    """
    Light wrapper around insert_docx_template() that inserts a formatted table into a docx
    file. If the object in the list is a plain string/int, it returns a bulleted list.

    Using this method will not give you any control at all over the formatting, but you can directly
    call field.overflow_value() instead of using this method.
    """
    return include_docx_template(path, columns=self.columns(), rows=self.overflow_value())

class ALAddendumFieldDict(DAOrderedDict):
  """
  Object representing a list of fields in your output document, together
  with the character limit for each field.

  Provides convenient methods to determine if an addendum is needed and to
  control the display of fields so the appropriate text (overflow or safe amount)
  is displayed in each context.

  Adding a new entry will implicitly set the `field_name` attribute of the field.

  optional:
    - style: if set to "overflow_only" will only display the overflow text
  """
  def init(self, *pargs, **kwargs):
    super(ALAddendumFieldDict, self).init(*pargs, **kwargs)
    self.object_type = ALAddendumField
    self.auto_gather=False
    if not hasattr(self, 'style'):
      self.style = 'overflow_only'
    if hasattr(self, 'data'):
      self.from_list(self.data)
      del self.data

  def initializeObject(self, *pargs, **kwargs):
    """
    When we create a new entry implicitly, make sure we also set the .field_name
    attribute to the key name so it knows its own field_name.
    """
    the_key = pargs[0]
    super().initializeObject(*pargs, **kwargs)
    self[the_key].field_name = the_key

  def from_list(self, data):
    for entry in data:
      new_field = self.initializeObject(entry['field_name'], ALAddendumField)
      new_field.field_name = entry['field_name']
      new_field.overflow_trigger = entry['overflow_trigger']

  def defined_fields(self, style='overflow_only'):
    """
    Return a filtered list of just the defined fields.
    If the "style" is set to overflow_only, only return the overflow values.
    """
    if style == 'overflow_only':
      return [field for field in self.values() if len(field.overflow_value())]
    else:
      return [field for field in self.values() if defined(field.field_name)]

  def overflow(self):
    return self.defined_fields(style='overflow_only')
  
  def has_overflow(self)->bool:
    """Returns True if any defined field's length exceeds the overflow trigger.
    Returns:
      bool: True if at least 1 field has "overflow" content, False otherwise.
    """
    for field in self.values():
      if field.overflow_value():
        return True
    return False      

  #def defined_sections(self):
  #  if self.style == 'overflow_only':
  #    return [section for section in self.elements if len(section.defined_fields(style=self.style))]

class DALazyAttribute(DAObject):
  """
  A DAObject with attributes that are reconsidered on every page load. Useful for
  caching information on a per-page load basis.

  Takes advantage of the way that objects are pickled in Docassemble by overriding the
  __getstate__ method Pickle uses.
  """
  def __getstate__(self):
      if hasattr(self, 'instanceName'):
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
      yesno: include_extra_document
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
  
  def init(self, *pargs, **kwargs):
    super(ALDocument, self).init(*pargs, **kwargs)
    self.initializeAttribute('overflow_fields',ALAddendumFieldDict)
    if not hasattr(self, 'default_overflow_message'):
      self.default_overflow_message = '...'
    if not hasattr(self, 'has_addendum'):
      self.has_addendum = False
    self.initializeAttribute('cache', DALazyAttribute)
    self.always_enabled = hasattr(self, 'enabled') and self.enabled


  def as_pdf(self, key:str='final', refresh:bool=True) -> DAFile:
    # Trigger some stuff up front to avoid idempotency problems
    filename = self.filename
    self.title
    self.need_addendum()
    if not filename.endswith('.pdf'):
      filename += '.pdf'

    safe_key = space_to_underscore(key)

    log_if_debug('Calling the as_pdf() method for ' + str(self.title))

    if hasattr(self.cache, safe_key):
      log_if_debug('Returning cached version of ' + self.title)
      return getattr(self.cache,  safe_key)

    if refresh:
      main_doc = self.getitem_fresh(key)
    else:
      main_doc = self[key]

    if isinstance(main_doc, DAFileCollection):
      main_doc = main_doc.pdf
      main_doc.title = self.title
      main_doc.filename = filename # Not sure if this works?

    if self.need_addendum():
      if refresh:
        addendum_doc = self.getattr_fresh('addendum')
      else:
        addendum_doc = self.addendum
      if isinstance(main_doc, DAFileCollection):
        addendum_doc = addendum_doc.pdf
      concatenated = pdf_concatenate(main_doc, addendum_doc, filename=filename)
      concatenated.title = self.title
      log_if_debug('Storing main file and addendum for ' + self.title + ' at ' + self.instanceName + '.cache.' + safe_key)
      setattr(self.cache,  safe_key, concatenated)
      return concatenated
    else:
      log_if_debug('Storing main file only ' + self.title + ' at ' + self.instanceName + '.cache.' + safe_key)
      setattr(self.cache, safe_key, main_doc)
      return main_doc

  def as_docx(self, key:str='final', refresh:bool=True) -> DAFile:
    """
    Returns the assembled document as a single DOCX file, if possible. Otherwise returns a PDF.
    """
    if self.need_addendum():
      try:
        the_file = docx_concatenate(self.as_list(key=key, refresh=refresh))
        the_file.title = self.title
        return the_file
      except:
        return self.as_pdf(key=key)

    if self._is_docx(key=key):
      the_file = self[key].docx
      the_file.title = self.title
      return the_file
    
    return self.as_pdf(key=key)

  def _is_docx(self, key:str='final'):
    """Returns True iff the file is a DOCX.
    """
    if isinstance(self[key], DAFileCollection) and hasattr(self[key], 'docx'):
      return True
    if isinstance(self[key], DAFile) and hasattr(self[key], 'docx'):
      return True
      
    return False

  def as_list(self, key:str='final', refresh:bool=True) -> List[DAFile]:
    """
    Returns a list of the document and its addendum, if any.
    Specify refresh=True if you want to generate the attachment new each time.
    This behavior is the default.
    """
    if refresh:
      if self.has_addendum and self.has_overflow():
        return [self.getitem_fresh(key), self.getattr_fresh('addendum')]
      else:
        return [self.getitem_fresh(key)]
    else:
      if self.has_addendum and self.has_overflow():
        return [self[key], self.addendum]
      else:
        return [self[key]]
      
  def need_addendum(self) -> bool:
    return hasattr(self, 'has_addendum') and self.has_addendum and self.has_overflow()

  def has_overflow(self) -> bool:
    return self.overflow_fields.has_overflow()

  def overflow(self):
    return self.overflow_fields.overflow()

  def safe_value(self, field_name:str, overflow_message:str=None, preserve_newlines:bool=False, input_width:int=80):
    """
    Shortcut syntax for accessing the "safe" (shorter than overflow trigger)
    value of a field that we have specified as needing an addendum.
    """
    if overflow_message is None:
      overflow_message = self.default_overflow_message
    return self.overflow_fields[field_name].safe_value(overflow_message=overflow_message, preserve_newlines=preserve_newlines, input_width=input_width)

  def overflow_value(self, field_name:str, overflow_message:str=None, preserve_newlines:bool=False, input_width:int=80):
    """
    Shortcut syntax for accessing the "overflow" value (amount that exceeds overflow trigger)
    for the given field as a string.

    Should mirror the "safe_value" for the same field.
    """
    if overflow_message is None:
      overflow_message = self.default_overflow_message
    return self.overflow_fields[field_name].overflow_value(overflow_message=overflow_message, preserve_newlines=preserve_newlines, input_width=input_width)

class ALStaticDocument(DAStaticFile):
  """A class that allows one-line initialization of static documents to include in an ALDocumentBundle.
  
  Note:
      You should always place the static file within the /data/static folder of a package.
      ALDocumentBundle relies on a publically accessible file. The /data/templates folder is private.
      
  Attributes:
      filename(str): the path to the file within /data/static/.
      title(str): The title that will display as a row when invoked with `download_list_html()` method
                  of an ALDocumentBundle.                  
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
      Handle files placed in /data/templates if that turns out to be useful. Likely by copying into
      a DAFile with pdf_concatenate().
  """
  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    self.has_addendum = False
    self.auto_gather = False
    self.gathered = True
    self.initializeAttribute('cache', DALazyAttribute)
    self.always_enabled = hasattr(self, 'enabled') and self.enabled

  
  def __getitem__(self, key):
    # This overrides the .get() method so that the 'final' and 'private' key always exist and
    # point to the same file.
    return self
  
  def as_list(self, key:str='final', refresh:bool=True) -> List[DAFile]:
    return [self]
  
  def as_pdf(self, key:str='final', refresh:bool=True) -> DAStaticFile:
    return pdf_concatenate(self)
    if self._is_pdf():
      return self
    else:
      return pdf_concatenate(self)
    
  def as_docx(self, key:str='final', refresh:bool=True) -> Union[DAStaticFile, DAFile]:
    """
    Returns the assembled document as a single DOCX file, if possible. Otherwise returns a PDF.
    """
    if self._is_docx():
      return self
    else:
      return self.as_pdf(key=key)
  
  def _is_docx(self, key:str="final"):
    if hasattr(self, 'extension') and self.extension.lower() == 'docx':
        return True
    if hasattr(self, 'mimetype') and self.mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return True
    return False
  
  def show(self, **kwargs):
    # TODO: this explicit conversion shouldn't be needed
    # Workaround for problem generating thumbnails without it
    return pdf_concatenate(self).show(**kwargs)
  
class ALDocumentBundle(DAList):
  """
  DAList of ALDocuments or nested ALDocumentBundles.

  Use case: providing a list of documents in a specific order.
  Example:
    - Cover page
    - Main motion form
    - Notice of Interpreter Request

  E.g., you may bundle documents one way for the court, one way for the user, one way for the
  opposing party. ALDocuments can separately be "enabled" or "disabled" for a particular run, which
  will affect their inclusion in all bundles.

  A bundle can be returned as one PDF or as a list of documents. If the list contains nested
  bundles, each nested bundle can similarly be returned as a combined PDF or a list of documents.

  required attributes:
    - filename
    - title
  optional attribute: enabled
  """

  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    if not hasattr(self, 'auto_gather'):
      self.auto_gather=False
    if not hasattr(self, 'gathered'):
      self.gathered=True
    self.initializeAttribute('cache', DALazyAttribute)
    self.always_enabled = hasattr(self, 'enabled') and self.enabled

  def as_pdf(self, key:str='final', refresh:bool=True) -> DAFile:
    safe_key = space_to_underscore(key)

    log_if_debug('Calling the as_pdf() method for bundle ' + str(self.title))

    if hasattr(self.cache, safe_key):
      log_if_debug('Returning cached version of bundle ' + self.title)
      return getattr(self.cache,  safe_key)

    if self.filename.endswith('.pdf'):
      ending = ''
    else:
      ending = '.pdf'
    files = self.enabled_documents(refresh=refresh)
    if len(files) == 1:
      # This case is simplest--we do not need to process the document at this level
      log_if_debug(f'Storing bundle for just one document {self.title} at {self.instanceName}.cache.{safe_key}')
      pdf = files[0].as_pdf(key=key, refresh=refresh)
      pdf.title = self.title
    else:
      log_if_debug(f'Storing bundle {self.title} at {self.instanceName}.cache.{safe_key}')
      pdf = pdf_concatenate([document.as_pdf(key=key, refresh=refresh) for document in files], filename=self.filename + ending)
    pdf.title = self.title
    setattr(self.cache, safe_key, pdf)
    return pdf

  def as_zip(self, key:str = 'final', refresh:bool = True, title:str = '') -> DAFile:
    '''Returns a zip file containing the whole bundle'''
    log_if_debug(f'Calling as_zip() for { str( self.title )}')

    zip_key = f'{ space_to_underscore( key )}_zip'

    # Speed up performance if can (docs say `zip_file` works like `pdf_concatenate`)
    if hasattr(self.cache, zip_key):
      log_if_debug(f'Returning cached version of { str( self.title )} zip')
      return getattr(self.cache,  zip_key)

    # strip out a possible '.pdf' ending then add '.zip'
    zipname = os.path.splitext(self.filename)[0]
    docs = [doc.as_pdf(key=key, refresh=refresh) for doc in self.enabled_documents(refresh=refresh)]
    zip = zip_file( docs, filename=zipname + '.zip' )
    if title == '':
      zip.title = self.title
    else:
      zip.title = title
    
    setattr(self.cache, zip_key, zip)
    log_if_debug(f'Stored {self.title} zip at {self.instanceName}.cache.{zip_key}')
    
    return zip
  
  def preview(self, refresh:bool=True) -> DAFile:
    return self.as_pdf(key='preview', refresh=refresh)

  def enabled_documents(self, refresh:bool=True) -> List[Any]:
    """
    Returns the enabled documents
    
    Args:
        refresh(bool): Controls whether the 'enabled' attribute is reconsidered.        
    """
    if refresh:
      retval = []
      for document in self.elements:
        if document.always_enabled:
          enabled = True
        else:
          if hasattr(document.cache, 'enabled'):
            enabled = document.cache.enabled
          else:
            document.cache.enabled = document.enabled
            enabled = document.cache.enabled
          if hasattr(document, 'enabled'):
            del document.enabled
        if enabled:
          retval.append(document)
      return retval
    else:
      return [document for document in self.elements 
          if (hasattr(document, 'always_enabled') and document.always_enabled) or document.enabled]

  def as_flat_list(self, key:str='final', refresh:bool=True) -> List[DAFile]:
    """
    Returns the nested bundle as a single flat list. This could be the preferred way to deliver forms to the
    court, e.g.--one file per court form/cover letter.
    """
    # Iterate through the list of self.templates
    # Unpack the list of documents at each step so this can be concatenated into a single list
    flat_list = []
    for document in self.enabled_documents(refresh=refresh):
      if isinstance(document, ALDocumentBundle):
        # call the bundle's as_flat_list() method to show all enabled templates.
        flat_list.extend(document.as_flat_list(key=key, refresh=refresh))
      # This is a simple document node; check if this individual template is enabled.
      else: # base case
        flat_list.extend(document.as_list(key=key, refresh=refresh))
    return flat_list

  def get_titles(self, key:str='final', refresh:bool=True) -> List[str]:
    """
    Gets all of titles of the documents in a list
    """
    flat_list = []
    for document in self.enabled_documents(refresh=refresh):
      if isinstance(document, ALDocumentBundle):
        flat_list.extend(document.get_titles(key=key, refresh=refresh))
      else:
        flat_list.append(document.title)
    return flat_list

  def as_pdf_list(self, key:str='final', refresh:bool=True) -> List[DAFile]:
    """
    Returns the nested bundles as a list of PDFs that is only one level deep.
    """
    return [doc.as_pdf(key=key, refresh=refresh) for doc in self.enabled_documents(refresh=refresh)]

  def as_editable_list(self, key:str='final', refresh:bool=True) -> List[DAFile]:
    """
    Return a flat list of the editable versions of the docs in this bundle.
    Not yet tested with editable PDFs.
    """
    docs = self.as_flat_list(key=key, refresh=refresh)
    editable = []
    for doc in docs:
      editable.append(doc.docx if hasattr(doc, 'docx') else doc.pdf)
    return editable

  def download_list_html(self, key:str='final', format:str='pdf', view:bool=True,
      refresh:bool=True, include_zip:bool = True, view_label="View", view_icon:str="eye",
      download_label:str="Download", download_icon:str="download", zip_label:str=None,
      zip_icon:str="file-archive") -> str:
    """
    Returns string of a table to display a list
    of pdfs with 'view' and 'download' buttons.
    
    `format` is one of:
    * pdf
    * docx
    * original
    """
    # Trigger some variables up top to avoid idempotency issues
    enabled_docs = self.enabled_documents(refresh=refresh)
    for doc in enabled_docs:
      doc.title
      if format == 'pdf':
        doc.as_pdf(key=key, refresh=refresh) # Generate cached file for this session

    html = f'<table class="al_table" id="{ html_safe_str(self.instanceName) }">'

    for doc in enabled_docs:
      filename_root = os.path.splitext(str(doc.filename))[0]
      # Do our best to use the provided filename + the extension from requested filetype
      if format=='original':
        download_doc = doc[key]
        download_filename = doc.filename
      if format=='docx' and doc._is_docx(key=key):
        download_doc = doc.as_docx(key=key)
        download_filename = filename_root + ".docx"
      else:
        download_doc = doc.as_pdf(key=key)
        download_filename = filename_root + ".pdf"
      
      try:
        # If it's possible, set the file extension to the actual filetype
        # This is mostly necessary if people omit the file extension in attachment block
        # for filetype="original"
        ext = next(iter(mimetypes.guess_all_extensions(download_doc.mimetype, strict=True)))
        download_filename = filename_root + ext
      except:
        pass        
      
      doc_download_button = action_button_html(
          download_doc.url_for(attachment=True, display_filename=download_filename),
          label=download_label, icon=download_icon, color="primary", size="md",
          classname='al_download' )
      if view and doc.as_pdf().url_for().endswith(".pdf"):
        doc_view_button = action_button_html(
            doc.as_pdf(key=key).url_for(attachment=False, display_filename=filename_root + ".pdf"),
            label=view_label, icon=view_icon, color="secondary", size="md", classname='al_view' )
        buttons = [ doc_view_button, doc_download_button ]
      else:
        buttons = [ doc_download_button ]
      html += table_row( doc.title, buttons )
    
    # Add a zip file row if there's more than one doc
    filename_root = os.path.splitext(str(self.filename))[0]
    if len(enabled_docs) > 1 and include_zip:
      if not zip_label:
        zip_label = str(self.zip_label)      
      zip = self.as_zip(key=key)
      zip_button = action_button_html(
          zip.url_for(attachment=False, display_filename = filename_root + ".zip"),
          label=zip_label, icon=zip_icon, color="primary", size="md", classname='al_zip' )
      html += table_row( zip.title, zip_button)

    html += '\n</table>'

    # Discuss: Do we want a table with the ability to have a merged pdf row?
    return html

  def download_html(self, key:str ='final', format:str ='pdf',
                    view:bool=True, refresh:bool=True,
                    view_label:str='View', view_icon:str='eye',
                    download_label:str="Download", download_icon:str="download") -> str:
    """
    Returns an HTML string of a table to display all the docs
    combined into one pdf with 'view' and 'download' buttons.
    """
    if format == 'docx':
      the_file = self.as_docx(key=key)
    else:
      the_file = self.as_pdf(key=key)

    doc_download_button = action_button_html(
        the_file.url_for(attachment=True),
        label=download_label,
        icon=download_icon,
        color="primary",
        size="md",
        classname='al_download')
    if view:
      doc_view_button = action_button_html(
          self.as_pdf(key=key).url_for(attachment=False),
          label=view_label,
          icon=view_icon,
          color="secondary",
          size="md",
          classname='al_view')
      buttons = [doc_view_button, doc_download_button]
    else:
      buttons = [doc_download_button]

    html = ( 
      f'<table class="al_table merged_docs" id="{html_safe_str(self.instanceName)}">'
      f'{table_row(self.title, buttons)}'
      f'\n</table>'
    )

    return html

  def send_button_html(self, key:str='final', show_editable_checkbox:bool = True)->str:
    """
    Generate HTML for an input box and button that allows someone to send
    the bundle to the specified email address.

    Optionally, display a checkbox that allows someone to decide whether or not to
    include an editable (Word) copy of the file, iff it is available.
    """
    name = html_safe_str(self.instanceName)  
    al_wants_editable_input_id = '_ignore_al_wants_editable_' + name
    al_email_input_id = '_ignore_al_doc_email_' + name
    al_send_button_id = 'al_send_email_button_' + name

    javascript_string = (
      f"javascript:aldocument_send_action("
      f"'{self.attr_name('send_email_action_event')}',"
      f"'{al_wants_editable_input_id}','{al_email_input_id}')"
    )

    return_str = f'''
  <div class="al_send_bundle {name}" id="al_send_bundle_{name}" name="al_send_bundle_{name}">
    <h5 id="al_doc_email_header">{self.get_email_copy}</h5> 
    '''
    if show_editable_checkbox:
      return_str += f'''
    <div class="form-check-container">
      <div class="form-check">
        <input class="form-check-input" type="checkbox" class="al_wants_editable" id="{al_wants_editable_input_id}">
        <label class="al_wants_editable form-check-label" for="{al_wants_editable_input_id}">{self.include_editable_documents}
        </label>
      </div>
    </div>
  '''
    return_str += f'''
  <div class="al_email_container">
    <span class="al_email_address {name} form-group row da-field-container da-field-container-datatype-email">
      <label for="{al_email_input_id}" class="al_doc_email col-form-label da-form-label datext-right">Email</label>
      <input value="{user_info().email if user_logged_in() else ''}" alt="Input box" class="form-control" type="email" size="35" name="{al_email_input_id}" id="{al_email_input_id}">
    </span>{action_button_html(javascript_string, label="Send", icon="envelope", color="primary", size="md", classname="al_send_email_button", id_tag=al_send_button_id)}

  </div>
  '''
    return_str += '</div>'  # al_send_bundle
    return return_str

  def send_email(self, to:any=None, key:str='final', editable:bool=False, template:any=None, **kwargs) -> bool:
    """
    Send an email with the current bundle as a single flat pdf or as editable documents.
    Can be used the same as https://docassemble.org/docs/functions.html#send_email with
    two optional additional params.

    keyword arguments:
    @param to {string} - Same as da send_email `to` - email address(es) or objects with such.
    @param [key] {string} - Optional. Which version of the doc. Default: 'final'
    @param [editable] {bool} - Optional. User wants the editable docs. Default: False
    @param template {object} - Same as da `send_email` `template` variable.
    @param * {*} - Any other parameters you'd send to a da `send_email` function
    """
    if not template:
      template = self.send_email_template

    if editable:
      return send_email(to=to, template=template, attachments=self.as_editable_list(key=key), **kwargs)
    else:
      return send_email(to=to, template=template, attachments=self.as_pdf(key=key), **kwargs)

  # I don't think this was actually ever used
  def table_css(self):
    """
    Return the css styles for the view/download table.
    This will be hard to develop with and it will be a bit
    harder to override for developers using this module.
    """
    return ""

class ALDocumentBundleDict(DADict):
  """
  A dictionary with named bundles of ALDocuments. In the assembly line, we
  expect to find two predetermined bundles: court_bundle and user_bundle.

  It may be helpful in some circumstances to have a "bundle" of bundles. E.g.,
  you may want to present the user multiple combinations of documents for
  different scenarios.
  """
  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    self.auto_gather=False
    self.gathered=True
    self.object_type = ALDocumentBundle
    if not hasattr(self, 'gathered'):
      self.gathered = True
    if not hasattr(self, 'auto_gather'):
      self.auto_gather=False

  def preview(self, format:str='PDF', bundle:str='user_bundle') -> DAFile:
    """
    Create a copy of the document as a single PDF that is suitable for a preview version of the
    document (before signature is added).
    """
    return self[bundle].as_pdf(key='preview', format=format)

  def as_attachment(self, format:str='PDF', bundle:str='court_bundle') -> List[DAFile]:
    """
    Return a list of PDF-ified documents, suitable to make an attachment to send_mail.
    """
    return self[bundle].as_pdf_list(key='final')

class ALExhibit(DAObject):
  """Class to represent a single exhibit, with cover page, which may contain multiple documents representing pages.
  Atributes:
      elements (list): List of individual DAFiles representing uploaded images or documents.
      cover_page (DAFile | DAFileCollection): (optional) A DAFile or DAFileCollection object created by an `attachment:` block
        Will typically say something like "Exhibit 1"
      label (str): A label, like "A" or "1" for this exhibit in the cover page and table of contents
      starting_page (int): first page number to use in table of contents
  """

  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    self.initializeAttribute('_cache', DALazyAttribute)
    self.object_type = DAFileList
    if not hasattr(self, 'starting_page'):
      self.start_page = 1

  def add_numbers(self, starting_page=None)->None:
    """
    Todo:
        Not implemented yet.
    """
    pass

  def ocr_pages(self):
    """
    Return the OCR version if it exists; otherwise the initial version of each doc in `pages`.
    """
    pages = []
    for page in self.pages:
      if hasattr(page, 'ocr_version') and hasattr(page, 'ocr_status') and page.ocr_status.ready() and not page.ocr_status.failed() and page.ocr_version.ok:
        pages.append(page.ocr_version)
      else: 
        pages.append(page)
    return pages

  def as_pdf(self, prefix='', add_page_numbers:bool=True, add_cover_page:bool=True, filename:str=None)->DAFile:
    if hasattr(self._cache, '_file'):
      return self._cache._file
    if not filename:
      filename = "exhibits.pdf"
    if add_cover_page:
      self._cache._file = pdf_concatenate(self.cover_page, self.ocr_pages(), filename=filename)
    else:
      self._cache._file = pdf_concatenate(self.ocr_pages(), filename=filename)
    return self._cache._file

  def num_pages(self)->int:
    return self.pages.num_pages()

  @property
  def complete(self):
    self.title
    self.pages.gather()
    return True

  def __str__(self):
    return self.title

class ALExhibitList(DAList):
  """
  Attributes:
      auto_label (bool): Set to True if you want exhibits to be automatically numbered for purposes of cover page 
                         and table of contents. Defaults to True.
      auto_labeler (Callable): (optional) a function or lambda to transform the index for each exhibit to a label.
                               Defaults to labels like A..Z if unspecified.
      auto_ocr (bool): Set to True if you would like exhibits to be OCR'ed in the background after they are uploaded. 
                       Defaults to True.
  """
  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    if not hasattr(self, 'auto_label'):
      self.auto_label = True
    if not hasattr(self, 'auto_labeler'):
      self.auto_labeler = alpha
    if not hasattr(self, 'auto_ocr'):
      self.auto_ocr = True
    self.object_type = ALExhibit
    self.complete_attribute = 'complete'
  
  def as_pdf(self, filename="file.pdf", add_cover_pages:bool = True)->DAFile:
    """
    Return a single PDF containing all exhibits.
    Args:
        filename (str): the filename to be assigned to the generated PDF document.
        add_cover_pages (bool): True if each exhibit should have a cover page, like "Exhibit A".
    Returns:
        A DAfile containing the rendered exhibit list as a single file.
    """
    return pdf_concatenate([exhibit.as_pdf(add_cover_page=add_cover_pages) for exhibit in self], filename=filename)

  def add_numbers(self, prefix:str='', starting_number:int=1)->None:
    """
    Add running page numbers. (TODO: not yet implemented)
    Args:
        prefix (str): The prefix before each page number. E.g., Ex-
        starting_number (int): The number that the first page will be assigned. Defaults 
                               to 1.
    """
    pass

  def _update_labels(self, auto_labeler:Callable=None)->None:
    """
    Private method to refresh labels on all exhibits.
    Args:
        auto_labeler (Callable): (optional) a lambda or function to transform index to a label, like A.
    """
    if auto_labeler is None:
      auto_labeler = self.auto_labeler

    for index, exhibit in enumerate(self.elements):
      exhibit.label = self.auto_labeler(index)

  def ocr_ready(self)->bool:
    """
    Returns:
        True iff OCR process has finished on all pages. OCR is non-blocking, and assembly will work
        even if OCR is not complete. Check this status if you want to wait to deliver a document until
        OCR is complete.
    """
    ready = True
    for exhibit in self.elements:
      for page in exhibit.pages:
        if hasattr(page, 'ocr_status'):
          ready &= page.ocr_status.ready()
    return ready

  def _update_page_numbers(self)->None:
    """
    Update the `start_page` attribute of all exhibits so it reflects current position in the list + number of pages of each document.
    """
    current_index = 1
    for exhibit in self.elements:
      exhibit.start_page = current_index
      current_index += exhibit.num_pages()

  def _ocr_docs(self):
    for exhibit in self.elements:
      if len(exhibit.pages):
        # We cannot OCR in place. It is too fragile.
        for page in exhibit.pages:
          page.ocr_version = DAFile(page.attr_name('ocr_version'))
          # psm=1 is the default which uses automatic text orientation and location detection.
          # Appears to be the most accurate method.
          page.ocr_status = page.make_ocr_pdf_in_background(page.ocr_version, psm=1)

  def hook_after_gather(self):
    """
    Private method automatically triggered when the list is fully gathered.
    """
    if len(self):
      self._update_page_numbers()
      if self.auto_label:
        self._update_labels()
    
    # TODO: implement below. Was buggy when OCRing a lot of files and OCRing in place. 
    # Switched to creating a new DAFile, but that introduced different bugs. -- third refresh breaks it. file never gets a number so not "ok"
    # if self.auto_ocr:
    #  self._ocr_docs()

class ALExhibitDocument(ALDocument):
  """Represents a collection of uploaded documents, formatted like a record appendix or exhibit list, with a table of contents and 
  optional page numbering.

  Attributes:
      exhibits (ALExhibitList): list of ALExhibit documents. Each item is a separate exhibit, which may be multiple pages.
      table_of_contents: DAFile or DAFileCollection object created by an `attachment:` block
      _cache (DAFile): a cached version of the list of exhibits. It may take
        a long time to process.
      include_table_of_contents (bool): flag to control whether a table of contents is generated for this form        
      include_exhibit_cover_pages (bool): flag to control whether cover pages are included with each separate exhibit
      add_page_numbers (bool): Flag that controls whether the as_pdf() method
        also will add Bates-stamp style page numbers and labels on each page.  

  Todo:
      * Method of making a safe link in place of the attachment (e.g., filesize limits on email)  
      
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
  """

  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    self.initializeAttribute('exhibits', ALExhibitList)
    if not hasattr(self, 'include_table_of_contents'):
      self.include_table_of_contents = True
    if not hasattr(self, 'include_exhibit_cover_pages'):
      self.include_exhibit_cover_pages = True
    self.has_addendum = False

  def has_overflow(self):
    """
    Provided for signature compatibility with ALDocument. Exhibits do not have overflow.
    """
    return False

  def __getitem__(self, key):
    # This overrides the .get() method so that the 'final' and 'private' key always exist and
    # point to the same file.
    return self
  
  def as_list(self, key:str='final', refresh:bool=True) -> List[DAFile]:
    return [self]

  def as_pdf(self, key="final", refresh:bool=True) -> DAFile:
    """
    Args:
        key (str): unused, for signature compatibility with ALDocument
    """
    filename = os.path.splitext(self.filename)[0] + ".pdf"
    
    if len(self.exhibits):
      if self.include_table_of_contents:
        return pdf_concatenate(self.table_of_contents, self.exhibits.as_pdf(add_cover_pages=self.include_exhibit_cover_pages), filename=filename)    
      else:
        return self.exhibits.as_pdf(add_cover_pages=self.include_exhibit_cover_pages, filename=filename)
    # pdf_concatenate([a.as_pdf() for a in self.exhibits], filename=self.filename)

  def as_docx(self, key:str="bool", refresh:bool=True) -> DAFile:
      return self.as_pdf()

class ALTableDocument(ALDocument):
  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    self.has_addendum = False

  def has_overflow(self):
    """
    Provided for signature compatibility with ALDocument.
    """
    return False

  def __getitem__(self, key):
    # This overrides the .get() method so that the 'final' and 'private' key always exist and
    # point to the same file.
    return self.as_pdf()
  
  def as_list(self, **kwargs) -> List[DAFile]:
    return [self]

  def as_pdf(self, **kwargs) -> DAFile:
    """
    Args:
        key (str): unused, for signature compatibility with ALDocument
    """
    return self.table.export(self.filename + '.xlsx', title=self.filename)
  
  def as_docx(self, **kwargs) -> DAFile:
    return self.as_pdf()
    

def ALUntransformedDocument(ALDocument):
  def init(self, *pargs, **kwargs):
    super().init(*pargs, **kwargs)
    self.has_addendum = False

  def has_overflow(self):
    """
    Provided for signature compatibility with ALDocument.
    """
    return False
  
  def as_list(self, **kwargs) -> List[DAFile]:
    return [self]

  def as_pdf(self, **kwargs) -> DAFile:
    """
    Args:
        key (str): unused, for signature compatibility with ALDocument
    """
    return self[key]
  
  def as_docx(self, **kwargs) -> DAFile:
    return self.as_pdf()
  
    
def unpack_dafilelist(the_file:DAFileList)->DAFile:
  """Creates a plain DAFile out of the first item in a DAFileList
  Args:
      the_file (DAFileList): an item representing an uploaded document in a Docassemble interview
  
  Returns:
      A DAFile representing the first item in the DAFileList, with a fixed instanceName attribute.
  """
  if isinstance(the_file, DAFileList):
    temp_name = the_file.instanceName
    the_file = next(iter(the_file))
    the_file.instanceName = temp_name # reset instance name to the whole object instead of index in list we got rid of
  return the_file

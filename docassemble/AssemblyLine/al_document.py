import re
from typing import List
from docassemble.base.util import log, word, DADict, DAList, DAObject, DAFile, DAFileCollection, DAFileList, defined, value, pdf_concatenate, DAOrderedDict, action_button_html, include_docx_template, user_logged_in, user_info, action_argument, send_email, docx_concatenate, reconsider

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
      return str(getattr(object, key))
    else:
      return ''
  except:
    return ""
  
def html_safe_str(the_string) -> str:
  """
  Return a string that can be used as an html class or id
  """
  return re.sub( r'[^A-Za-z0-9]+', '_', the_string )

def table_row( aldoc, key='final', view_icon="eye", download_icon="download", format="pdf", refresh=True ):
  """
  Return a string of html that is one row of a table containing
  the `.as_pdf()` contents of an AL object and its interaction buttons
  """
  pdf = aldoc.as_pdf(key=key, refresh=refresh)
  if format=="docx":
    docx = aldoc.as_docx(key=key, refresh=refresh)
  
  html = '\n\t<tr>'
  # html += '\n\t\t<td><i class="fas fa-file"></i>&nbsp;&nbsp;</td>'
  # TODO: Need to replace with proper CSS
  html += '\n\t\t<td><div><strong>' + aldoc.title + '</strong></div></td>'
  html += '\n\t\t<td>'
  html += action_button_html( pdf.url_for(), label=word("View"), size="md", icon=view_icon, color="secondary" )
  if format=="docx":
    html += action_button_html( docx.url_for(attachment=True), size="md", label=word("Download"), icon=download_icon, color="primary" )
  else:
    html += action_button_html( pdf.url_for(attachment=True), size="md", label=word("Download"), icon=download_icon, color="primary" )

  html += '\n\t</tr>'

  return html
  
class ALAddendumField(DAObject):
  """
  Object representing a single field and its attributes as related to whether
  it should be displayed in an addendum. Useful for PDF templates.
  
  The items can be strings or lists/list-like objects. It does not know
  how to handle overflow for a dictionary, e.g.
  
  Required attributes:
    - field_name->str represents the name of a docassemble variable
    - overflow_trigger->int

  Optional/planned (not implemented yet):    
    - headers->dict(attribute: display label for table)
    - field_style->"list"|"table"|"string" (optional: defaults to "string")
  """
  def init(self, *pargs, **kwargs):
    super(ALAddendumField, self).init(*pargs, **kwargs)

  def overflow_value(self, preserve_newlines=False, input_width=80, overflow_message = ""):
    """
    Try to return just the portion of the variable (list-like object or string)
    that exceeds the overflow trigger. Otherwise, return empty string.
    
    If newlines are preserved, we will use a heuristic to estimate line breaks instead
    of using absolute character limit.
    """
    last_char = max(len(self.safe_value(overflow_message = overflow_message, input_width=input_width, preserve_newlines=True)) - (max(len(overflow_message)-1,0)), 0)   
    
    if preserve_newlines and isinstance(self.value_if_defined(),str):
      # start where the safe value ends
      return self.value_if_defined()[last_char:]
      
    if isinstance(self.value_if_defined(),str):
      return self.value_if_defined()[last_char:]
    
    return self.value_if_defined()[self.overflow_trigger:]

  def max_lines(self, input_width=80, overflow_message_length=0):
    """
    Estimate the number of rows in the field in the output document.
    """
    return int(max(self.overflow_trigger-overflow_message_length,0) / input_width) + 1
        
  def value(self):    
    """
    Return the full value, disregarding overflow. Could be useful in addendum
    if you want to show the whole value without making user flip back/forth between multiple
    pages.
    """
    return self.value_if_defined()
    
  def safe_value(self, overflow_message = "", input_width=80, preserve_newlines=False):
    """
    Try to return just the portion of the variable
    that is _shorter than_ the overflow trigger. Otherwise, return empty string.
    """
    
    # Handle simplest case first
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
      
  def value_if_defined(self):
    """
    Return the value of the field if it is defined, otherwise return an empty string.
    Addendum should never trigger docassemble's variable gathering.
    """
    if defined(self.field_name):
      return value(self.field_name)
    return ""
  
  def __str__(self):
    return str(self.value_if_defined())
    
  def columns(self):
    """
    Return a list of the columns in this object.
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
          return [{key:key} for key in list( set(first_value.__dict__.keys()) - attr_to_ignore )]
      except:
        return None
      # None means the value has no meaningful columns we can extract


  def type(self):
    """
    list | object_list | other
    """
    value = self.value_if_defined()
    if isinstance(value, list) or isinstance(value, DAList):
      if len(value) and (isinstance(value[0], dict) or isinstance(value[0], DADict) or isinstance(value[0], DAObject)):
        return "object_list"
      return "list"
    return "other"                         

  def is_list(self):
    """
    Identify whether the field is a list, whether of objects/dictionaries or just plain variables.
    """
    return self.type() == 'object_list' or self.type() == 'list'
      
  def is_object_list(self):
    """
    Identify whether the field represents a list of either dictionaries or objects.
    """
    return self.type() == 'object_list'
  
  def overflow_markdown(self):
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
  
  def overflow_docx(self, path="docassemble.ALDocumentDict:data/templates/addendum_table.docx"):
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
      self.from_list(data)
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
      return [field for field in self.values() if defined(field.field_name) and len(field.overflow_value())]
    else:
      return [field for field in self.values() if defined(field.field_name)]
  
  def overflow(self):
    return self.defined_fields(style='overflow_only')
    
  #def defined_sections(self):
  #  if self.style == 'overflow_only':    
  #    return [section for section in self.elements if len(section.defined_fields(style=self.style))]
  
class ALDocument(DADict):
  """
  An opinionated collection of typically three attachment blocks:
  1. The final version of a document, at typical key "final"
  2. The preview version of a document, at typical key "preview"
  3. An addendum of a document, at the attribute `addendum`
  
  Each form that an interview generates will get its own ALDocument object.
  
  This should really relate to one canonical document in different states. Not multiple
  unrelated output documents that might get delivered together, except the addendum.
  
  The "addendum" attribute will typically be handled in a generic object block.
  Multiple documents can use the same addendum template, with just the case caption
  varying.
  
  Required attributes:
    - filename: name used for output PDF
    - title: display name for the output PDF
    - enabled
    - has_addendum: set to False if the document never has overflow, like for a DOCX template
  
  Optional attribute:
    - addendum: an attachment block
    - overflow_fields
  
  """
  def init(self, *pargs, **kwargs):
    super(ALDocument, self).init(*pargs, **kwargs)
    self.initializeAttribute('overflow_fields',ALAddendumFieldDict)
    if not hasattr(self, 'default_overflow_message'):
      self.default_overflow_message = ''

  def as_pdf(self, key='final', refresh=True):
    if self.filename.endswith('.pdf'):
      ending = ''
    else:
      ending = '.pdf'
    pdf = pdf_concatenate(self.as_list(key=key, refresh=refresh), filename=self.filename + ending)
    pdf.title = self.title
    return pdf
  
  def as_docx(self, key='final', refresh=True):
    """
    Returns the assembled document as a single DOCX file, if possible. Otherwise returns a PDF.
    """
    try:
      the_file = docx_concatenate(self.as_list(key=key, refresh=refresh))
      the_file.title = self.title
      return the_file
    except:
      return self.as_pdf(key=key)

  def as_list(self, key='final', refresh=True):
    """
    Returns a list of the document and its addendum, if any.
    Specify refresh=True if you want to generate the attachment new each time.
    This behavior is the default.
    """
    if refresh:
      if key in self.elements:
        reconsider(self.instanceName + '["' + key + '"]')
      if hasattr(self, 'addendum'):
        reconsider(self.attr_name('addendum'))
    if self.has_addendum and self.has_overflow():
      return [self[key], self.addendum]
    else:
      return [self[key]]
    
  def has_overflow(self):
    return len(self.overflow()) > 0
  
  def overflow(self):
    return self.overflow_fields.overflow()
    
  def safe_value(self, field_name, overflow_message=None, preserve_newlines=False):
    """
    Shortcut syntax for accessing the "safe" (shorter than overflow trigger)
    value of a field that we have specified as needing an addendum.
    """
    if overflow_message is None:
      overflow_message = self.default_overflow_message
    return self.overflow_fields[field_name].safe_value(overflow_message=overflow_message, preserve_newlines=preserve_newlines)

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
    super(ALDocumentBundle, self).init(*pargs, **kwargs)
    self.auto_gather=False
    self.gathered=True
    # self.initializeAttribute('templates', ALBundleList)
    
  def as_pdf(self, key='final', refresh=True):
    if self.filename.endswith('.pdf'):
      ending = ''
    else:
      ending = '.pdf'
    pdf = pdf_concatenate(self.as_flat_list(key=key, refresh=refresh), filename=self.filename + ending)
    pdf.title = self.title
    return pdf
  
  def preview(self, refresh=True):
    return self.as_pdf(key='preview', refresh=refresh)
  
  def as_flat_list(self, key='final', refresh=True):
    """
    Returns the nested bundle as a single flat list.
    """
    # Iterate through the list of self.templates
    # Unpack the list of documents at each step so this can be concatenated into a single list
    flat_list = []
    for document in self:
      if isinstance(document, ALDocumentBundle):
        # call the bundle's as_flat_list() method to show all enabled templates.
        flat_list.extend(document.as_flat_list(key=key, refresh=refresh))
      # This is a simple document node; check if this individual template is enabled.
      elif document.enabled: # base case
        flat_list.extend(document.as_list(key=key, refresh=refresh))
    return flat_list

  def get_titles(self, key='final') -> List[str]:
    """
    Gets all of titles of the documents in a list
    """
    flat_list = []
    for document in self:
      if isinstance(document, ALDocumentBundle):
        flat_list.extend(document.get_titles(key=key))
      elif document.enabled:
        flat_list.append(document.title)
    return flat_list

  def as_pdf_list(self, key='final', refresh=True):
    """
    Returns the nested bundles as a list of PDFs that is only one level deep.
    """
    return [doc.as_pdf(key=key, refresh=True) for doc in self if isinstance(doc, ALDocumentBundle) or doc.enabled]
  
  def as_editable_list(self, key='final', refresh=True):
    """
    Return a flat list of the editable versions of the docs in this bundle.
    Not yet tested with editable PDFs.
    """
    docs = self.as_flat_list(key=key, refresh=refresh)
    editable = []
    for doc in docs:
      editable.append(doc.docx if hasattr(doc, 'docx') else doc.pdf)
    return editable  
  
  def download_list_html(self, key='final', format='pdf', view=True, refresh=True) -> str:
    """
    Returns string of a table to display a list
    of pdfs with 'view' and 'download' buttons.
    """
    # TODO: wire up the format and view keywords
    # TODO: make icons configurable
    html ='<table class="al_table" id="' + html_safe_str(self.instanceName) + '">'
    
    for doc in self:
      if doc.enabled:
        html += table_row(doc, key=key, format=format, refresh=True)
    
    html += '\n</table>'
    
    # Discuss: Do we want a table with the ability to have a merged pdf row?
    return html
  
  def download_html(self, key: str ='final', format: str ='pdf',
                    view:bool=True, refresh:bool=True) -> str:
    """
    Returns an HTML string of a table to display all the docs
    combined into one pdf with 'view' and 'download' buttons.
    """
    html ='<table class="al_table merged_docs" id="' + html_safe_str(self.instanceName) + '">'
    html += table_row( self, key=key, format=format, refresh=True )
    html += '\n</table>'
    
    return html
  
  def send_button_html(self, key='final'):
    name = re.sub(r'[^A-Za-z0-9]+','_', self.instanceName)  # safe name for classes and ids
    al_wants_editable_input_id = 'al_wants_editable_' + name
    al_email_input_id = 'al_doc_email_' + name
    al_send_button_id = "al_send_email_button_"+name
    
    javascript_string = "javascript:aldocument_send_action('" + \
      self.attr_name('send_email_action_event') + \
      "','" + al_wants_editable_input_id + "','" + \
      al_email_input_id + "')"
    
    return '''
  <div class="al_send_bundle '''+name+'''" id="al_send_bundle_'''+name+'''" name="al_send_bundle_'''+name+'''">
  <h4 id="al_doc_email_header">Get a copy of the documents in email</h4>  
  <div class="al_email_container">
  <span class="al_email_address '''+name+''' form-group row da-field-container da-field-container-datatype-email">
    <label for="'''+al_email_input_id+'''" class="al_doc_email col-form-label da-form-label datext-right">Email</label>
    <input value="''' + (user_info().email if user_logged_in() else '') + '''" alt="Input box" class="form-control" type="email" name="'''+al_email_input_id+'''" id="'''+al_email_input_id+'''">
  </span>''' + action_button_html(javascript_string, label="Send", icon="envelope", color="primary", size="md", classname="al_send_email_button", id_tag=al_send_button_id) + "\n" + '''
    </div>
    <div class="form-check-container"><div class="form-check">
    <input class="form-check-input" type="checkbox" class="al_wants_editable" id="'''+al_wants_editable_input_id+'''">
    <label class="al_wants_editable form-check-label" for="'''+al_wants_editable_input_id+'''">'''\
      + word("Include an editable copy") + '''
    </label>
  </div></div>
  '''
    
  def send_email(self, to:any=None, key:str='final', editable:bool=False, template=None, **kwargs):
    """
    Send an email with the current bundle as a single flat pdf or as editable documents.
    Can be used the same as https://docassemble.org/docs/functions.html#send_email with 
    two optional additional params.
    
    keyword arguments:
    @param [editable] {bool} - Optional. User wants the editable docs. Default: False
    @param [key] {string} - Optional. Which version of the doc. Default: 'final'
    @param to {string} - Same as da send_email `to` - email address(es) or objects with such.
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
  A dictionary with named bundles of ALDocuments.
  In the assembly line, we expect to find two predetermined bundles:
  court_bundle and user_bundle.
  
  It may be helpful in some circumstances to have a "bundle" of bundles. E.g.,
  you may want to present the user multiple combinations of documents for
  different scenarios.
  """
  def init(self, *pargs, **kwargs):
    super(ALBundleList, self).init(*pargs, **kwargs)
    self.auto_gather=False
    self.gathered=True
    self.object_type = ALBundle
    if not hasattr(self, 'gathered'):
      self.gathered = True
    if not hasattr(self, 'auto_gather'):
      self.auto_gather=False

  def preview(format='PDF', bundle='user_bundle'):
    """
    Create a copy of the document as a single PDF that is suitable for a preview version of the 
    document (before signature is added).
    """
    return self[bundle].as_pdf(key='preview', format=format)
  
  def as_attachment(format='PDF', bundle='court_bundle'):
    """
    Return a list of PDF-ified documents, suitable to make an attachment to send_mail.
    """
    return self[bundle].as_pdf_list(key='final')

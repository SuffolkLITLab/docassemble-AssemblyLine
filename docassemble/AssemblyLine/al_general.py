from typing import Dict, List, Union
from docassemble.base.util import Address, Individual, DAList, date_difference, name_suffix, states_list, comma_and_list, word, comma_list, url_action, get_config, phone_number_is_valid, validation_error, DAWeb, get_config, as_datetime, DADateTime, subdivision_type
from docassemble.base.functions import DANav
import re

__all__ = ['ALAddress', 
           'ALAddressList', 
           'ALPeopleList', 
           'ALIndividual', 
           'section_links', 
           'is_phone_or_email',
           'section_links',
           'Landlord',
           'Tenant',
           'HousingAuthority',
           'Applicant',
           'Abuser',
           'Survivor',
           'PeopleList',           
           'VCIndividual',
           'AddressList',
           'Applicant',
           'Abuser',
           'Survivor',
           'github_modified_date',
           'will_send_to_real_court',
           'safe_subdivision_type']

##########################################################
# Base classes

def safe_subdivision_type(country_code):
  try:
    return subdivision_type(country_code)
  except:
    return None

class ALAddress(Address):
  # Future-proofing TODO: this class can be used to help handle international addresses in the future.
  # Most likely, ask for international address as just 3 unstructured lines. Key thing is
  # the built-in address object requires some fields to be defined that we don't want to require of
  # international addresses when you want to render it to text.

  def address_fields(self, country_code=None, default_state=None, show_country=False):
    fields = [
      {"label": str(self.address_label), "address autocomplete": True, "field": self.attr_name('address')},
      {"label": str(self.unit_label), "field": self.attr_name('unit'), "required": False},
      {"label": str(self.city_label), "field": self.attr_name("city")},
    ]
    if country_code:
      fields.append(
        {"label": str(self.state_label), "field": self.attr_name("state"), "code": "states_list(country_code='{}')".format(country_code), "default": default_state if default_state else ''}
      )
    else:
      fields.append(
        {"label": str(self.state_label), "field": self.attr_name("state"), "default": default_state if default_state else ''}
      )      
    if country_code == "US":
      fields.append(
        {"label": str(self.zip_label), "field": self.attr_name('zip'), "required": False}
      )
    else:
      fields.append(
        # We have code in ALWeaver that relies on "zip", so keep attribute same for now
        {"label": str(self.postal_code_label), "field": self.attr_name('zip'), "required": False}
      )
      
    if show_country:
      fields.append({"label": self.country_label, "field": self.attr_name("country"), "required": False, "code": "countries_list()", "default": country_code})
      # NOTE: using , "datatype": "combobox" might be nice but does not play together well w/ address autocomplete
    return fields      
    

class ALAddressList(DAList):
  """Store a list of Address objects"""
  def init(self, *pargs, **kwargs):
    super(ALAddressList, self).init(*pargs, **kwargs)
    self.object_type = ALAddress

  def __str__(self):
    return comma_and_list([item.on_one_line() for item in self])

class ALPeopleList(DAList):
  """Used to represent a list of people. E.g., defendants, plaintiffs, children"""
  def init(self, *pargs, **kwargs):
    super(ALPeopleList, self).init(*pargs, **kwargs)
    self.object_type = ALIndividual

  def names_and_addresses_on_one_line(self, comma_string:str='; ') -> str:
    """Returns the name of each person followed by their address, separated by a semicolon"""
    return comma_and_list([str(person) + ', ' + person.address.on_one_line() for person in self], comma_string=comma_string)

  def familiar(self) -> str:
    return comma_and_list([person.name.familiar() for person in self])

  def familiar_or(self) -> str:
    return comma_and_list([person.name.familiar() for person in self],and_string=word("or"))

class ALIndividual(Individual):
  """Used to represent an Individual on the assembly line project.
  Two custom attributes are objects and so we need to initialize: `previous_addresses` 
  and `other_addresses`
  """
  previous_addresses: ALAddressList
  other_addresses: ALAddressList
  mailing_address: ALAddress

  def init(self, *pargs, **kwargs):
    super(ALIndividual, self).init(*pargs, **kwargs)
    # Initialize the attributes that are themselves objects. Requirement to work with Docassemble
    # See: https://docassemble.org/docs/objects.html#ownclassattributes
    
    # NOTE: this stops you from passing the address to the constructor
    self.reInitializeAttribute('address',ALAddress)
    
    if not hasattr(self, 'previous_addresses'):
      self.initializeAttribute('previous_addresses', ALAddressList)
    if not hasattr(self, 'other_addresses'):
      self.initializeAttribute('other_addresses', ALAddressList)
    if not hasattr(self, 'mailing_address'):
      self.initializeAttribute('mailing_address',ALAddress)

  def signature_if_final(self, i: str):
    if i == 'final':
      return self.signature
    else:
      return ''

  def phone_numbers(self) -> str:
    nums = []
    if hasattr(self, 'mobile_number') and self.mobile_number:
      nums.append({self.mobile_number: 'cell'})
    if hasattr(self, 'phone_number') and self.phone_number:
      nums.append({self.phone_number: 'other'})
    if len(nums) > 1:      
      return comma_list([list(num.keys())[0] + ' (' + list(num.values())[0] + ')' for num in nums])
    elif len(nums):
      return list(nums[0].keys())[0]
    else:
      return ''
  
  def contact_methods(self)-> str:
    """Method to return a formatted string with all provided contact methods of the individual:
        * Phone number(s)
        * Email
        * other method
    Returns:
        str: Formatted string
    """
    methods = []
    if self.phone_numbers():
      methods.append({self.phone_numbers(): word("by phone at ")})
    if hasattr(self, 'email') and self.email:
      methods.append({self.email: word("by email at ")})
    if hasattr(self, 'other_contact_method') and self.other_contact_method:
      methods.append({self.other_contact_method: "by "})
    
    return comma_and_list([list(method.values())[0] + list(method.keys())[0] for method in methods if len(method)], and_string=word("or"))
  
  def merge_letters(self, new_letters: str):
    # TODO: move to 209A package
    """If the Individual has a child_letters attribute, add the new letters to the existing list"""
    if hasattr(self, 'child_letters'):
      self.child_letters = filter_letters([new_letters, self.child_letters])
    else:
      self.child_letters = filter_letters(new_letters)

  def formatted_age(self) -> str:
    dd = date_difference(self.birthdate)
    if dd.years >= 2:
      return '%d years' % (int(dd.years),)
    if dd.weeks > 12:
      return '%d months' % (int(dd.years * 12.0),)
    if dd.weeks > 2:
      return '%d weeks' % (int(dd.weeks),)
    return '%d days' % (int(dd.days),)
  
  # This design helps us translate the prompts for common fields just once
  def name_fields(self, person_or_business:str = 'person', show_suffix=True) -> List[Dict[str, str]]:
    """
    Return suitable field prompts for a name. If `uses_parts` is None, adds the 
    proper "show ifs" and uses both the parts and the single entry
    """
    if person_or_business == 'person':
      fields = [
        {"label": str(self.first_name_label), "field": self.attr_name('name.first')},
        {"label": str(self.middle_name_label), "field": self.attr_name('name.middle'), "required": False},
        {"label": str(self.last_name_label), "field": self.attr_name("name.last")},
      ]
      if show_suffix:
        fields.append({"label": str(self.suffix_label), "field": self.attr_name("name.suffix"), "choices": name_suffix(), "required": False})
      return fields        
    elif person_or_business == 'business':
      # Note: we don't make use of the name.text field for simplicity
      # TODO: this could be reconsidered`, but name.text tends to lead to developer error
      return [
        {"label": str(self.business_name_label), "field": self.attr_name('name.first')}
      ]
    else:
      # Note: the labels are template block objects: if they are keys,
      # they should be converted to strings first
      show_if_indiv = {"variable": self.attr_name("person_type"), "is": "ALIndividual"}
      show_if_business = {"variable": self.attr_name("person_type"), "is": "business"}
      fields = [
        {"label": str(self.person_type_label), "field": self.attr_name('person_type'),
         "choices": [{str(self.individual_choice_label): "ALIndividual"},
                     {str(self.business_choice_label): "business"}],
         "input type": "radio", "required": True},
        # Individual questions
        {"label": str(self.first_name_label), "field": self.attr_name('name.first'),
         "show if": show_if_indiv},
        {"label": str(self.middle_name_label), "field": self.attr_name('name.middle'), "required": False,
         "show if": show_if_indiv},
        {"label": str(self.last_name_label), "field": self.attr_name("name.last"),
         "show if": show_if_indiv}
      ]
      if show_suffix:
        fields.append({"label": str(self.suffix_label), "field": self.attr_name("name.suffix"), "choices": name_suffix(), "required": False, 'show if': show_if_indiv})
      fields.append(        
        # Business names
        {"label": str(self.business_name_label), "field": self.attr_name('name.first'),
         "show if": show_if_business} 
      )
      return fields
 
  def address_fields(self, country_code:str="US", default_state:str=None, show_country:bool=False) -> List[Dict[str, str]]:
    """
    Return field prompts for address.
    """
    # TODO make this more flexible to work w/ homeless individuals and
    # international addresses
    return self.address.address_fields(country_code=country_code, default_state=default_state, show_country=show_country)
  
  def gender_fields(self, show_help=False):
    """
    Return a standard gender input with "self described" option.
    """
    choices = [
        {str(self.gender_female_label): 'female'},
        {str(self.gender_male_label): 'male'},
        {str(self.gender_nonbinary_label): 'nonbinary'},
        {str(self.gender_prefer_not_to_say_label): 'prefer-not-to-say'},
        {str(self.gender_prefer_self_described_label): 'self-described'},
        {str(self.gender_unknown_label): 'unknown'},
    ]
    self_described_input = {"label": str(self.gender_self_described_label),
                            "field": self.attr_name('gender'),
                            "show if": {"variable": self.attr_name('gender'),
                                        "is": 'self-described'},
                           }
    if show_help:
      return [
        {"label": str(self.gender_label),
         "field": self.attr_name('gender'),
         "choices": choices,
         "help": str(self.gender_help_text)
        },
        self_described_input
      ]
    else:
      return [
        {"label": self.gender_label,
         "field": self.attr_name('gender'),
         "choices": choices,
        },
        self_described_input
      ]
      
  @property
  def gender_male(self):
    """Provide True/False for 'male' gender to assist with checkbox filling
    in PDFs with "skip undefined" turned on."""
    return self.gender == 'male'
  
  @property
  def gender_female(self):
    """Provide True/False for 'female' gender to assist with checkbox filling
    in PDFs with "skip undefined" turned on."""
    return self.gender == 'female'
  
  @property
  def gender_other(self):
    """Provide True/False for 'other' gender to assist with checkbox filling
    in PDFs with "skip undefined" turned on for forms without more inclusive options."""
    return ((self.gender != 'male') and (self.gender != 'female'))
  
  @property
  def gender_nonbinary(self):
    """Provide True/False for 'nonbinary' gender to assist with checkbox filling
    in PDFs with "skip undefined" turned on."""
    return self.gender == 'nonbinary'
  
  @property
  def gender_unknown(self):
    """Provide True/False for 'unknown' gender to assist with checkbox filling
    in PDFs with "skip undefined" turned on."""
    return self.gender == 'unknown'
  
  @property
  def gender_undisclosed(self):
    """Provide True/False for 'prefer-not-to-say' gender to assist with checkbox filling
    in PDFs with "skip undefined" turned on."""
    return self.gender == 'prefer-not-to-say'  
  
  @property
  def gender_self_described(self):
    """Provide True/False for 'self-described' gender to assist with checkbox filling
    in PDFs with "skip undefined" turned on."""    
    return not (self.gender in ['prefer-not-to-say','male','female','unknown','nonbinary'])
  
  def contact_fields(self):
    """
    Return field prompts for other contact info
    """
    pass
  
  @property
  def initials(self):
    """Return the individual's initials, like QKS for Quinten K Steenhuis"""
    return f"{self.name.first[:1]}{self.name.middle[:1] if hasattr(self.name,'middle') else ''}{self.name.last[:1]}"

def section_links(nav: DANav) -> List[str]:
  """Returns a list of clickable navigation links without animation."""
  sections = nav.get_sections()
  section_link = []
  for section in sections:
    for key in section:
      section_link.append('[' + section[key] + '](' + url_action(key) + ')' )

  return section_link    

########################################################
# Subject-specific classes

class Landlord(ALIndividual):
  pass

class Tenant(ALIndividual):
  pass

class HousingAuthority(Landlord):
  pass

class Applicant(Tenant):
  pass

class Abuser(ALIndividual):
  pass

class Survivor(ALIndividual):
  pass

########################################################
# Compatibility layer to help with migration

# TODO: consider removing after packages migrated

class VCIndividual(ALIndividual):
  pass

class AddressList(ALAddressList):
  pass

class PeopleList(ALPeopleList):
  pass

########################################################
# Miscellaneous functions needed for baseline questions
# These could go in toolbox but keeping here to reduce packages
# needed for baseline running.

def will_send_to_real_court() -> bool:
  """Dev or root needs to be in the URL root: can change in the config file"""
  return not ('dev' in get_config('url root') or 
              'test' in get_config('url root') or
              'localhost' in get_config('url root'))

# This one is only used for 209A--should move there along with the combined_letters() method
def filter_letters(letter_strings: Union[List[str], str]) -> str:
  """Used to take a list of letters like ["A","ABC","AB"] and filter out any duplicate letters."""
  # There is probably a cute one liner, but this is easy to follow and
  # probably same speed
  unique_letters = set()
  if isinstance(letter_strings, str):
    letter_strings = [letter_strings]
  for string in letter_strings:
    if string: # Catch possible None values
      for letter in string:
        unique_letters.add(letter)
  try:
    retval = ''.join(sorted(unique_letters))
  except:
    retval = ''
  return retval

# Note: removed "combined_locations" because it is too tightly coupled to MACourts.py right now

def fa_icon(icon:str, color:str="primary", color_css:str=None, size:str="sm"):
  """
  Return HTML for a font-awesome icon of the specified size and color. You can reference
  a CSS variable (such as Bootstrap theme color) or a true CSS color reference, such as 'blue' or 
  '#DDDDDD'. Defaults to Bootstrap theme color "primary".
  """
  if not color and not color_css:
    return ':' + icon + ':' # Default to letting Docassemble handle it
  elif color_css:
    return '<i class="fa fa-' + icon + ' fa-' + size + '" style="color:' + color_css + ';"></i>'
  else:
    return '<i class="fa fa-' + icon + ' fa-' + size + '" style="color:var(--' + color + ');"></i>'

def is_phone_or_email(text:str)->bool:
  """
  Returns True if the string is either a valid phone number or a valid email address.
  Email validation is extremely minimal--just checks for an @ sign between two non-zero length 
  strings.
  """
  if re.match("\S+@\S+", text) or phone_number_is_valid(text):
    return True
  else:
    validation_error("Enter a valid phone number or email address")


def github_modified_date(github_user:str, github_repo_name:str)->Union[DADateTime, None]:
  """
  Returns the date that the given GitHub repository was modified or None if API call fails.
  
  Will check for the presence of credentials in the configuration labeled "github readonly"
  in this format:
  
  github readonly:
    username: YOUR_GITHUB_USERNAME
    password: YOUR_GITHUB_PRIVATE_TOKEN
    type: basic    

  If no valid auth information is in the configuration, it will fall back to anonymous authentication.
  The GitHub API is rate-limited to 60 anonymous API queries/hour.    
  """
  github_readonly_web = DAWeb(base_url="https://api.github.com")
  res = github_readonly_web.get("repos/" + github_user + '/' + github_repo_name, auth=get_config("github readonly"))
  if res and res.get('pushed_at'):
    return as_datetime(res.get('pushed_at'))
  else:
    return None
  
  
  
  
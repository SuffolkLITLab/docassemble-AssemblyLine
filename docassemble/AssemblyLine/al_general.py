from docassemble.base.functions import comma_and_list, word, comma_list, url_action
from docassemble.base.util import Address, Individual, DAList, Person, date_difference

class AddressList(DAList):
  """Store a list of Address objects"""
  def init(self, *pargs, **kwargs):
    super(AddressList, self).init(*pargs, **kwargs)
    self.object_type = Address

  def __str__(self):
    return comma_and_list([item.on_one_line() for item in self])

class PeopleList(DAList):
  """Used to represent a list of people. E.g., defendants, plaintiffs, children"""
  def init(self, *pargs, **kwargs):
    super(PeopleList, self).init(*pargs, **kwargs)
    self.object_type = VCIndividual

  def names_and_addresses_on_one_line(self, comma_string='; '):
    """Returns the name of each person followed by their address, separated by a semicolon"""
    return comma_and_list([str(person) + ', ' + person.address.on_one_line() for person in self], comma_string=comma_string)

  def familiar(self):
    return comma_and_list([person.name.familiar() for person in self])

  def familiar_or(self):
    return comma_and_list([person.name.familiar() for person in self],and_string=word("or"))

class VCIndividual(Individual):
  """Used to represent an Individual on the assembly line/virtual court project.
  Two custom attributes are objects and so we need to initialize: `previous_addresses` 
  and `other_addresses`
  """
  def init(self, *pargs, **kwargs):
    super(VCIndividual, self).init(*pargs, **kwargs)
    # Initialize the attributes that are themselves objects. Requirement to work with Docassemble
    # See: https://docassemble.org/docs/objects.html#ownclassattributes
    if not hasattr(self, 'previous_addresses'):
      self.initializeAttribute('previous_addresses', AddressList)
    if not hasattr(self, 'other_addresses'):
      self.initializeAttribute('other_addresses', AddressList)

  def phone_numbers(self):
    nums = []
    if hasattr(self, 'mobile_number') and self.mobile_number:
      nums.append(self.mobile_number + ' (cell)')
    if hasattr(self, 'phone_number') and self.phone_number:
      nums.append(self.phone_number + ' (other)')
    return comma_list(nums)
  
  def merge_letters(self, new_letters):
    """If the Individual has a child_letters attribute, add the new letters to the existing list"""
    if hasattr(self, 'child_letters'):
      self.child_letters = filter_letters([new_letters, self.child_letters])
    else:
      self.child_letters = filter_letters(new_letters)

  def formatted_age(self):
    dd = date_difference(self.birthdate)
    if dd.years >= 2:
      return '%d years' % (int(dd.years),)
    if dd.weeks > 12:
      return '%d months' % (int(dd.years * 12.0),)
    if dd.weeks > 2:
      return '%d weeks' % (int(dd.weeks),)
    return '%d days' % (int(dd.days),)

def section_links(nav):
  """Returns a list of clickable navigation links without animation."""
  sections = nav.get_sections()
  section_link = []
  for section in sections:
    for key in section:
      section_link.append('[' + section[key] + '](' + url_action(key) + ')' )

  return section_link    
	
def combined_locations(locations):
    """Accepts a list of locations, and combines locations that share a
    latitude/longitude in a way that makes a neater display in Google Maps.
    Designed for MACourts class but may work for other objects that subclass DAObject.
    Will not work for base Address class but should never be needed for that anyway
    Rounds lat/longitude to 3 significant digits
    """

    places = list()

    for location in locations:
        if isinstance(location, DAObject):
            if not has_match(places,location):
                places.append(MAPlace(location=location.location, address=copy.deepcopy(location.address), description = str(location)))
            else:
                for place in places:
                    if match(place,location):
                        if hasattr(place, 'description') and str(location) not in place.description:
                            place.description += "  [NEWLINE]  " + str(location)
    return places
	
def fa_icon(icon, color="primary", color_css=None, size="sm"):
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

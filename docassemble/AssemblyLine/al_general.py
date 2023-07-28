from typing import Dict, List, Literal, Union, Optional
from docassemble.base.util import (
    Address,
    as_datetime,
    capitalize,
    comma_and_list,
    comma_list,
    country_name,
    DADateTime,
    DADict,
    DAFile,
    DAList,
    date_difference,
    DAWeb,
    ensure_definition,
    get_config,
    get_country,
    her,
    his,
    Individual,
    IndividualName,
    its,
    name_suffix,
    phone_number_formatted,
    phone_number_is_valid,
    state_name,
    states_list,
    subdivision_type,
    their,
    this_thread,
    url_action,
    validation_error,
    word,
    your,
)
import random
import re
import pycountry

__all__ = [
    "Abuser",
    "Abuser",
    "AddressList",
    "ALAddress",
    "ALAddressList",
    "ALIndividual",
    "ALPeopleList",
    "Applicant",
    "Applicant",
    "github_modified_date",
    "has_parsable_pronouns",
    "HousingAuthority",
    "is_phone_or_email",
    "Landlord",
    "language_name",
    "parse_custom_pronouns",
    "PeopleList",
    "safe_subdivision_type",
    "section_links",
    "section_links",
    "Survivor",
    "Survivor",
    "Tenant",
    "VCIndividual",
    "will_send_to_real_court",
]

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

    def address_fields(
        self,
        country_code: Optional[str] = None,
        default_state: Optional[str] = None,
        show_country: bool = False,
        show_county: bool = False,
        show_if: Union[str, Dict[str, str], None] = None,
        allow_no_address: bool = False,
    ):
        """
            Return a YAML structure representing the list of fields for the object's address.
            Optionally, allow the user to specify they do not have an address.
            NOTE: if you set allow_no_address to True, you must make sure to trigger
            the question with `users[0].address.has_no_address` rather than
            `users[0].address.address`.
            Optionally, add a `show if` modifier to each field. The `show if` modifier
            will not be used if the `allow_no_address` modifier is used.
        `country_code` should be an ISO-3166-1 alpha-2 code (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements)

            NOTE: address_fields() is stateful if you:
            1. Use the `country_code` parameter and;
            1. Do not use the `show_country` parameter, and
            1. `country_code` has a different value than `get_country()`.

            Under these circumstances, address_fields() will set the `country` attribute of the Address
            to `country_code`.
        """
        # make sure the state name still returns a meaningful value if the interview country
        # differs from the server's country.
        if country_code and country_code != get_country() and not show_country:
            self.country = country_code
        if not country_code:
            country_code = get_country()
        if allow_no_address:
            fields = [
                {
                    "label": str(self.has_no_address_label),
                    "field": self.attr_name("has_no_address"),
                    "datatype": "yesno",
                },
                {
                    "label": str(self.has_no_address_explanation_label),
                    "field": self.attr_name("has_no_address_explanation"),
                    "datatype": "area",
                    "rows": 2,
                    "help": str(self.has_no_address_explanation_help),
                    "show if": self.attr_name("has_no_address"),
                    "required": False,
                },
            ]
        else:
            fields = []
        fields.extend(
            [
                {
                    "label": str(self.address_label),
                    "address autocomplete": bool(
                        (get_config("google") or {}).get("google maps api key")
                    ),
                    "field": self.attr_name("address"),
                },
                {
                    "label": str(self.unit_label),
                    "field": self.attr_name("unit"),
                    "required": False,
                },
            ]
        )
        if allow_no_address:
            fields[-1]["hide if"] = self.attr_name("has_no_address")
            fields[-2]["hide if"] = self.attr_name("has_no_address")

        fields.append({"label": str(self.city_label), "field": self.attr_name("city")})

        if country_code:
            fields.append(
                {
                    "label": str(self.state_label),
                    "field": self.attr_name("state"),
                    "code": "states_list(country_code='{}')".format(country_code),
                    "default": default_state if default_state else "",
                }
            )
        else:  # not showing country and not showing country code
            fields.append(
                {
                    "label": str(self.state_label),
                    "field": self.attr_name("state"),
                    "default": default_state if default_state else "",
                }
            )
        if country_code == "US":
            fields.append(
                {
                    "label": str(self.zip_label),
                    "field": self.attr_name("zip"),
                    "required": False,
                }
            )
        else:
            fields.append(
                # We have code in ALWeaver that relies on "zip", so keep attribute same for now
                {
                    "label": str(self.postal_code_label),
                    "field": self.attr_name("zip"),
                    "required": False,
                }
            )
        if allow_no_address:
            fields[-1]["hide if"] = self.attr_name("has_no_address")

        if show_county:
            fields.append(
                {
                    "label": str(self.county_label),
                    "field": self.attr_name("county"),
                    "required": False,
                }
            )
        if show_country:
            fields.append(
                {
                    "label": str(self.country_label),
                    "field": self.attr_name("country"),
                    "required": False,
                    "code": "countries_list()",
                    "default": country_code,
                }
            )
            # NOTE: using , "datatype": "combobox" might be nice but does not play together well w/ address autocomplete
        if not allow_no_address:
            # show if isn't compatible with the hide if logic for `allow_no_address`
            if show_if:
                for field in fields:
                    field["show if"] = show_if

        return fields

    def formatted_unit(
        self, language: Optional[str] = None, require: bool = False, bare: bool = False
    ) -> str:
        """
        Returns the unit, formatted appropriately.

        Args:
            language (str, optional): The language in which to format the unit. Defaults to None (which uses system language).
            require (bool, optional): A flag indicating whether the unit is required. If set to True, the function will
                                    raise an error if the unit attribute does not exist. Defaults to False.
            bare (bool, optional): A flag indicating whether to add the word 'Unit' before the unit number. If set to
                                True, the function will not add 'Unit' regardless of other conditions. Defaults to False.

        Returns:
            str: The formatted unit. If the unit attribute does not exist and require is set to False, this will be an
                empty string. If the unit attribute exists and is not None or an empty string, the function will return
                the unit number, possibly prefixed with 'Unit'. If the unit attribute exists and is None or an empty
                string, the function will return an empty string.
        """
        if (
            not hasattr(self, "unit")
            and not hasattr(self, "floor")
            and not hasattr(self, "room")
        ):
            if require:
                self.unit
            else:
                return ""
        if hasattr(self, "unit") and self.unit is not None and self.unit != "":
            unit_lower = str(self.unit).lower()
            # Sometimes people neglect to add a word before the unit number,
            # use some heuristics to decide when it's necessary to add one.
            if not bare and (
                unit_lower.isnumeric()
                or (
                    not " " in self.unit
                    and not any(
                        x in unit_lower
                        for x in [
                            "apt",
                            "unit",
                            "suite",
                            "bldg",
                            "fl",
                            "apartment",
                            "building",
                            "floor",
                            "ste",
                        ]
                    )
                )
            ):
                return word("Unit", language=language) + " " + str(self.unit)
            else:
                return str(self.unit)
        if hasattr(self, "floor") and self.floor != "" and self.floor is not None:
            return word("Floor", language=language) + " " + str(self.floor)
        if hasattr(self, "room") and self.room != "" and self.room is not None:
            return word("Room", language=language) + " " + str(self.room)
        return ""

    def block(
        self,
        language=None,
        international=False,
        show_country=None,
        bare=False,
        long_state=False,
    ):
        """Returns the address formatted as a block, as in a mailing."""
        if this_thread.evaluation_context == "docx":
            line_breaker = '</w:t><w:br/><w:t xml:space="preserve">'
        else:
            line_breaker = " [NEWLINE] "

        if (
            hasattr(self, "has_no_address")
            and self.has_no_address
            and hasattr(self, "has_no_address_explanation")
        ):
            return (
                self.has_no_address_explanation
                + line_breaker
                + self.city
                + line_breaker
                + self.state
            )
        if international:
            i18n_address = {}
            if (
                (not hasattr(self, "address"))
                and hasattr(self, "street_number")
                and hasattr(self, "street")
            ):
                i18n_address["street_address"] = (
                    str(self.street_number) + " " + str(self.street)
                )
            else:
                i18n_address["street_address"] = str(self.address)
            the_unit = self.formatted_unit(language=language, bare=bare)
            if the_unit != "":
                i18n_address["street_address"] += "\n" + the_unit
            if hasattr(self, "sublocality_level_1") and self.sublocality_level_1:
                i18n_address["city_area"] = str(self.sublocality_level_1)
            i18n_address["city"] = str(self.city)
            if hasattr(self, "state") and self.state:
                i18n_address["country_area"] = str(self.state)
            if hasattr(self, "zip") and self.zip:
                i18n_address["postal_code"] = str(self.zip)
            elif hasattr(self, "postal_code") and self.postal_code:
                i18n_address["postal_code"] = str(self.postal_code)
            i18n_address["country_code"] = self._get_country()
            return i18n_address.format_address(i18n_address).replace("\n", line_breaker)
        output = ""
        if self.city_only is False:
            if (
                (not hasattr(self, "address"))
                and hasattr(self, "street_number")
                and hasattr(self, "street")
            ):
                output += (
                    str(self.street_number) + " " + str(self.street) + line_breaker
                )
            else:
                output += str(self.address) + line_breaker
            the_unit = self.formatted_unit(language=language)
            if the_unit != "":
                output += the_unit + line_breaker
        if hasattr(self, "sublocality_level_1") and self.sublocality_level_1:
            output += str(self.sublocality_level_1) + line_breaker
        output += str(self.city)
        if hasattr(self, "state") and self.state:
            if long_state:
                output += ", " + str(self.state_name())
            else:
                output += ", " + str(self.state)
        if hasattr(self, "zip") and self.zip:
            output += " " + str(self.zip)
        elif hasattr(self, "postal_code") and self.postal_code:
            output += " " + str(self.postal_code)
        if (
            show_country is None
            and hasattr(self, "country")
            and self.country
            and get_country() != self.country
        ):
            show_country = True
        if show_country:
            output += line_breaker + country_name(self._get_country())
        return output

    def line_one(self, language=None, bare=False):
        """Returns the first line of the address, including the unit
        number if there is one."""
        if (
            hasattr(self, "has_no_address")
            and self.has_no_address
            and hasattr(self, "has_no_address_explanation")
        ):
            return self.has_no_address_explanation
        if self.city_only:
            return ""
        if (
            (not hasattr(self, "address"))
            and hasattr(self, "street_number")
            and hasattr(self, "street")
        ):
            output = str(self.street_number) + " " + str(self.street)
        else:
            output = str(self.address)
        the_unit = self.formatted_unit(language=language, bare=bare)
        if the_unit != "":
            output += ", " + the_unit
        return output

    def line_two(self, language=None, long_state=False):
        """Returns the second line of the address, including the city,
        state and zip code."""
        output = ""
        # if hasattr(self, 'sublocality') and self.sublocality:
        #    output += str(self.sublocality) + ", "
        if hasattr(self, "sublocality_level_1") and self.sublocality_level_1:
            output += str(self.sublocality_level_1) + ", "
        output += str(self.city)
        if hasattr(self, "state") and self.state:
            if long_state:
                output += ", " + str(self.state_name())
            else:
                output += ", " + str(self.state)
        if hasattr(self, "zip") and self.zip:
            output += " " + str(self.zip)
        elif hasattr(self, "postal_code") and self.postal_code:
            output += " " + str(self.postal_code)
        return output

    def on_one_line(
        self,
        include_unit=True,
        omit_default_country=True,
        language=None,
        show_country=None,
        bare=False,
        long_state=False,
    ):
        """Returns a one-line address.  Primarily used internally for geocoding."""
        if (
            hasattr(self, "has_no_address")
            and self.has_no_address
            and hasattr(self, "has_no_address_explanation")
        ):
            return f"{self.has_no_address_explanation}, {self.city} {self.state}"
        output = ""
        if self.city_only is False:
            if (
                (not hasattr(self, "address"))
                and hasattr(self, "street_number")
                and hasattr(self, "street")
            ):
                output += str(self.street_number) + " " + str(self.street)
            else:
                output += str(self.address)
            if include_unit:
                the_unit = self.formatted_unit(language=language, bare=bare)
                if the_unit != "":
                    output += ", " + the_unit
            if output != "":
                output += ", "
        # if hasattr(self, 'sublocality') and self.sublocality:
        #    output += str(self.sublocality) + ", "
        if hasattr(self, "sublocality_level_1") and self.sublocality_level_1:
            if not (
                hasattr(self, "street_number")
                and self.street_number == self.sublocality_level_1
            ):
                output += str(self.sublocality_level_1) + ", "
        output += str(self.city)
        if hasattr(self, "state") and self.state:
            if long_state:
                output += ", " + str(self.state_name())
            else:
                output += ", " + str(self.state)
        if hasattr(self, "zip") and self.zip:
            output += " " + str(self.zip)
        elif hasattr(self, "postal_code") and self.postal_code:
            output += " " + str(self.postal_code)
        if (
            show_country is None
            and hasattr(self, "country")
            and self.country
            and ((not omit_default_country) or get_country() != self.country)
        ):
            show_country = True
        if show_country:
            output += ", " + country_name(self._get_country())
        return output

    def normalized_address(self) -> Union[Address, "ALAddress"]:
        """
        Try geocoding the address, and if it succeeds, return the "long" normalized version of
        the address. All methods are still available, such as my_address.normalized_address().block(), etc.,
        but note that this will be a standard Address object, not an ALAddress object.

        If geocoding fails, return the version of the address as entered by the user instead.
        """
        try:
            self.geocode()
        except:
            pass
        if self.was_geocoded_successfully() and hasattr(self, "norm_long"):
            return self.norm_long
        return self

    def state_name(self, country_code=None):
        """
        Return the full state name associated with the Address object's state abbreviation.

        If provided, the `country_code` parameter will override the country attribute of the
        Address object. If omitted, it will use in order:

        1. The country code associated with the Address object, and then
        2. The country set in the global config for the server

        `country_code` should be an ISO-3166-1 alpha-2 code
        (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements)
        """
        if country_code:
            return state_name(self.state, country_code=country_code)
        # Do a quick check for a valid ISO country code (alpha-2 only at this time)
        if hasattr(self, "country") and self.country and len(self.country) == 2:
            try:
                return state_name(self.state, country_code=self.country)
            except:
                pass
        try:
            return state_name(
                self.state
            )  # Docassemble falls back to the default set in global config
        except:
            return self.state


class ALAddressList(DAList):
    """Store a list of Address objects"""

    def init(self, *pargs, **kwargs):
        super(ALAddressList, self).init(*pargs, **kwargs)
        self.object_type = ALAddress

    def __str__(self):
        return comma_and_list([item.on_one_line() for item in self])


class ALNameList(DAList):
    """Store a list of IndividualNames"""

    def init(self, *pargs, **kwargs):
        super().init(*pargs, **kwargs)
        self.object_type = IndividualName

    def __str__(self):
        return comma_list(self)


class ALPeopleList(DAList):
    """Used to represent a list of people. E.g., defendants, plaintiffs, children"""

    def init(self, *pargs, **kwargs):
        super(ALPeopleList, self).init(*pargs, **kwargs)
        self.object_type = ALIndividual

    def names_and_addresses_on_one_line(
        self, comma_string: str = "; ", bare=False
    ) -> str:
        """Returns the name of each person followed by their address, separated by a semicolon"""
        return comma_and_list(
            [
                str(person) + ", " + person.address.on_one_line(bare=bare)
                for person in self
            ],
            comma_string=comma_string,
        )

    def familiar(self) -> str:
        return comma_and_list([person.name.familiar() for person in self])

    def familiar_or(self) -> str:
        return comma_and_list(
            [person.name.familiar() for person in self], and_string=word("or")
        )

    def short_list(self, limit: int, truncate_string: str = ", et. al."):
        """Return a subset of the list, as as string with a comma separating items, followed by 'et. al.' if the list exceeds the provided limit.
        Otherwise just return the items in the list.
        """
        if len(self) > limit:
            return comma_and_list(self[:limit]) + truncate_string
        else:
            return comma_and_list(self)

    def full_names(self, comma_string=", ", and_string=word("and")):
        """
        Return a formatted list of names in the PeopleList, without shortening middle name to an initial.
        Optional parameters `comma_string` and `and_string` will be passed to `comma_and_list` and allow
        you to change the list separator and the word before the final list item, respectively.
        """
        return comma_and_list(
            [person.name.full(middle="full") for person in self],
            comma_string=comma_string,
            and_string=and_string,
        )


class ALIndividual(Individual):
    """Used to represent an Individual on the assembly line project.
    Two custom attributes are objects and so we need to initialize: `previous_addresses`
    and `other_addresses`
    """

    previous_addresses: ALAddressList
    other_addresses: ALAddressList
    mailing_address: ALAddress
    service_address: ALAddress
    previous_names: ALNameList
    aliases: ALNameList
    preferred_name: IndividualName

    def init(self, *pargs, **kwargs):
        super(ALIndividual, self).init(*pargs, **kwargs)
        # Initialize the attributes that are themselves objects. Requirement to work with Docassemble
        # See: https://docassemble.org/docs/objects.html#ownclassattributes

        # NOTE: this stops you from passing the address to the constructor
        self.reInitializeAttribute("address", ALAddress)

        if not hasattr(self, "previous_addresses"):
            self.initializeAttribute("previous_addresses", ALAddressList)
        if not hasattr(self, "other_addresses"):
            self.initializeAttribute("other_addresses", ALAddressList)
        if not hasattr(self, "mailing_address"):
            self.initializeAttribute("mailing_address", ALAddress)
        if not hasattr(self, "service_address"):
            self.initializeAttribute("service_address", ALAddress)
        if not hasattr(self, "previous_names"):
            self.initializeAttribute("previous_names", ALNameList)
        if not hasattr(self, "aliases"):
            self.initializeAttribute("aliases", ALNameList)
        if not hasattr(self, "preferred_name"):
            self.initializeAttribute("preferred_name", IndividualName)

    def signature_if_final(self, i: str) -> Union[DAFile, str]:
        if i == "final":
            return self.signature
        else:
            return ""

    def phone_numbers(self, country=None) -> str:
        nums = []
        if hasattr(self, "mobile_number") and self.mobile_number:
            try:
                nums.append(
                    {
                        phone_number_formatted(
                            self.mobile_number, country=country
                        ): "cell"
                    }
                )
            except:
                nums.append({self.mobile_number: "cell"})
        if hasattr(self, "phone_number") and self.phone_number:
            try:
                nums.append(
                    {
                        phone_number_formatted(
                            self.phone_number, country=country
                        ): "other"
                    }
                )
            except:
                nums.append({self.phone_number: "other"})
        if len(nums) > 1:
            return comma_list(
                [
                    list(num.keys())[0] + " (" + list(num.values())[0] + ")"
                    for num in nums
                ]
            )
        elif len(nums):
            return list(nums[0].keys())[0]
        else:
            return ""

    def contact_methods(self) -> str:
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
        if hasattr(self, "email") and self.email:
            methods.append({self.email: word("by email at ")})
        if hasattr(self, "other_contact_method") and self.other_contact_method:
            methods.append({self.other_contact_method: "by "})

        return comma_and_list(
            [
                list(method.values())[0] + list(method.keys())[0]
                for method in methods
                if len(method)
            ],
            and_string=word("or"),
        )

    def merge_letters(self, new_letters: str):
        # TODO: move to 209A package
        """If the Individual has a child_letters attribute, add the new letters to the existing list"""
        if hasattr(self, "child_letters"):
            self.child_letters: str = filter_letters([new_letters, self.child_letters])
        else:
            self.child_letters = filter_letters(new_letters)

    def formatted_age(self) -> str:
        dd = date_difference(self.birthdate)
        if dd.years >= 2:
            return "%d years" % (int(dd.years),)
        if dd.weeks > 12:
            return "%d months" % (int(dd.years * 12.0),)
        if dd.weeks > 2:
            return "%d weeks" % (int(dd.weeks),)
        return "%d days" % (int(dd.days),)

    def normalized_address(self) -> Union[Address, ALAddress]:
        return self.address.normalized_address()

    # This design helps us translate the prompts for common fields just once
    def name_fields(
        self,
        person_or_business: str = "person",
        show_suffix: bool = True,
        show_if: Union[str, Dict[str, str], None] = None,
    ) -> List[Dict[str, str]]:
        """
        Return suitable field prompts for a name. If `person_or_business` is None, adds the
        proper "show ifs" and uses both the parts and the single entry
        """
        if person_or_business == "person":
            fields = [
                {
                    "label": str(self.first_name_label),
                    "field": self.attr_name("name.first"),
                },
                {
                    "label": str(self.middle_name_label),
                    "field": self.attr_name("name.middle"),
                    "required": False,
                },
                {
                    "label": str(self.last_name_label),
                    "field": self.attr_name("name.last"),
                },
            ]
            if show_suffix:
                fields.append(
                    {
                        "label": str(self.suffix_label),
                        "field": self.attr_name("name.suffix"),
                        "choices": name_suffix(),
                        "required": False,
                    }
                )
            if show_if:
                for field in fields:
                    field["show if"] = show_if
            return fields
        elif person_or_business == "business":
            # Note: we don't make use of the name.text field for simplicity
            # TODO: this could be reconsidered`, but name.text tends to lead to developer error
            fields = [
                {
                    "label": str(self.business_name_label),
                    "field": self.attr_name("name.first"),
                }
            ]
            if show_if:
                fields[0]["show if"] = show_if
            return fields
        else:
            # Note: the labels are template block objects: if they are keys,
            # they should be converted to strings first
            show_if_indiv = {
                "variable": self.attr_name("person_type"),
                "is": "ALIndividual",
            }
            show_if_business = {
                "variable": self.attr_name("person_type"),
                "is": "business",
            }
            fields = [
                {
                    "label": str(self.person_type_label),
                    "field": self.attr_name("person_type"),
                    "choices": [
                        {str(self.individual_choice_label): "ALIndividual"},
                        {str(self.business_choice_label): "business"},
                    ],
                    "input type": "radio",
                    "required": True,
                },
                # Individual questions
                {
                    "label": str(self.first_name_label),
                    "field": self.attr_name("name.first"),
                    "show if": show_if_indiv,
                },
                {
                    "label": str(self.middle_name_label),
                    "field": self.attr_name("name.middle"),
                    "required": False,
                    "show if": show_if_indiv,
                },
                {
                    "label": str(self.last_name_label),
                    "field": self.attr_name("name.last"),
                    "show if": show_if_indiv,
                },
            ]
            if show_if:
                fields[0]["show if"] = show_if

            if show_suffix:
                fields.append(
                    {
                        "label": str(self.suffix_label),
                        "field": self.attr_name("name.suffix"),
                        "choices": name_suffix(),
                        "required": False,
                        "show if": show_if_indiv,
                    }
                )
            fields.append(
                # Business names
                {
                    "label": str(self.business_name_label),
                    "field": self.attr_name("name.first"),
                    "show if": show_if_business,
                }
            )
            return fields

    def address_fields(
        self,
        country_code: str = "US",
        default_state: Optional[str] = None,
        show_country: bool = False,
        show_county: bool = False,
        show_if: Union[str, Dict[str, str], None] = None,
        allow_no_address: bool = False,
    ) -> List[Dict[str, str]]:
        """
        Return field prompts for address.
        """
        # TODO make this more flexible to work w/ homeless individuals and
        # international addresses
        return self.address.address_fields(
            country_code=country_code,
            default_state=default_state,
            show_country=show_country,
            show_county=show_county,
            show_if=show_if,
            allow_no_address=allow_no_address,
        )

    def gender_fields(
        self, show_help=False, show_if: Union[str, Dict[str, str], None] = None
    ):
        """
        Return a standard gender input with "self described" option.
        """
        choices = [
            {str(self.gender_female_label): "female"},
            {str(self.gender_male_label): "male"},
            {str(self.gender_nonbinary_label): "nonbinary"},
            {str(self.gender_prefer_not_to_say_label): "prefer-not-to-say"},
            {str(self.gender_prefer_self_described_label): "self-described"},
            {str(self.gender_unknown_label): "unknown"},
        ]
        self_described_input = {
            "label": str(self.gender_self_described_label),
            "field": self.attr_name("gender"),
            "show if": {"variable": self.attr_name("gender"), "is": "self-described"},
        }
        fields = [
            {
                "label": str(self.gender_label),
                "field": self.attr_name("gender"),
                "choices": choices,
            },
            self_described_input,
        ]

        if show_help:
            fields[0]["help"] = str(self.gender_help_text)
        if show_if:
            fields[0]["show if"] = show_if

        return fields

    def pronoun_fields(
        self,
        show_help=False,
        show_if: Union[str, Dict[str, str], None] = None,
        required: bool = False,
        shuffle: bool = False,
        show_unknown: Optional[Union[Literal["guess"], bool]] = "guess",
    ):
        """
        Return a standard multiple choice checkbox pronouns input with a "self described" option.

        Options are shuffled by default.
        """
        shuffled_choices = [
            {str(self.pronoun_she_label): "she/her/hers"},
            {str(self.pronoun_he_label): "he/him/his"},
            {str(self.pronoun_they_label): "they/them/theirs"},
            {str(self.pronoun_zir_label): "ze/zir/zirs"},
        ]
        if shuffle:
            random.shuffle(shuffled_choices)
        final_choices = [
            {str(self.pronoun_prefer_self_described_label): "self-described"},
        ]
        if show_unknown == True or (
            show_unknown == "guess" and self.instanceName != "users[0]"
        ):
            final_choices.append({str(self.pronoun_unknown_label): "unknown"})
        self_described_input = {
            "label": str(self.pronoun_self_described_label),
            "field": self.attr_name("pronouns_self_described"),
            "show if": self.attr_name("pronouns['self-described']"),
        }
        fields = [
            {
                "label": str(self.pronouns_label),
                "field": self.attr_name("pronouns"),
                "datatype": "checkboxes",
                "choices": shuffled_choices + final_choices,
                "none of the above": str(self.pronoun_prefer_not_to_say_label),
                "required": required,
            },
            self_described_input,
        ]

        if show_help:
            fields[0]["help"] = str(self.pronouns_help_text)
        if show_if:
            fields[0]["show if"] = show_if

        return fields

    def get_pronouns(self) -> set:
        """
        Return a set of the individual's pronouns. If the individual's
        pronouns include self-described pronouns, display those in place of the word "self-described".

        The set can be displayed in the interview or in a template. For example:

        Pronouns: {{ users[0].get_pronouns() | comma_and_list }}
        """
        if self.pronouns.all_false():
            return {str(self.pronoun_prefer_not_to_say_label)}
        pronouns = set(self.pronouns.true_values()) - {"self-described"}
        if self.pronouns.get("self-described"):
            pronouns = pronouns.union(self.pronouns_self_described.splitlines())
        return pronouns

    def language_fields(
        self,
        choices: Optional[List[Dict[str, str]]] = None,
        style: str = "radio",
        show_if: Union[str, Dict[str, str], None] = None,
    ):
        """Return a standard language picker with an "other" input. Language should be specified as ISO 639-2 or -3 codes so it is compatible with the language_name() function."""
        if not choices:
            choices = [
                {"English": "en"},
                {"Spanish": "es"},
                {"Other": "other"},
            ]
        other = {
            "label": str(self.language_other_label),
            "field": self.attr_name("language_other"),
            "show if": {"variable": self.attr_name("language"), "is": "other"},
        }
        fields = [
            {
                "label": str(self.language_label),
                "field": self.attr_name("language"),
                "choices": choices,
            },
            other,
        ]
        if style == "radio":
            fields[0]["input type"] = "radio"
        if show_if:
            fields[0]["show if"] = show_if
        return fields

    def language_name(self):
        """Return the human-readable version of the individual's language, handling the "other" option."""
        if self.language == "other":
            return self.language_other
        else:
            return language_name(self.language)

    @property
    def gender_male(self):
        """Provide True/False for 'male' gender to assist with checkbox filling
        in PDFs with "skip undefined" turned on."""
        return self.gender.lower() == "male"

    @property
    def gender_female(self):
        """Provide True/False for 'female' gender to assist with checkbox filling
        in PDFs with "skip undefined" turned on."""
        return self.gender.lower() == "female"

    @property
    def gender_other(self):
        """Provide True/False for 'other' gender to assist with checkbox filling
        in PDFs with "skip undefined" turned on for forms without more inclusive options.
        """
        return (self.gender != "male") and (self.gender != "female")

    @property
    def gender_nonbinary(self):
        """Provide True/False for 'nonbinary' gender to assist with checkbox filling
        in PDFs with "skip undefined" turned on."""
        return self.gender.lower() == "nonbinary"

    @property
    def gender_unknown(self):
        """Provide True/False for 'unknown' gender to assist with checkbox filling
        in PDFs with "skip undefined" turned on."""
        return self.gender.lower() == "unknown"

    @property
    def gender_undisclosed(self):
        """Provide True/False for 'prefer-not-to-say' gender to assist with checkbox filling
        in PDFs with "skip undefined" turned on."""
        return self.gender.lower() == "prefer-not-to-say"

    @property
    def gender_self_described(self):
        """Provide True/False for 'self-described' gender to assist with checkbox filling
        in PDFs with "skip undefined" turned on."""
        return not (
            self.gender
            in ["prefer-not-to-say", "male", "female", "unknown", "nonbinary"]
        )

    def contact_fields(self):
        """
        Return field prompts for other contact info
        """
        pass

    @property
    def initials(self):
        """Return the individual's initials, like QKS for Quinten K Steenhuis"""
        return f"{self.name.first[:1]}{self.name.middle[:1] if hasattr(self.name,'middle') else ''}{self.name.last[:1] if hasattr(self.name, 'last') else ''}"

    def address_block(
        self, language=None, international=False, show_country=False, bare=False
    ):
        """Returns the person name address as a block, for use in mailings."""
        if this_thread.evaluation_context == "docx":
            return (
                self.name.full()
                + '</w:t><w:br/><w:t xml:space="preserve">'
                + self.address.block(
                    language=language,
                    international=international,
                    show_country=show_country,
                )
            )
        return (
            "[FLUSHLEFT] "
            + self.name.full()
            + " [NEWLINE] "
            + self.address.block(
                language=language,
                international=international,
                show_country=show_country,
                bare=bare,
            )
        )

    def pronoun(self, **kwargs):
        """Returns an objective pronoun as appropriate, based on attributes.

        The pronoun could be "you," "her," "him," "it," or "them". It depends
        on the `gender` and `person_type` attributes and whether the individual
        is the current user.

        If the user selected specific pronouns, they take priority over
        gender (only if they chose a pronoun from the list)

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            str: The appropriate pronoun.
        """
        if self == this_thread.global_vars.user:
            output = word("you", **kwargs)
        elif (
            hasattr(self, "pronouns")
            and isinstance(self.pronouns, DADict)
            and len(self.pronouns.true_values()) == 1
            and (
                (
                    self.pronouns.true_values()[0]
                    in ["she/her/hers", "he/him/his", "they/them/theirs", "ze/zir/zirs"]
                )
                or (
                    self.pronouns.get("self-described")
                    and has_parsable_pronouns(self.pronouns_self_described)
                )
            )
        ):
            if self.pronouns["she/her/hers"]:
                output = word("her", **kwargs)
            elif self.pronouns["he/him/his"]:
                output = word("him", **kwargs)
            elif self.pronouns["they/them/theirs"]:
                output = word("them", **kwargs)
            elif self.pronouns["ze/zir/zirs"]:
                output = word("zir", **kwargs)
            elif self.pronouns.get("self-described"):
                output = parse_custom_pronouns(self.pronouns_self_described)["o"]
        elif hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            output = word("it", **kwargs)
        elif self.gender.lower() == "female":
            output = word("her", **kwargs)
        elif self.gender.lower() == "male":
            output = word("him", **kwargs)
        else:
            output = word("them", **kwargs)
        if "capitalize" in kwargs and kwargs["capitalize"]:
            return capitalize(output)
        return output

    def pronoun_objective(self, **kwargs):
        """Returns the same pronoun as the `pronoun()` method.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            str: The appropriate objective pronoun.
        """
        return self.pronoun(**kwargs)

    def pronoun_possessive(self, target, **kwargs):
        """Returns a possessive pronoun and a target word, based on attributes.

        Given a target word, the function returns "{pronoun} {target}". The pronoun could be
        "her," "his," "its," or "their". It depends on the `gender` and `person_type` attributes
        and whether the individual is the current user.

        Args:
            target (str): The target word to follow the pronoun.
            **kwargs: Additional keyword arguments.

        Returns:
            str: The appropriate possessive phrase.
        """
        if self == this_thread.global_vars.user and (
            "thirdperson" not in kwargs or not kwargs["thirdperson"]
        ):
            output = your(target, **kwargs)
        elif (
            hasattr(self, "pronouns")
            and isinstance(self.pronouns, DADict)
            and len(self.pronouns.true_values()) == 1
            and (
                (
                    self.pronouns.true_values()[0]
                    in ["she/her/hers", "he/him/his", "they/them/theirs", "ze/zir/zirs"]
                )
                or (
                    self.pronouns.get("self-described")
                    and has_parsable_pronouns(self.pronouns_self_described)
                )
            )
        ):
            if self.pronouns["she/her/hers"]:
                output = her(target, **kwargs)
            elif self.pronouns["he/him/his"]:
                output = his(target, **kwargs)
            elif self.pronouns["they/them/theirs"]:
                output = their(target, **kwargs)
            elif self.pronouns["ze/zir/zirs"]:
                output = word("zir", **kwargs) + " " + target
            elif self.pronouns.get("self-described"):
                output = (
                    parse_custom_pronouns(self.pronouns_self_described)["p"]
                    + " "
                    + target
                )
        elif hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            output = its(target, **kwargs)
        elif self.gender.lower() == "female":
            output = her(target, **kwargs)
        elif self.gender.lower() == "male":
            output = his(target, **kwargs)
        else:
            output = their(target, **kwargs)
        if "capitalize" in kwargs and kwargs["capitalize"]:
            return capitalize(output)
        return output

    def pronoun_subjective(self, **kwargs):
        """Returns a subjective pronoun, based on attributes.

        The pronoun could be "you," "she," "he," "it," or "they". It depends
        on the `gender` and `person_type` attributes and whether the individual
        is the current user.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            str: The appropriate subjective pronoun.
        """
        if self == this_thread.global_vars.user and (
            "thirdperson" not in kwargs or not kwargs["thirdperson"]
        ):
            output = word("you", **kwargs)
        elif (
            hasattr(self, "pronouns")
            and isinstance(self.pronouns, DADict)
            and len(self.pronouns.true_values()) == 1
            and (
                (
                    self.pronouns.true_values()[0]
                    in ["she/her/hers", "he/him/his", "they/them/theirs", "ze/zir/zirs"]
                )
                or (
                    self.pronouns.get("self-described")
                    and has_parsable_pronouns(self.pronouns_self_described)
                )
            )
        ):
            if self.pronouns["she/her/hers"]:
                output = word("she", **kwargs)
            elif self.pronouns["he/him/his"]:
                output = word("he", **kwargs)
            elif self.pronouns["they/them/theirs"]:
                output = word("they", **kwargs)
            elif self.pronouns["ze/zir/zirs"]:
                output = word("ze", **kwargs)
            elif self.pronouns.get("self-described"):
                output = parse_custom_pronouns(self.pronouns_self_described)["s"]
        elif hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            output = word("it", **kwargs)
        elif self.gender.lower() == "female":
            output = word("she", **kwargs)
        elif self.gender.lower() == "male":
            output = word("he", **kwargs)
        else:
            output = word("they", **kwargs)
        if "capitalize" in kwargs and kwargs["capitalize"]:
            return capitalize(output)
        return output


def section_links(nav) -> List[str]:
    """Returns a list of clickable navigation links without animation."""
    sections = nav.get_sections()
    section_link = []
    for section in sections:
        for key in section:
            section_link.append("[" + section[key] + "](" + url_action(key) + ")")

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
    return not (
        get_config("debug")
        or "dev" in get_config("url root")
        or "test" in get_config("url root")
        or "localhost" in get_config("url root")
    )


# This one is only used for 209A--should move there along with the combined_letters() method
def filter_letters(letter_strings: Union[List[str], str]) -> str:
    """Used to take a list of letters like ["A","ABC","AB"] and filter out any duplicate letters."""
    # There is probably a cute one liner, but this is easy to follow and
    # probably same speed
    unique_letters = set()
    if isinstance(letter_strings, str):
        letter_strings = [letter_strings]
    for string in letter_strings:
        if string:  # Catch possible None values
            for letter in string:
                unique_letters.add(letter)
    try:
        retval = "".join(sorted(unique_letters))
    except:
        retval = ""
    return retval


# Note: removed "combined_locations" because it is too tightly coupled to MACourts.py right now


def fa_icon(
    icon: str, color: str = "primary", color_css: Optional[str] = None, size: str = "sm"
):
    """
    Return HTML for a font-awesome icon of the specified size and color. You can reference
    a CSS variable (such as Bootstrap theme color) or a true CSS color reference, such as 'blue' or
    '#DDDDDD'. Defaults to Bootstrap theme color "primary".
    """
    if not color and not color_css:
        return ":" + icon + ":"  # Default to letting Docassemble handle it
    elif color_css:
        return (
            '<i class="fa fa-'
            + icon
            + " fa-"
            + size
            + '" style="color:'
            + color_css
            + ';"></i>'
        )
    else:
        return (
            '<i class="fa fa-'
            + icon
            + " fa-"
            + size
            + '" style="color:var(--'
            + color
            + ');"></i>'
        )


def is_phone_or_email(text: str) -> bool:
    """
    Returns True if the string is either a valid phone number or a valid email address.
    Email validation is extremely minimal--just checks for an @ sign between two non-zero length
    strings.
    """
    if re.match("\S+@\S+", text) or phone_number_is_valid(text):
        return True
    else:
        validation_error("Enter a valid phone number or email address")
        assert False, "unreachable"


def github_modified_date(
    github_user: str, github_repo_name: str, auth=None
) -> Union[DADateTime, None]:
    """
    Returns the date that the given GitHub repository was modified or None if API call fails.

    Will check for the presence of credentials in the configuration labeled "github issues"
    in this format:

    github issues:
      username: YOUR_GITHUB_USERNAME
      token: YOUR_GITHUB_PRIVATE_TOKEN

    If those credentials aren't found, it will then search for credentials in this format (deprecated):

    github readonly:
      username: YOUR_GITHUB_USERNAME
      password: YOUR_GITHUB_PRIVATE_TOKEN
      type: basic

    If no valid auth information is in the configuration, it will fall back to anonymous authentication.
    The GitHub API is rate-limited to 60 anonymous API queries/hour.
    """
    if not auth:
        issue_config = get_config("github issues")
        if issue_config:
            auth = {
                "username": issue_config.get("username"),
                "password": issue_config.get("token"),
                "type": "basic",
            }
        else:
            auth = get_config("github readonly")
    github_readonly_web = DAWeb(base_url="https://api.github.com")
    res = github_readonly_web.get(
        "repos/" + github_user + "/" + github_repo_name,
        auth=auth,
    )
    if res and res.get("pushed_at"):
        return as_datetime(res.get("pushed_at"))
    else:
        return None


# TODO(qs): remove if https://github.com/jhpyle/docassemble/pull/520 is merged
def language_name(language_code: str) -> str:
    """Given a 2 digit language code abbreviation, returns the full
    name of the language. The language name will be passed through the `word()`
    function."""
    ensure_definition(language_code)
    try:
        if len(language_code) == 2:
            return word(pycountry.languages.get(alpha_2=language_code).name)
        else:
            return word(pycountry.languages.get(alpha_3=language_code).name)
    except:
        return language_code


def safe_states_list(country_code: str) -> List[Dict[str, str]]:
    """Wrapper around states_list that doesn't error if passed
    an invalid country_code (e.g., a country name spelled out)"""
    try:
        return states_list(country_code=country_code)
    except:
        return states_list()


def has_parsable_pronouns(pronouns: str) -> bool:
    """
    Returns True if the pronouns string can be parsed into a dictionary of pronouns.

    Args:
        pronouns: a string of pronouns in the format "objective/subjective/possessive"

    Returns:
        True if the pronouns string can be parsed into a dictionary of pronouns, False otherwise
    """
    try:
        parse_custom_pronouns(pronouns)
        return True
    except:
        return False


def parse_custom_pronouns(pronouns: str) -> Dict[str, str]:
    """
    Parses a custom pronoun string into a dictionary of pronouns.

    Args:
        pronouns: a string of pronouns in the format "objective/subjective/possessive"

    Returns:
        a dictionary of pronouns in the format {"o": objective, "s": subjective, "p": possessive}
    """
    # test for presence of either 2 or 3 /'s
    if not (2 <= pronouns.count("/") <= 3):
        raise Exception("Pronouns must contain either 2 or 3 slashes.")

    pronoun_list = pronouns.split("/")
    # entry 1 is objective, entry 2 is subjective, entry 3 is possessive, entry 4 is possessive pronoun (unused)
    return {
        "o": pronoun_list[0].lower(),
        "s": pronoun_list[1].lower(),
        "p": pronoun_list[2].lower(),
    }

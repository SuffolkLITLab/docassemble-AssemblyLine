from copy import deepcopy
from typing import Dict, List, Literal, Union, Optional, Any
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
    showifdef,
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
    "get_visible_al_nav_items",
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
    "is_sms_enabled",
]

##########################################################
# Base classes


def safe_subdivision_type(country_code: str) -> Optional[str]:
    """
    Returns the subdivision type for the country with the given country code.
    If no subdivision type is found, returns None.

    Args:
        country_code (str): The ISO-3166-1 alpha-2 code for the country.

    Returns:
        Optional[str]: The subdivision type for the country with the given country code.
    """
    try:
        return subdivision_type(country_code)
    except:
        return None


class ALAddress(Address):
    """
    This class is used to store addresses. The ALAddress class extends the Address
    class with the `address_fields()` method and "smarter"
    handling of the unit attribute when printing a formatted address.

    Attributes:
        address (str): The street where the person lives.
        unit (str): The unit number where the person lives.
        city (str): The city where the person lives.
        state (str): The state where the person lives.
        zip (str): The zip code where the person lives.
        country (str): The country where the person lives.
        impounded (Optional[bool]): Whether the address is impounded.
    """

    def address_fields(
        self,
        country_code: Optional[str] = None,
        default_state: Optional[str] = None,
        show_country: bool = False,
        show_county: bool = False,
        show_if: Union[str, Dict[str, str], None] = None,
        allow_no_address: bool = False,
        ask_if_impounded: Optional[bool] = False,
        maxlengths: Optional[Dict[str, int]] = None,
        required: Optional[Dict[str, bool]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return a YAML structure representing the list of fields for the object's address.

        Optionally, allow the user to specify they do not have an address. When using
        `allow_no_address=True`, ensure to trigger the question with `users[0].address.has_no_address`
        rather than `users[0].address.address`. If `show_if` is used, it will not be applied when
        `allow_no_address` is also used. Ensure `country_code` adheres to ISO-3166-1 alpha-2 code standard.

        NOTE: This function is stateful under specific conditions. Refer to the conditions mentioned below.

        Args:
            country_code (Optional[str]): ISO-3166-1 alpha-2 code of the country. Defaults to None.
            default_state (Optional[str]): Default state to set. Defaults to None.
            show_country (bool): Whether to display the country field. Defaults to False.
            show_county (bool): Whether to display the county field. Defaults to False.
            show_if (Union[str, Dict[str, str], None]): Condition to display each field. Defaults to None.
            allow_no_address (bool): Allow users to specify they don't have an address. Defaults to False.
            ask_if_impounded (Optional[bool]): Whether to ask if the address is impounded. Defaults to False.
            maxlengths (Optional[Dict[str, int]]): A dictionary of field names and their maximum lengths. Defaults to None.
            required (Dict[str, bool], optional): A dictionary of field names and if they should be required. Default is None (everything but unit and zip is required)

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing address fields.

        Notes:
            - The function will set the `country` attribute of the Address to `country_code` under these
            circumstances:
                1. The `country_code` parameter is used.
                2. The `show_country` parameter is not used.
                3. `country_code` differs from the value returned by `get_country()`.

            - Link to ISO-3166-1 alpha-2 codes:
            [Officially assigned code elements](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements).
        """
        # make sure the state name still returns a meaningful value if the interview country
        # differs from the server's country.
        if country_code and country_code != get_country() and not show_country:
            self.country = country_code
        # Priority order for country: already answered country, passed in country_code, then get_country
        prev_selected_country = showifdef(self.attr_name("country"), None, prior=True)
        if prev_selected_country:
            country_code = prev_selected_country
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

        if country_code and not show_country:
            fields.append(
                {
                    "label": str(self.state_label),
                    "field": self.attr_name("state"),
                    "code": "states_list(country_code='{}')".format(country_code),
                    "default": default_state if default_state else "",
                }
            )
        else:  # when you are allowed to change country
            fields.append(
                {
                    "label": str(self.state_or_province_label),
                    "field": self.attr_name("state"),
                    "default": default_state if default_state else "",
                }
            )
        if country_code == "US" and not show_country:
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

        if ask_if_impounded:
            fields.append(
                {
                    "label": str(self.impounded_label),
                    "field": self.attr_name("impounded"),
                    "datatype": "yesno",
                }
            )

        if maxlengths:
            for field in fields:
                if field["field"] in maxlengths:
                    field["maxlength"] = maxlengths[field["field"]]

        if required:
            for field in fields:
                if field["field"] in required:
                    field["required"] = required[field["field"]]

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
            str:
                The formatted unit. If the unit attribute does not exist and require is set to False, this will be an
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
        language: Optional[str] = None,
        international: bool = False,
        show_country: Optional[bool] = None,
        bare: bool = False,
        long_state: bool = False,
        show_impounded: bool = False,
    ) -> str:
        """Returns a one-line formatted address, primarily for geocoding.

        Args:
            language (str, optional): Language for the address format.
            international (bool): If True, formats the address as an international address. Defaults to False.
            show_country (bool, optional): If True, includes the country in the formatted address.
                If None, decides based on the country attribute.
            bare (bool): If True, excludes certain formatting elements. Defaults to False.
            long_state (bool): If True, uses the full state name. Defaults to False.
            show_impounded (bool): If True, shows the address even if impounded. Defaults to False.

        Returns:
            str: The one-line formatted address.
        """
        if this_thread.evaluation_context == "docx":
            line_breaker = '</w:t><w:br/><w:t xml:space="preserve">'
        else:
            line_breaker = " [NEWLINE] "

        if not show_impounded and (hasattr(self, "impounded") and self.impounded):
            return str(self.impounded_output_label)
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
            return i18n_address.format_address(i18n_address).replace("\n", line_breaker)  # type: ignore
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
            current_country = (
                self.country if hasattr(self, "country") else get_country()
            )
            if current_country == "US":
                output += " " + str(self.zip).zfill(5)
            else:
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

    def line_one(
        self,
        language: Optional[str] = None,
        bare: bool = False,
        show_impounded: bool = False,
    ) -> str:
        """Returns the first line of the address, including the unit number if it exists.

        Args:
            language (str, optional): Language for the address format.
            bare (bool): If True, excludes certain formatting elements. Defaults to False.
            show_impounded (bool): If True, shows the address even if impounded. Defaults to False.

        Returns:
            str: The first line of the address.
        """
        if not show_impounded and (hasattr(self, "impounded") and self.impounded):
            return str(self.impounded_output_label)
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

    def line_two(
        self,
        language: Optional[str] = None,
        long_state: bool = False,
        show_impounded: bool = False,
    ) -> str:
        """Returns the second line of the address, including city, state, and postal code.

        Args:
            language (str, optional): Language for the address format.
            long_state (bool): If True, uses the full state name. Defaults to False.
            show_impounded (bool): If True, shows the address even if impounded. Defaults to False.

        Returns:
            str: The second line of the address.
        """
        if not show_impounded and (hasattr(self, "impounded") and self.impounded):
            return str(self.impounded_output_label)
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
            current_country = (
                self.country if hasattr(self, "country") else get_country()
            )
            if current_country == "US":
                output += " " + str(self.zip).zfill(5)
            else:
                output += " " + str(self.zip)
        elif hasattr(self, "postal_code") and self.postal_code:
            output += " " + str(self.postal_code)
        return output

    def on_one_line(
        self,
        include_unit: bool = True,
        omit_default_country: bool = True,
        language: Optional[str] = None,
        show_country: Optional[bool] = None,
        bare: bool = False,
        long_state: bool = False,
        show_impounded: bool = False,
    ) -> str:
        """Returns a one-line formatted address.

        Args:
            include_unit (bool): If True, includes the unit in the formatted address. Defaults to True.
            omit_default_country (bool): If True, doesn't show the Docassemble default country in the formatted address. Defaults to True.
            language (str, optional): Language for the address format.
            show_country (bool, optional): If True, includes the country in the formatted address.
                If None, decides based on the country attribute.
            bare (bool): If True, excludes certain formatting elements. Defaults to False.
            long_state (bool): If True, uses the full state name. Defaults to False.
            show_impounded (bool): If True, shows the address even if impounded. Defaults to False.

        Returns:
            str: The one-line formatted address.
        """
        if not show_impounded and (hasattr(self, "impounded") and self.impounded):
            return str(self.impounded_output_label)
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
            current_country = (
                self.country if hasattr(self, "country") else get_country()
            )
            if current_country == "US":
                output += " " + str(self.zip).zfill(5)
            else:
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
        """Try geocoding the address, returning the normalized version if successful.

        If geocoding is successful, the method returns the "long" normalized version
        of the address. All methods, such as `my_address.normalized_address().block()`, are
        still available on the returned object. However, note that the returned object will
        be a standard Address object, not an ALAddress object. If geocoding fails, it returns
        the version of the address as entered by the user.

        Warning: currently the normalized address will not be redacted if the address is impounded.

        Returns:
            Union[Address, "ALAddress"]:
                Normalized address if geocoding is successful, otherwise
                the original address.
        """
        try:
            self.geocode()
        except:
            pass
        if self.was_geocoded_successfully() and hasattr(self, "norm_long"):
            return self.norm_long
        return self

    def state_name(self, country_code: Optional[str] = None) -> str:
        """Returns the full state name based on the state abbreviation.

        If a `country_code` is provided, it will override the country attribute of the Address
        object. Otherwise, the method uses, in order:

        1. The country code associated with the Address object, and then
        2. The country set in the global config for the server.

        Args:
            country_code (str, optional): ISO-3166-1 alpha-2 code to override the country attribute of
                the Address object. For valid codes, refer to:
                https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements

        Returns:
            str: The full state name corresponding to the state abbreviation. If an error occurs
            or the full name cannot be determined, returns the state abbreviation.
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
    """A class to store a list of ALAddress objects.

    Extends the DAList class and specifically caters to ALAddress objects.
    It provides methods to initialize the list and get a string representation
    of the list in a formatted manner.
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super(ALAddressList, self).init(*pargs, **kwargs)
        self.object_type = ALAddress

    def __str__(self) -> str:
        """Provide a string representation of the ALAddressList.

        This method returns the addresses in the list formatted in a
        comma-separated manner using the on_one_line method of ALAddress.

        Returns:
            str: Formatted string of all addresses in the list.
        """
        return comma_and_list([item.on_one_line() for item in self])


class ALNameList(DAList):
    """A class to store a list of IndividualName objects.

    Extends the DAList class and is tailored for IndividualName objects.
    """

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super().init(*pargs, **kwargs)
        self.object_type = IndividualName

    def __str__(self) -> str:
        """Provide a string representation of the ALNameList.

        Returns:
            str: Formatted string of all names in the list.
        """
        return comma_list(self)


class ALPeopleList(DAList):
    """Class to store a list of ALIndividual objects, representing people.

    For example, defendants, plaintiffs, or children."""

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
        super(ALPeopleList, self).init(*pargs, **kwargs)
        self.object_type = ALIndividual

    def names_and_addresses_on_one_line(
        self, comma_string: str = "; ", bare=False
    ) -> str:
        """Provide names and addresses of individuals on one line.

        Args:
            comma_string (str, optional): The string to use between name-address pairs. Defaults to '; '.
            bare (bool, optional): If True, prevents appending the word "Unit" to the unit attribute. Defaults to False.

        Returns:
            str: Formatted string of names followed by addresses.
        """
        return comma_and_list(
            [
                str(person)
                + ", "
                + (
                    person.address.on_one_line(bare=bare)
                    if isinstance(person.address, ALAddress)
                    else str(person.address.on_one_line())
                )
                for person in self
            ],
            comma_string=comma_string,
        )

    def familiar(self, **kwargs) -> str:
        """Provide a list of familiar forms of names of individuals.

        Args:
            **kwargs: Keyword arguments to pass to the familiar method.
        Returns:
            str: Formatted string of familiar names.
        """
        return comma_and_list([person.familiar(**kwargs) for person in self])

    def familiar_or(self, **kwargs) -> str:
        """Provide a list of familiar forms of names of individuals separated by 'or'.

        Args:
            **kwargs: Keyword arguments to pass to the familiar method.

        Returns:
            str: Formatted string of familiar names separated by 'or'.
        """
        return comma_and_list(
            [person.familiar(**kwargs) for person in self], and_string=word("or")
        )

    def short_list(self, limit: int, truncate_string: str = ", et. al.") -> str:
        """Return a subset of the list, truncated with 'et. al.' if it exceeds a given limit.

        Args:
            limit (int): The maximum number of items to display before truncating.
            truncate_string (str, optional): The string to append when truncating. Defaults to ', et. al.'.

        Returns:
            str: Formatted string of names, truncated if needed.
        """
        if len(self) > limit:
            return comma_and_list(self[:limit]) + truncate_string
        else:
            return comma_and_list(self)

    def full_names(self, comma_string=", ", and_string=word("and")) -> str:
        """Return a formatted list of full names of individuals.

        Args:
            comma_string (str, optional): The string to use between names. Defaults to ','.
            and_string (str, optional): The string to use before the last name in the list. Defaults to 'and'.

        Returns:
            str: Formatted string of full names.
        """
        return comma_and_list(
            [
                (
                    person.name_full()
                    if isinstance(person, ALIndividual)
                    else person.name.full(middle="full")
                )
                for person in self
            ],
            comma_string=comma_string,
            and_string=and_string,
        )

    def pronoun_reflexive(self, **kwargs) -> str:
        """Returns the appropriate reflexive pronoun for the list of people, depending
        on the `person` keyword argument and the number of items in the list.

        If the list is singular, return the reflexive pronoun for the first item in the list.
        If it is plural, return the appropriate plural reflexive pronoun (e.g., "themselves")

        Args:
            **kwargs: Additional keyword arguments that are defined [upstream](https://docassemble.org/docs/objects.html#language%20methods).
                    - person (Optional[[Union[str,int]]): Whether to use a first, second, or third person pronoun. Can be one of 1/"1p", 2/"2p", or 3/"3p" (default is 3). See [upstream](https://docassemble.org/docs/objects.html#language%20methods) documentation for more information.
                    - default (Optional[str]): The default word to use if the pronoun is not defined, e.g. "the agent". If not defined, the default term is the user's name.

        Returns:
            str: The reflexive pronoun for the list.
        """
        person = str(kwargs.get("person", self.get_point_of_view()))

        if self.number_gathered() > 1:
            if person in ("1", "1p", "2", "2p"):
                if person in ("1", "1p"):
                    output = word("ourselves")
                elif person in ("2", "2p"):
                    output = word("yourselves")
            else:
                output = word("themselves")

        elif self.number_gathered() == 1:
            if isinstance(self[0], ALIndividual) and hasattr(
                self[0], "pronoun_reflexive"
            ):
                output = self[0].pronoun_reflexive(**kwargs)
            else:
                output = word("itself")
        else:
            output = word("themselves")

        if kwargs.get("capitalize"):
            return output.capitalize()
        return output


class ALIndividual(Individual):
    """Used to represent an Individual on the assembly line project.

    This class extends the Individual class and adds more tailored attributes and methods
    relevant for the assembly line project. Specifically, it has attributes for previous addresses,
    other addresses, mailing addresses, previous names, aliases, and a preferred name.

    Attributes:
        previous_addresses (ALAddressList): List of previous addresses.
        other_addresses (ALAddressList): List of other addresses.
        mailing_address (ALAddress): Current mailing address.
        service_address (ALAddress): Service address.
        previous_names (ALNameList): List of previous names.
        aliases (ALNameList): List of aliases.
        preferred_name (IndividualName): The preferred name.

    Note:
        Objects as attributes should not be passed directly to the constructor due to
        initialization requirements in the Docassemble framework. See the `init` method.
    """

    previous_addresses: ALAddressList
    other_addresses: ALAddressList
    mailing_address: ALAddress
    service_address: ALAddress
    previous_names: ALNameList
    aliases: ALNameList
    preferred_name: IndividualName

    def init(self, *pargs, **kwargs) -> None:
        """Standard DAObject init method.

        Args:
            *pargs: Positional arguments
            **kwargs: Keyword arguments
        """
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
        """Returns the individual's signature if `i` is "final", which usually means we are assembling the final version of the document (as opposed to a preview).

        Args:
            i (str): The condition which, if set to "final", returns the signature.

        Returns:
            Union[DAFile, str]: The signature if the condition is met, otherwise an empty string.
        """
        if i == "final":
            return self.signature
        else:
            return ""

    def phone_numbers(
        self, country: Optional[str] = None, show_impounded: bool = False
    ) -> str:
        """Fetches and formats the phone numbers of the individual.

        Args:
            country (str, optional): The country for phone number formatting. Defaults to the country of the docassemble server.
            show_impounded (bool): If True, shows the phone numbers even if impounded. Defaults to False.

        Returns:
            str: Formatted string of phone numbers.
        """
        nums = []
        if hasattr(self, "mobile_number") and self.mobile_number:
            fmt_number = None
            try:
                fmt_number = phone_number_formatted(self.mobile_number, country=country)
            except:
                fmt_number = None
            if fmt_number:
                nums.append({fmt_number: "cell"})
            else:
                nums.append({self.mobile_number: "cell"})
        if hasattr(self, "phone_number") and self.phone_number:
            fmt_number = None
            try:
                fmt_number = phone_number_formatted(self.phone_number, country=country)
            except:
                fmt_number = None
            if fmt_number:
                nums.append({fmt_number: "other"})
            else:
                nums.append({self.phone_number: "other"})
        if len(nums) < 1:
            return ""
        # Check for impounded phone number
        elif not show_impounded and (
            hasattr(self, "phone_impounded") and self.phone_impounded
        ):
            return str(self.impounded_phone_output_label)
        elif len(nums) > 1:
            return comma_list(
                [f"{list(num.keys())[0]} ({list(num.values())[0]})" for num in nums]
            )
        elif len(nums):
            return list(nums[0].keys())[0]

        assert False  # We should never get here, no default return is necessary

    def contact_methods(self) -> str:
        """Generates a formatted string of all provided contact methods.

        Returns:
            str: A formatted string indicating the available methods to contact the individual.
        """
        methods = []
        if self.phone_numbers():
            methods.append({self.phone_numbers(): str(self.phone_number_contact_label)})
        if hasattr(self, "email") and self.email:
            methods.append({self.email: str(self.email_contact_label)})
        if hasattr(self, "other_contact_method") and self.other_contact_method:
            methods.append(
                {self.other_contact_method: str(self.other_contact_method_label)}
            )

        return comma_and_list(
            [
                list(method.values())[0] + " " + list(method.keys())[0]
                for method in methods
                if len(method)
            ],
            and_string=word("or"),
        )

    def merge_letters(self, new_letters: str) -> None:
        """If the Individual has a child_letters attribute, add the new letters to the existing list

        Avoid using. Only used in 209A.

        Args:
            new_letters (str): The new letters to add to the existing list of letters
        """
        # TODO: move to 209A package
        if hasattr(self, "child_letters"):
            self.child_letters: str = filter_letters([new_letters, self.child_letters])
        else:
            self.child_letters = filter_letters(new_letters)

    def formatted_age(self) -> str:
        """Calculates and formats the age of the individual based on their birthdate.

        Returns:
            str: Formatted age string that shows the most relevant time unit; for example, if under 2 years, it will return "X months".
        """
        dd = date_difference(self.birthdate)
        if dd.years >= 2:
            return "%d years" % (int(dd.years),)
        if dd.weeks > 12:
            return "%d months" % (int(dd.years * 12.0),)
        if dd.weeks > 2:
            return "%d weeks" % (int(dd.weeks),)
        return "%d days" % (int(dd.days),)

    def normalized_address(self) -> Union[Address, ALAddress]:
        """Fetches the normalized version of the address.

        Returns:
            Union[Address, ALAddress]: The normalized address object.
        """
        return self.address.normalized_address()

    # This design helps us translate the prompts for common fields just once
    def name_fields(
        self,
        person_or_business: str = "person",
        show_suffix: bool = True,
        show_title: bool = False,
        title_options: Optional[List[str]] = None,
        show_if: Union[str, Dict[str, str], None] = None,
        maxlengths: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, str]]:
        """
        Generates suitable field prompts for a name based on the type of entity (person or business)
        and other provided parameters.

        Args:
            person_or_business (str, optional): Specifies the entity type. It can either be "person" or "business".
                Default is "person".
            show_suffix (bool, optional): Determines if the name's suffix (e.g., Jr., Sr.) should be included in the prompts.
                Default is True.
            show_title: (bool, optional): Determines if the name's title (e.g., Mr., Ms.) should be included in the prompts.
                Default is False.
            title_options (List[str], optional): A list of title options to use in the prompts. Default is defined as a list
                of common titles in English-speaking countries.
            show_if (Union[str, Dict[str, str], None], optional): Condition to determine which fields to show.
                It can be a string, a dictionary with conditions, or None. Default is None.
            maxlengths (Dict[str, int], optional): A dictionary of field names and their maximum lengths. Default is None.

        Returns:
            List[Dict[str, str]]: A list of dictionaries where each dictionary contains field prompt details.

        Note:
            If `person_or_business` is set to None, the method will offer the end user a choice
            and will set appropriate "show ifs" conditions for each type.
        """
        if not title_options:
            title_options = [
                "Mr.",
                "Mrs.",
                "Miss",
                "Ms.",
                "Mx.",
                "Dr.",
                "Prof.",
                "Hon.",
                "Rev.",
                "Sir",
                "Lord",
                "Lady",
                "Dame",
                "Maj.",
                "Gen.",
                "Capt.",
                "Lt.",
                "Sgt.",
                "Fr.",
                "Sr.",
            ]
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
            if show_title:
                fields.insert(
                    0,
                    {
                        "label": str(self.name_title_label),
                        "field": self.attr_name("name.title"),
                        "choices": title_options,
                        "required": False,
                    },
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

            if maxlengths:
                for field in fields:
                    if field["field"] in maxlengths:
                        field["maxlength"] = maxlengths[field["field"]]
            return fields

    def address_fields(
        self,
        country_code: str = "US",
        default_state: Optional[str] = None,
        show_country: bool = False,
        show_county: bool = False,
        show_if: Union[str, Dict[str, str], None] = None,
        allow_no_address: bool = False,
        ask_if_impounded: bool = False,
        maxlengths: Optional[Dict[str, int]] = None,
        required: Optional[Dict[str, bool]] = None,
    ) -> List[Dict[str, str]]:
        """
        Generate field prompts for capturing an address.

        Args:
            country_code (str): The default country for the address. Defaults to "US".
            default_state (Optional[str]): Default state if applicable. Defaults to None.
            show_country (bool): Whether to display the country field. Defaults to False.
            show_county (bool): Whether to display the county field. Defaults to False.
            show_if (Union[str, Dict[str, str], None]): Condition to determine if the field should be shown. Defaults to None.
            allow_no_address (bool): Whether to permit entries with no address. Defaults to False.
            ask_if_impounded (bool): Whether to ask if the address is impounded. Defaults to False.
            maxlengths (Dict[str, int], optional): A dictionary of field names and their maximum lengths. Default is None.
            required (Dict[str, bool], optional): A dictionary of field names and if they should be required. Default is None (everything but unit and zip is required)

        Returns:
            List[Dict[str, str]]: A list of dictionaries with field prompts for addresses.
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
            ask_if_impounded=ask_if_impounded,
            maxlengths=maxlengths,
            required=required,
        )

    def gender_fields(
        self,
        show_help=False,
        show_if: Union[str, Dict[str, str], None] = None,
        maxlengths: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, str]]:
        """
        Generate fields for capturing gender information, including a
        self-described option.

        Args:
            show_help (bool): Whether to show additional help text. Defaults to False.
            show_if (Union[str, Dict[str, str], None]): Condition to determine if the field should be shown. Defaults to None.
            maxlengths (Dict[str, int], optional): A dictionary of field names and their maximum lengths. Default is None.

        Returns:
            List[Dict[str, str]]: A list of dictionaries with field prompts for gender.
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

        if maxlengths:
            for field in fields:
                if field["field"] in maxlengths:
                    field["maxlength"] = maxlengths[field["field"]]

        return fields

    def pronoun_fields(
        self,
        show_help=False,
        show_if: Union[str, Dict[str, str], None] = None,
        required: bool = False,
        shuffle: bool = False,
        show_unknown: Optional[Union[Literal["guess"], bool]] = "guess",
        maxlengths: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, str]]:
        """
        Generate fields for capturing pronoun information.

        Args:
            show_help (bool): Whether to show additional help text. Defaults to False.
            show_if (Union[str, Dict[str, str], None]): Condition to determine if the field should be shown. Defaults to None.
            required (bool): Whether the field is required. Defaults to False.
            shuffle (bool): Whether to shuffle the order of pronouns. Defaults to False.
            show_unknown (Union[Literal["guess"], bool]): Whether to show an "unknown" option. Can be "guess", True, or False. Defaults to "guess".
            maxlengths (Dict[str, int], optional): A dictionary of field names and their maximum lengths. Default is None.

        Returns:
            List[Dict[str, str]]: A list of dictionaries with field prompts for pronouns.
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

        if maxlengths:
            for field in fields:
                if field["field"] in maxlengths:
                    field["maxlength"] = maxlengths[field["field"]]

        return fields

    def get_pronouns(self) -> set:
        """
        Retrieve a set of the individual's pronouns.

        If the individual has selected the "self-described" option, it will use their custom input.

        Can be formatted however the author likes.

        Returns:
            set: A set of strings representing the individual's pronouns.
        """
        if hasattr(self, "pronouns") and isinstance(self.pronouns, str):
            return {self.pronouns}
        if self.pronouns.all_false():
            return {str(self.pronoun_prefer_not_to_say_label)}
        pronouns = set(self.pronouns.true_values()) - {"self-described"}
        if self.pronouns.get("self-described"):
            pronouns = pronouns.union(self.pronouns_self_described.splitlines())
        return pronouns

    def list_pronouns(self) -> str:
        """
        Retrieve a formatted string of the individual's pronouns, arranged with
        the comma_list() function.

        Returns:
            str: A formatted string of the individual's pronouns.
        """
        return comma_list(sorted(self.get_pronouns()))

    def language_fields(
        self,
        choices: Optional[List[Dict[str, str]]] = None,
        style: str = "radio",
        show_if: Union[str, Dict[str, str], None] = None,
        maxlengths: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, str]]:
        """
        Generate fields for capturing language preferences.

        Args:
            choices (Optional[List[Dict[str, str]]]): A list of language choices. Defaults to None.
            style (str): The display style of choices. Defaults to "radio".
            show_if (Union[str, Dict[str, str], None]): Condition to determine if the field should be shown. Defaults to None.
            maxlengths (Dict[str, int], optional): A dictionary of field names and their maximum lengths. Default is None.

        Returns:
            List[Dict[str, str]]: A list of dictionaries with field prompts for language preferences.
        """
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

        if maxlengths:
            for field in fields:
                if field["field"] in maxlengths:
                    field["maxlength"] = maxlengths[field["field"]]
        return fields

    def language_name(self) -> str:
        """
        Get the human-readable version of the individual's selected language.

        Returns:
            str: The human-readable version of the language. If 'other' is selected,
            it returns the value in `language_other`. Otherwise, it uses the
            `language_name` function.
        """
        if self.language == "other":
            return self.language_other
        else:
            return language_name(self.language)

    @property
    def gender_male(self) -> bool:
        """
        Returns True only if the gender is male.

        Used to assist with checkbox filling in PDFs with "skip undefined"
        turned on.
        """
        return self.gender.lower() == "male"

    @property
    def gender_female(self) -> bool:
        """
        Returns True only if the gender is female.

        Used to assist with checkbox filling in PDFs with "skip undefined"
        turned on.
        """
        return self.gender.lower() == "female"

    @property
    def gender_other(self) -> bool:
        """
        Returns True only if the gender is not male or female.

        Used to assist with checkbox filling in PDFs with "skip undefined"
        turned on.
        """
        return (self.gender != "male") and (self.gender != "female")

    @property
    def gender_nonbinary(self) -> bool:
        """
        Returns True only if the gender is nonbinary.

        Used to assist with checkbox filling in PDFs with "skip undefined"
        turned on.
        """
        return self.gender.lower() == "nonbinary"

    @property
    def gender_unknown(self) -> bool:
        """
        Returns True only if the gender is unknown.

        Used to assist with checkbox filling in PDFs with "skip undefined"
        turned on.
        """
        return self.gender.lower() == "unknown"

    @property
    def gender_undisclosed(self) -> bool:
        """
        Returns True only if the gender is not disclosed ("prefer-not-to-say")

        Used to assist with checkbox filling in PDFs with "skip undefined"
        turned on.
        """
        return self.gender.lower() == "prefer-not-to-say"

    @property
    def gender_self_described(self) -> bool:
        """
        Returns True only if the gender is self described.

        Used to assist with checkbox filling in PDFs with "skip undefined"
        turned on.
        """
        return not (
            self.gender
            in ["prefer-not-to-say", "male", "female", "unknown", "nonbinary"]
        )

    def contact_fields(self) -> None:
        """
        Return field prompts for other contact info
        """
        pass

    @property
    def initials(self) -> str:
        """
        Returns the initials of the individual as a string.

        For example, "Quinten K Steenhuis" would return "QKS".
        """
        return f"{self.name.first[:1]}{self.name.middle[:1] if hasattr(self.name,'middle') else ''}{self.name.last[:1] if hasattr(self.name, 'last') else ''}"

    def address_block(
        self,
        language=None,
        international=False,
        show_country=False,
        bare=False,
        show_impounded=False,
    ) -> str:
        """
        Generate a formatted address block for mailings.

        Args:
            language (Optional): The language in which the address is written.
            international (bool): If True, format for international mailing. Defaults to False.
            show_country (bool): If True, include the country in the address. Defaults to False.
            bare (bool): If True, produce the address without additional formatting. Defaults to False.
            show_impounded (bool): If True, show the address even if it is impounded. Defaults to False.

        Returns:
            str: The formatted address block.
        """
        if this_thread.evaluation_context == "docx":
            if isinstance(self.address, ALAddress):
                return self.address.block(
                    language=language,
                    international=international,
                    show_country=show_country,
                    bare=bare,
                    show_impounded=show_impounded,
                )
            else:
                # bare parameter is ignored for plain Address objects
                return self.address.block(
                    language=language,
                    international=international,
                    show_country=show_country,
                )
        else:
            if isinstance(self.address, ALAddress):
                return (
                    "[FLUSHLEFT] " + self.name_full()
                    if isinstance(self, ALIndividual)
                    else self.name.full(middle="full")
                    + " [NEWLINE] "
                    + self.address.block(
                        language=language,
                        international=international,
                        show_country=show_country,
                        bare=bare,
                        show_impounded=show_impounded,
                    )
                )
            else:
                return (
                    "[FLUSHLEFT] " + self.name_full()
                    if isinstance(self, ALIndividual)
                    else self.name.full(middle="full")
                    + " [NEWLINE] "
                    + self.address.block(
                        language=language,
                        international=international,
                        show_country=show_country,
                    )
                )

    def pronoun(self, **kwargs) -> str:
        """Returns an objective pronoun as appropriate, based on the user's `pronouns` attribute or `gender` attribute.

        The pronoun could be "I", "you," "her," "him," "it," or "them", or a user-provided pronoun.
        If the user has selected multiple pronouns, each will appear, separated by a "/".

        This method will not trigger the definition of `gender` or `pronouns`, but it will use them if they are defined,
        with `pronouns` taking precedence. As a default, it will either use the value of `default` or the individual's full name.

        Args:
            **kwargs: Additional keyword arguments that are defined [upstream](https://docassemble.org/docs/objects.html#language%20methods).
                    - person (Optional[[Union[str,int]]): Whether to use a first, second, or third person pronoun. Can be one of 1/"1p", 2/"2p", or 3/"3p" (default is 3). See [upstream](https://docassemble.org/docs/objects.html#language%20methods) documentation for more information.
                    - default (Optional[str]): The default word to use if the pronoun is not defined, e.g. "the agent". If not defined, the default term is the user's name.
        Returns:
            str: The appropriate pronoun.
        """
        person = str(kwargs.get("person", self.get_point_of_view()))

        if person in ("1", "1p", "2", "2p"):
            # Use the parent version of pronoun
            return super().pronoun(**kwargs)

        if "default" in kwargs:
            default = kwargs.pop("default")
        else:
            default = self.name_full()

        if hasattr(self, "pronouns") and self.pronouns:
            if isinstance(self.pronouns, str):
                pronouns = DADict(elements={self.pronouns.lower(): True})
            else:
                pronouns = self.pronouns

        if self == this_thread.global_vars.user:
            output = word("you", **kwargs)
        elif hasattr(self, "pronouns") and self.pronouns:
            pronouns_to_use = []
            if isinstance(pronouns, DADict):
                for pronoun in pronouns.true_values():
                    if pronoun in [
                        "she/her/hers",
                        "he/him/his",
                        "they/them/theirs",
                        "ze/zir/zirs",
                    ]:
                        if pronoun == "she/her/hers":
                            pronouns_to_use.append(word("her", **kwargs))
                        elif pronoun == "he/him/his":
                            pronouns_to_use.append(word("him", **kwargs))
                        elif pronoun == "they/them/theirs":
                            pronouns_to_use.append(word("them", **kwargs))
                        elif pronoun == "ze/zir/zirs":
                            pronouns_to_use.append(word("zir", **kwargs))
                    elif pronoun == "self-described" and has_parsable_pronouns(
                        self.pronouns_self_described
                    ):
                        pronouns_to_use.append(
                            parse_custom_pronouns(self.pronouns_self_described)["o"]
                        )
                    elif has_parsable_pronouns(pronoun):
                        pronouns_to_use.append(parse_custom_pronouns(pronoun)["o"])
            if len(pronouns_to_use) > 0:
                output = "/".join(pronouns_to_use)
            else:
                output = default
        elif hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            output = word("it", **kwargs)
        elif hasattr(self, "gender"):
            if self.gender.lower() == "female":
                output = word("her", **kwargs)
            elif self.gender.lower() == "male":
                output = word("him", **kwargs)
            else:
                output = word("them", **kwargs)
        else:
            output = default

        if "capitalize" in kwargs and kwargs["capitalize"]:
            return capitalize(output)
        return output

    def pronoun_objective(self, **kwargs) -> str:
        """Returns the same pronoun as the `pronoun()` method.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            str: The appropriate objective pronoun.
        """
        return self.pronoun(**kwargs)

    def pronoun_possessive(self, target, **kwargs) -> str:
        """
        Returns a possessive pronoun and a target word, based on attributes.

        This method will not trigger the definition of `gender` or `pronouns`, but it will use them if they are defined,
        with `pronouns` taking precedence. As a default, it will either use the value of `default` or the individual's full name.

        Given a target word, the function returns "{pronoun} {target}". The pronoun could be
        "my", "her," "his," "its," or "their". It depends on the `gender` and `person_type` attributes
        and whether the individual is the current user.

        Args:
            target (str): The target word to follow the pronoun.
            **kwargs: Additional keyword arguments that can be passed to modify the behavior. These might include:
                - `default` (Optional[str]): The default word to use if the pronoun is not defined, e.g., "the agent". If not defined, the default term is the user's name.
                - `person` (Optional[Union[str, int]]): Whether to use a first, second, or third person pronoun. Can be one of 1/"1p", 2/"2p", or 3/"3p" (default is 3). See [upstream documentation](https://docassemble.org/docs/objects.html#language%20methods) for more information.

        Returns:
            str: The appropriate possessive phrase, e.g., "her book", "their document".
        """
        person = str(kwargs.get("person", self.get_point_of_view()))

        if person in ("1", "1p", "2", "2p"):
            # Use the parent version of pronoun
            return super().pronoun_possessive(target, **kwargs)

        if hasattr(self, "pronouns") and isinstance(self.pronouns, str):
            pronouns = DADict(elements={self.pronouns.lower(): True})
        else:
            pronouns = self.pronouns

        if "default" in kwargs:
            default = kwargs.pop("default")
        else:
            default = self.name_full()

        if self == this_thread.global_vars.user and (
            "thirdperson" not in kwargs or not kwargs["thirdperson"]
        ):
            output = your(target, **kwargs)
        elif hasattr(self, "pronouns") and self.pronouns:
            pronouns_to_use = []
            if isinstance(pronouns, DADict):
                for pronoun in pronouns.true_values():
                    if pronoun in [
                        "she/her/hers",
                        "he/him/his",
                        "they/them/theirs",
                        "ze/zir/zirs",
                    ]:
                        if pronoun == "she/her/hers":
                            pronouns_to_use.append(her(target, **kwargs))
                        elif pronoun == "he/him/his":
                            pronouns_to_use.append(his(target, **kwargs))
                        elif pronoun == "they/them/theirs":
                            pronouns_to_use.append(their(target, **kwargs))
                        elif pronoun == "ze/zir/zirs":
                            pronouns_to_use.append(word("zir", **kwargs) + " " + target)
                    elif pronoun == "self-described" and has_parsable_pronouns(
                        self.pronouns_self_described
                    ):
                        pronouns_to_use.append(
                            parse_custom_pronouns(self.pronouns_self_described)["p"]
                            + " "
                            + target
                        )
                    elif has_parsable_pronouns(pronoun):
                        pronouns_to_use.append(
                            parse_custom_pronouns(pronoun)["p"] + " " + target
                        )
            if len(pronouns_to_use) > 0:
                output = "/".join(pronouns_to_use)
            else:
                output = default
        elif hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            output = its(target, **kwargs)
        elif hasattr(self, "gender"):
            if self.gender.lower() == "female":
                output = her(target, **kwargs)
            elif self.gender.lower() == "male":
                output = his(target, **kwargs)
            else:
                output = their(target, **kwargs)
        else:
            output = default

        if "capitalize" in kwargs and kwargs["capitalize"]:
            return capitalize(output)
        return output

    def pronoun_subjective(self, **kwargs) -> str:
        """Returns a subjective pronoun, based on attributes.

        The pronoun could be "you," "we", "she," "he," "it," or "they". It depends
        on the `gender` and `person_type` attributes and whether the individual
        is the current user.

        Args:
            **kwargs: Additional keyword arguments that are defined [upstream](https://docassemble.org/docs/objects.html#language%20methods).
                    - person (Optional[[Union[str,int]]): Whether to use a first, second, or third person pronoun. Can be one of 1/"1p", 2/"2p", or 3/"3p" (default is 3). See [upstream](https://docassemble.org/docs/objects.html#language%20methods) documentation for more information.
                    - default (Optional[str]): The default word to use if the pronoun is not defined, e.g. "the agent". If not defined, the default term is the user's name.
        Returns:
            str: The appropriate subjective pronoun.
        """
        person = str(kwargs.get("person", self.get_point_of_view()))

        if person in ("1", "1p", "2", "2p"):
            # Use the parent version of pronoun
            return super().pronoun_subjective(**kwargs)
        if "default" in kwargs:
            default = kwargs.pop("default")
        else:
            default = self.name_full()

        if hasattr(self, "pronouns") and self.pronouns:
            if isinstance(self.pronouns, str):
                pronouns = DADict(elements={self.pronouns.lower(): True})
            else:
                pronouns = self.pronouns

        if self == this_thread.global_vars.user:
            output = word("you", **kwargs)
        elif hasattr(self, "pronouns") and self.pronouns:
            pronouns_to_use = []
            if isinstance(pronouns, DADict):
                for pronoun in pronouns.true_values():
                    if pronoun in [
                        "she/her/hers",
                        "he/him/his",
                        "they/them/theirs",
                        "ze/zir/zirs",
                    ]:
                        if pronoun == "she/her/hers":
                            pronouns_to_use.append(word("she", **kwargs))
                        elif pronoun == "he/him/his":
                            pronouns_to_use.append(word("he", **kwargs))
                        elif pronoun == "they/them/theirs":
                            pronouns_to_use.append(word("they", **kwargs))
                        elif pronoun == "ze/zir/zirs":
                            pronouns_to_use.append(word("ze", **kwargs))
                    elif pronoun == "self-described" and has_parsable_pronouns(
                        self.pronouns_self_described
                    ):
                        pronouns_to_use.append(
                            parse_custom_pronouns(self.pronouns_self_described)["s"]
                        )
                    elif has_parsable_pronouns(pronoun):
                        pronouns_to_use.append(parse_custom_pronouns(pronoun)["s"])
            if len(pronouns_to_use) > 0:
                output = "/".join(pronouns_to_use)
            else:
                output = default
        elif hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            output = word("it", **kwargs)
        elif hasattr(self, "gender"):
            if self.gender.lower() == "female":
                output = word("she", **kwargs)
            elif self.gender.lower() == "male":
                output = word("he", **kwargs)
            else:
                output = word("they", **kwargs)
        else:
            output = default

        if "capitalize" in kwargs and kwargs["capitalize"]:
            return capitalize(output)
        return output

    def pronoun_reflexive(self, **kwargs) -> str:
        """Returns the appropriate reflexive pronoun ("herself", "themself", "myself"), based on the user's pronouns or gender and whether we are asked
        to return a 1st, 2nd, or 3rd person pronoun.

        Note that if the person has pronouns of they/them/theirs or a nonbinary gender, we return "themself" as the singular non-gendered
        reflexive pronoun and not "themselves". This has growing acceptance although some consider it nonstandard.
        See: https://www.merriam-webster.com/wordplay/themself

        Args:
            **kwargs: Additional keyword arguments that are defined [upstream](https://docassemble.org/docs/objects.html#language%20methods).
                    - person (Optional[[Union[str,int]]): Whether to use a first, second, or third person pronoun. Can be one of 1/"1p", 2/"2p", or 3/"3p" (default is 3). See [upstream](https://docassemble.org/docs/objects.html#language%20methods) documentation for more information.
                    - default (Optional[str]): The default word to use if the pronoun is not defined, e.g. "the agent". If not defined, the default term is the user's name.

        Returns:
            str: The appropriate reflexive pronoun.
        """
        person = str(kwargs.get("person", self.get_point_of_view()))

        if person in ("1", "1p", "2", "2p"):
            if person == "1":
                return word("myself")
            if person == "1p":
                return word("ourselves")
            if person == "2":
                return word("yourself")
            if person == "2p":
                return word("yourselves")

        if self == this_thread.global_vars.user:
            output = word("yourself", **kwargs)

        if "default" in kwargs:
            default = kwargs.pop("default")
        else:
            default = None

        if hasattr(self, "pronouns") and self.pronouns:
            if isinstance(self.pronouns, str):
                pronouns = DADict(elements={self.pronouns.lower(): True})
            else:
                pronouns = self.pronouns
        else:
            pronouns = None

        if self == this_thread.global_vars.user:
            output = word("yourself", **kwargs)
        elif hasattr(self, "pronouns") and self.pronouns:
            pronouns_to_use = []

            if isinstance(pronouns, DADict):
                for pronoun in pronouns.true_values():
                    if pronoun in [
                        "she/her/hers",
                        "he/him/his",
                        "they/them/theirs",
                        "ze/zir/zirs",
                    ]:
                        if pronoun == "she/her/hers":
                            pronouns_to_use.append(word("herself", **kwargs))
                        elif pronoun == "he/him/his":
                            pronouns_to_use.append(word("himself", **kwargs))
                        elif pronoun == "they/them/theirs":
                            pronouns_to_use.append(word("themself", **kwargs))
                        elif pronoun == "ze/zir/zirs":
                            pronouns_to_use.append(word("zirself", **kwargs))
                    elif pronoun == "self-described" and has_parsable_pronouns(
                        self.pronouns_self_described
                    ):
                        pronouns_to_use.append(
                            parse_custom_pronouns(self.pronouns_self_described)["o"]
                            + word("self")
                        )
                    elif has_parsable_pronouns(pronoun):
                        pronouns_to_use.append(
                            parse_custom_pronouns(pronoun)["o"] + word("self")
                        )
                if len(pronouns_to_use) > 0:
                    output = "/".join(pronouns_to_use)
                else:
                    output = default
        elif hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            output = word("itself", **kwargs)
        elif hasattr(self, "gender"):
            if self.gender.lower() == "female":
                output = word("herself", **kwargs)
            elif self.gender.lower() == "male":
                output = word("himself", **kwargs)
            else:
                output = word("themself", **kwargs)
        else:
            if default:
                output = default
            else:
                output = word(
                    "themself"
                )  # reflexive pronoun shouldn't be the person's name

        if kwargs.get("capitalize"):
            return capitalize(output)
        return output

    def name_full(self) -> str:
        """Returns the individual's full name.

        If the person has the attribute person_type and it is defined
        as either `business` or `organization`, it will only return
        the first name, even if middle, last, or suffix are defined.

        Returns:
            str: The individual or business's full name.
        """
        if hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            return self.name.first
        return self.name.full(middle="full")

    def name_initials(self) -> str:
        """
        Returns the individual's name with the middle name as an initial.
        Equivalent to `name.full(middle="initial")`, which is also the default.
        Defined only to make it possible to be explicit about the name form.

        If the person has the attribute person_type and it is defined
        as either `business` or `organization`, it will only return
        the "initials" of the first name, even if middle, last, or suffix are defined.

        Returns:
            str: The individual's name with the middle name as an initial.
        """
        if hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            return self.name.first
        return self.name.full(middle="initial")

    def name_short(self) -> str:
        """
        Returns the individual's name without any middle name.

        Equivalent to self.name.firstlast()

        If the person has the attribute person_type and it is defined
        as either `business` or `organization`, it will only return
        the first name, even if middle, last, or suffix are defined.

        Returns:
            str: The individual'
        """
        if hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            return self.name.first
        return self.name.firstlast()

    def familiar(
        self, unique_names: Optional[List[Any]] = None, default: Optional[str] = None
    ) -> str:
        """
        Returns the individual's name in the most familiar form possible.

        The purpose is to allow using a short version of the individual's name in an unambiguous
        way in the interview. For example: referring to the child in a guardianship petition
        by first name instead of "the minor". But there may be a problem if context doesn't make
        it clear if you are talking about the child or their parent when they share a name.

        In order, it will try to use:

        * just the first name
        * the first name and suffix
        * the first and middle name
        * the first and last name
        * the full name
        * the default value, e.g., "the minor", if provided
        * the full name

        If the person has the attribute `person_type` and it is defined
        as either `business` or `organization`, it will only return
        the first name, even if middle, last, or suffix are defined.

        Args:
            unique_names (Optional[List[Any]]): A list of unique names to compare against. Defaults to None.
            default (Optional[str]): The default name to return if no unique name is found. Defaults to None.

        Returns:
            str: The individual's name in the most familiar form possible.

        Example:
            ```mako
            Who do you want to take care of ${ children.familiar(unique_names=parents + petitioners, default="the minor") }
            ```
        """
        if hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            return self.name.first

        if unique_names is None:
            unique_names = []

        first_name_candidates = [person.familiar() for person in unique_names]
        if self.name.first not in first_name_candidates:
            return self.name.first

        first_name_and_suffix_candidates = [
            f"{person.familiar()} {person.name.suffix if hasattr(person.name, 'suffix') else ''}"
            for person in unique_names
        ]
        if (
            f"{self.name.first} {self.name.suffix if hasattr(self.name, 'suffix') else ''}"
            not in first_name_and_suffix_candidates
        ):
            if hasattr(self.name, "suffix") and self.name.suffix:
                return f"{self.name.first} {self.name.suffix if hasattr(self.name, 'suffix') else ''}"
            return self.name.first

        first_and_middle_candidates = [
            f"{person.name.first} {person.name.middle if hasattr(person.name, 'middle') and person.name.middle else ''}"
            for person in unique_names
        ]
        if (
            f"{self.name.first} {self.name.middle if hasattr(self.name, 'middle') and self.name.middle else ''}"
            not in first_and_middle_candidates
        ):
            if hasattr(self.name, "middle") and self.name.middle:
                return f"{self.name.first} {self.name.middle}"
            return self.name.first

        first_and_last_candidates = [
            (
                person.name.firstlast()
                if hasattr(person.name, "last")
                else person.name.first
            )
            for person in unique_names
        ]
        if self.name_short() not in first_and_last_candidates:
            return self.name_short()

        full_name_candidates = [person.name.full() for person in unique_names]
        if self.name_full() not in full_name_candidates:
            return self.name_full()

        if default:
            return default
        return self.name_full()  # We tried but couldn't disambiguate

    def __str__(self) -> str:
        """
        Returns a string representation of the individual, which is their full name with the
        middle name shortened to one letter.

        If the individual has the attribute `person_type` and it is defined
        as either `business` or `organization`, it will only return
        the first name, even if middle, last, or suffix are defined.

        Returns:
            str: The individual's name.
        """
        if hasattr(self, "person_type") and self.person_type in [
            "business",
            "organization",
        ]:
            return self.name.first

        return (
            super().__str__()
        )  # This will call the parent's __str__ method, which returns the full name with middle initial


# (DANav isn't in public DA API, but currently in functions.py)
def section_links(nav) -> List[str]:  # type: ignore
    """Returns a list of clickable navigation links without animation.

    Args:
        nav: The navigation object.

    Returns:
        List[str]: A list of clickable navigation links without animation.
    """
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
    """
    For legacy email to court forms, this checks to see if the form
    is being run on the dev, test, or production server.

    The text "dev" or "test" needs to be in the URL root in the DA config: can change in `/config`.

    Returns:
        bool: True if the form is being run on the dev, test, or production server.
    """
    return not (
        get_config("debug")
        or "dev" in get_config("url root")
        or "test" in get_config("url root")
        or "localhost" in get_config("url root")
    )


# TODO: move to 209A package
# This one is only used for 209A--should move there along with the combined_letters() method
def filter_letters(letter_strings: Union[List[str], str]) -> str:
    """Used to take a list of letters like ["A","ABC","AB"] and filter out any duplicate letters.

    Avoid using, this is created for 209A.

    Args:
        letter_strings (Union[List[str], str]): A list of letters.

    Returns:
        str: A string of unique letters.
    """
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
) -> str:
    """
    Return HTML for a font-awesome icon of the specified size and color. You can reference
    a CSS variable (such as Bootstrap theme color) or a true CSS color reference, such as 'blue' or
    '#DDDDDD'. Defaults to Bootstrap theme color "primary".

    Args:
        icon (str): The name of the icon to use. See https://fontawesome.com/icons for a list of icons.
        color (str): The color of the icon. Defaults to "primary".
        color_css (Optional[str]): A CSS variable or color reference. Defaults to None.
        size (str): The size of the icon. Defaults to "sm".

    Returns:
        str: HTML for the icon.
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


def is_sms_enabled() -> bool:
    """Checks if SMS (Twilio) is enabled on the server. Does not verify that it works.

    See https://docassemble.org/docs/config.html#twilio for more info.

    Returns:
        bool: True if there is a non-empty Twilio config on the server, False otherwise
    """
    twilio_config = get_config("twilio")
    if isinstance(twilio_config, list):
        to_check = twilio_config[0]
    elif isinstance(twilio_config, dict):
        to_check = twilio_config
    else:
        return False

    return bool(
        to_check.get("sms")
        and to_check.get("account sid")
        and to_check.get("auth token")
        and to_check.get("number")
    )


def is_phone_or_email(text: str) -> bool:
    """
    Returns True if the string is either a valid phone number or a valid email address.
    If SMS is not enabled on the server (through the Twilio config), only accepts emails.
    Email validation is extremely minimal--just checks for an @ sign between two non-zero length
    strings.

    Args:
        text (str): The string to check.

    Returns:
        bool: True if the string is either a valid phone number or a valid email address.

    Raises:
        DAValidationError if the string is neither a valid phone number nor a valid email address.
    """
    sms_enabled = is_sms_enabled()
    if re.match("\S+@\S+", text) or (sms_enabled and phone_number_is_valid(text)):
        return True
    else:
        if sms_enabled:
            validation_error("Enter a valid phone number or email address")
        else:
            validation_error("Enter a valid email address")
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

    Args:
        github_user (str): The GitHub username of the repository owner.
        github_repo_name (str): The name of the repository.
        auth (Optional[dict]): A dictionary containing authentication information. Defaults to None.

    Returns:
        Union[DADateTime, None]: The date that the given GitHub repository was modified or None if API call fails.
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
    function.

    Args:
        language_code (str): A 2 digit language code abbreviation.

    Returns:
        str: The full name of the language.
    """
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
    an invalid country_code (e.g., a country name spelled out)

    Args:
        country_code (str): A 2 digit country code abbreviation.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with field prompts for states.
    """
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


def get_visible_al_nav_items(
    nav_items: List[Union[str, dict]],
) -> List[Union[str, dict]]:
    """
    Processes a list of nav items and returns only the ones that are not hidden.
    Can be used to control the visible nav items in a more declarative way while keeping
    the navigation dynamic.

    Expects a list like this:

    data = [
        {"key": "value", "hidden": True},
        "top level item",
        {"key2": [{"subkey": "subvalue", "hidden": False}, {"subkey": "subvalue2", "hidden": True}]},
    ]

    Args:
        nav_items: a list of nav items

    Returns:
        a list of nav items with hidden items removed
    """
    new_list: List[Union[str, dict]] = []

    for item in nav_items:
        # For strings at top level
        if isinstance(item, str):
            new_list.append(item)
            continue

        # For dictionaries at top level
        item_copy = deepcopy(item)
        if not str(item_copy.pop("hidden", "False")).lower() == "true":  # if not hidden
            for key, val in item_copy.items():
                if isinstance(val, list):  # if value of a key is a list
                    new_sublist: List[Union[str, dict]] = []
                    for subitem in val:
                        # Add subitem strings as-is
                        if isinstance(subitem, str):
                            new_sublist.append(subitem)
                        # Add dictionaries if not hidden
                        elif (
                            isinstance(subitem, dict)
                            and not str(subitem.pop("hidden", "False")).lower()
                            == "true"
                        ):
                            new_sublist.append(subitem)
                    item_copy[key] = new_sublist
            new_list.append(item_copy)
        continue

    return new_list

import unittest
from .al_general import ALIndividual, ALAddress, get_visible_al_nav_items
from unittest.mock import Mock, patch
from docassemble.base.util import DADict, DAAttributeError


class test_aladdress(unittest.TestCase):
    def setUp(self):
        self.addr = ALAddress()

    def test_empty_is_empty(self):
        addr = ALAddress(address="", city="")
        self.assertEqual(addr.on_one_line(), "")

    def test_address_required(self):
        addr = ALAddress(
            address_label="address",
            unit_label="unit",
            city_label="city",
            state_label="state",
            zip_label="zip",
        )
        addr.instanceName = "addr"
        fields = addr.address_fields(required={"addr.zip": True})
        for field in fields:
            if "zip" in field["field"]:
                self.assertTrue(field["required"])
        fields = addr.address_fields()
        for field in fields:
            if "zip" in field["field"]:
                self.assertFalse(field["required"])

    def test_no_unit_floor_room(self):
        self.assertFalse(hasattr(self.addr, "unit"))
        self.assertFalse(hasattr(self.addr, "floor"))
        self.assertFalse(hasattr(self.addr, "room"))
        self.assertEqual(self.addr.formatted_unit(), "")

    def test_require_unit_exception(self):
        self.assertFalse(hasattr(self.addr, "unit"))
        with self.assertRaises(AttributeError):
            self.addr.formatted_unit(require=True)

    def test_unit_isnumeric(self):
        self.addr.unit = "123"
        self.assertEqual(self.addr.formatted_unit(), "Unit 123")

    def test_unit_no_space_without_known_descriptors(self):
        self.addr.unit = "1A"
        self.assertEqual(self.addr.formatted_unit(), "Unit 1A")

    def test_unit_with_space_and_known_descriptor(self):
        self.addr.unit = "Apt 1A"
        self.assertEqual(self.addr.formatted_unit(), "Apt 1A")

    def test_bare_unit(self):
        self.addr.unit = "1A"
        self.assertEqual(self.addr.formatted_unit(bare=True), "1A")

    def test_floor_formatting(self):
        self.addr.floor = "5"
        self.assertEqual(self.addr.formatted_unit(), "Floor 5")

    def test_room_formatting(self):
        self.addr.room = "101"
        self.assertEqual(self.addr.formatted_unit(), "Room 101")


class TestALIndividual(unittest.TestCase):
    def setUp(self):
        self.individual = ALIndividual()

        # Creating a mock object for this_thread
        self.this_thread = Mock()

        # Mocking this_thread.global_vars.user as a distinct object
        self.this_thread.global_vars.user = Mock()

        # Assigning this_thread to self.individual
        self.individual.this_thread = self.this_thread

        self.individual.name.first = "John"

        # Mock template attributes for demographic fields
        self.individual.race_ethnicity_label = "Race and ethnicity"
        self.individual.race_ethnicity_other_label = "Please specify"
        self.individual.race_ethnicity_help_text = "You may select more than one category that applies to you."
        self.individual.age_range_label = "Age range"
        self.individual.age_range_help_text = "Select the age range that applies to you."
        self.individual.income_range_label = "Household income range"
        self.individual.income_range_help_text = "Select the range that best describes your household's total income before taxes in the last 12 months."
        self.individual.occupation_label = "Occupation"
        self.individual.occupation_other_label = "Please specify your occupation"
        self.individual.occupation_help_text = "Select the category that best describes your current work or situation."

        self._functions_value_patcher = patch(
            "docassemble.base.functions.value",
            side_effect=self._mock_value_with_defaults,
        )
        self._util_value_patcher = patch(
            "docassemble.base.util.value",
            side_effect=self._mock_value_with_defaults,
        )
        self._al_general_value_patcher = patch(
            "docassemble.AssemblyLine.al_general.value",
            side_effect=self._mock_value_with_defaults,
        )
        self._functions_value_patcher.start()
        self._util_value_patcher.start()
        self._al_general_value_patcher.start()

    def tearDown(self):
        self._al_general_value_patcher.stop()
        self._util_value_patcher.stop()
        self._functions_value_patcher.stop()

    def _mock_value_with_defaults(self, variable_name, *args, **kwargs):
        if variable_name == "al_name_suffixes":
            return ["Jr.", "Sr."]
        if variable_name == "al_name_titles":
            return ["Mr.", "Ms."]
        if variable_name == "al_pronoun_choices":
            return [
                {"He/him/his": "he/him/his"},
                {"She/her/hers": "she/her/hers"},
                {"They/them/theirs": "they/them/theirs"},
            ]
        if variable_name == "al_race_ethnicity_choices":
            return [
                {"American Indian or Alaska Native": "american_indian_alaska_native"},
                {"Asian": "asian"},
                {"White": "white"},
                {"Other": "other"},
                {"Prefer not to say": "prefer_not_to_say"},
            ]
        if variable_name == "al_income_range_choices":
            return [
                {"Under $25,000": "under_25k"},
                {"$25,000 - $49,999": "25k_49k"},
                {"$50,000 - $74,999": "50k_74k"},
                {"Prefer not to say": "prefer_not_to_say"},
            ]
        if variable_name == "al_occupation_choices":
            return [
                {"Service": "service"},
                {"Student": "student"},
                {"Professional": "professional"},
                {"Other": "other"},
                {"Prefer not to say": "prefer_not_to_say"},
            ]
        if variable_name == "al_age_range_choices":
            return [
                {"Under 18": "under_18"},
                {"18-24": "18_24"},
                {"25-34": "25_34"},
                {"35-44": "35_44"},
                {"45-54": "45_54"},
                {"55-64": "55_64"},
                {"65 or older": "65_older"},
                {"Prefer not to say": "prefer_not_to_say"},
            ]
        # Never pass through to the real value() function as it only works in an interactive DA server
        raise ValueError(
            f"Unmocked call to value() with variable_name='{variable_name}'. Please add a mock for this variable in the test."
        )

    def test_phone_numbers(self):
        self.assertEqual(self.individual.phone_numbers(), "")
        self.individual.phone_number = ""
        self.individual.mobile_number = None
        self.assertEqual(self.individual.phone_numbers(), "")

        self.individual.mobile_number = "aoueb"
        self.assertEqual(self.individual.phone_numbers(), "aoueb")
        self.individual.phone_number = "409_4567890 ext. 123"
        self.assertEqual(
            self.individual.phone_numbers(),
            "aoueb (cell), 409_4567890 ext. 123 (other)",
        )

        self.individual.mobile_number = "4094567890"
        self.individual.phone_number = None
        self.assertEqual(self.individual.phone_numbers(), "(409) 456-7890")
        self.individual.phone_number = "987-6543210"
        self.assertEqual(
            self.individual.phone_numbers(),
            "(409) 456-7890 (cell), (987) 654-3210 (other)",
        )

        # TODO: Not sure how to test international numbers
        # TODO: test impounding

    def test_pronoun(self):
        self.individual.pronouns = None
        self.individual.person_type = "individual"

        self.individual.gender = "female"
        self.assertEqual(self.individual.pronoun(), "her")
        self.assertEqual(self.individual.pronoun(capitalize=True), "Her")

        self.individual.gender = "male"
        self.assertEqual(self.individual.pronoun(), "him")
        self.assertEqual(self.individual.pronoun(capitalize=True), "Him")

        self.individual.gender = "nonbinary"
        self.assertEqual(self.individual.pronoun(), "them")
        self.assertEqual(self.individual.pronoun(capitalize=True), "Them")

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": True,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun(), "her")
        self.assertEqual(self.individual.pronoun(capitalize=True), "Her")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": True,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun(), "him")
        self.assertEqual(self.individual.pronoun(capitalize=True), "Him")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": True,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun(), "them")
        self.assertEqual(self.individual.pronoun(capitalize=True), "Them")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": True,
            },
        )
        self.assertEqual(self.individual.pronoun(), "zir")
        self.assertEqual(self.individual.pronoun(capitalize=True), "Zir")

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = "business"
        self.assertEqual(self.individual.pronoun(), "it")
        self.assertEqual(self.individual.pronoun(capitalize=True), "It")

    def test_pronoun_objective(self):
        self.individual.pronouns = None
        self.individual.person_type = "individual"

        self.individual.gender = "female"
        self.assertEqual(self.individual.pronoun_objective(), "her")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "Her")

        self.individual.gender = "male"
        self.assertEqual(self.individual.pronoun_objective(), "him")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "Him")

        self.individual.gender = "nonbinary"
        self.assertEqual(self.individual.pronoun_objective(), "them")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "Them")

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": True,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_objective(), "her")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "Her")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": True,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_objective(), "him")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "Him")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": True,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_objective(), "them")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "Them")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": True,
            },
        )
        self.assertEqual(self.individual.pronoun_objective(), "zir")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "Zir")

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = "business"
        self.assertEqual(self.individual.pronoun_objective(), "it")
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), "It")

    def test_pronoun_possessive(self):
        self.individual.pronouns = None
        self.individual.person_type = "individual"
        item = "fish"

        self.individual.gender = "female"
        self.assertEqual(self.individual.pronoun_possessive(item), "her fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "Her fish"
        )

        self.individual.gender = "male"
        self.assertEqual(self.individual.pronoun_possessive(item), "his fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "His fish"
        )

        self.individual.gender = "nonbinary"
        self.assertEqual(self.individual.pronoun_possessive(item), "their fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "Their fish"
        )

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": True,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_possessive(item), "her fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "Her fish"
        )

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": True,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_possessive(item), "his fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "His fish"
        )

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": True,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_possessive(item), "their fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "Their fish"
        )

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": True,
            },
        )
        self.assertEqual(self.individual.pronoun_possessive(item), "zir fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "Zir fish"
        )

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = "business"
        self.assertEqual(self.individual.pronoun_possessive(item), "its fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True), "Its fish"
        )

    def test_pronoun_subjective(self):
        self.individual.pronouns = None
        self.individual.person_type = "individual"

        self.individual.gender = "female"
        self.assertEqual(self.individual.pronoun_subjective(), "she")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "She")

        self.individual.gender = "male"
        self.assertEqual(self.individual.pronoun_subjective(), "he")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "He")

        self.individual.gender = "nonbinary"
        self.assertEqual(self.individual.pronoun_subjective(), "they")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "They")

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": True,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_subjective(), "she")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "She")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": True,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_subjective(), "he")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "He")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": True,
                "ze/zir/zirs": False,
            },
        )
        self.assertEqual(self.individual.pronoun_subjective(), "they")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "They")

        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": True,
            },
        )
        self.assertEqual(self.individual.pronoun_subjective(), "ze")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "Ze")

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = "business"
        self.assertEqual(self.individual.pronoun_subjective(), "it")
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), "It")

    def test_custom_pronouns(self):
        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={
                "she/her/hers": False,
                "he/him/his": False,
                "they/them/theirs": False,
                "ze/zir/zirs": False,
                "self-described": True,
            },
        )

        self.individual.pronouns_self_described = "Xe/Xir/Xem"
        self.assertEqual(self.individual.pronoun_objective(), "xe")
        self.assertEqual(self.individual.pronoun_subjective(), "xir")
        self.assertEqual(self.individual.pronoun_possessive("fish"), "xem fish")

        self.individual.pronouns_self_described = "Xe/Xir/Xirs/xem/xirself"
        self.assertEqual(self.individual.pronoun_objective(), "John")

    def test_name_methods(self):
        self.individual.name.first = "John"
        self.individual.name.middle = "Jacob"
        self.individual.name.last = "Jingleheimer"

        self.assertEqual(self.individual.name_full(), "John Jacob Jingleheimer")
        self.assertEqual(self.individual.name_initials(), "John J. Jingleheimer")
        self.assertEqual(self.individual.name_short(), "John Jingleheimer")

        self.individual.person_type = "business"
        self.individual.name.first = "Johnny's Sandwiches"

        self.assertEqual(self.individual.name_full(), "Johnny's Sandwiches")
        self.assertEqual(self.individual.name_initials(), "Johnny's Sandwiches")
        self.assertEqual(self.individual.name_short(), "Johnny's Sandwiches")
        self.assertEqual(str(self.individual), "Johnny's Sandwiches")

    def test_name_fields_required(self):
        """Test the required parameter for name_fields method"""
        self.individual.instanceName = "test_individual"
        self.individual.first_name_label = "First name"
        self.individual.middle_name_label = "Middle name"
        self.individual.last_name_label = "Last name"
        self.individual.suffix_label = "Suffix"
        self.individual.title_label = "Title"
        self.individual.business_name_label = "Business name"

        # Test without required parameter - middle name should default to False
        fields = self.individual.name_fields(
            person_or_business="person",
            title_choices=["a title"],
            suffix_choices=["Jr.", "Sr."],
        )
        middle_field = None
        for field in fields:
            if "middle" in field["field"]:
                middle_field = field
                break
        self.assertIsNotNone(middle_field)
        self.assertEqual(middle_field["required"], False)

        # Test with required parameter making middle name required
        fields = self.individual.name_fields(
            person_or_business="person",
            required={"test_individual.name.middle": True},
            title_choices=["a title"],
            suffix_choices=["Jr.", "Sr."],
        )
        middle_field = None
        for field in fields:
            if "middle" in field["field"]:
                middle_field = field
                break
        self.assertIsNotNone(middle_field)
        self.assertEqual(middle_field["required"], True)

        # Test business case with required parameter
        fields = self.individual.name_fields(
            person_or_business="business",
            required={"test_individual.name.first": True},
            title_choices=["a title"],
            suffix_choices=["Jr.", "Sr."],
        )
        business_field = fields[0]
        self.assertEqual(business_field["required"], True)

    def test_gender_fields_required(self):
        """Test the required parameter for gender_fields method"""
        self.individual.instanceName = "test_individual"
        self.individual.gender_female_label = "Female"
        self.individual.gender_male_label = "Female"
        self.individual.gender_nonbinary_label = "Non-binary"
        self.individual.gender_prefer_not_to_say_label = "Prefer not to say"
        self.individual.gender_prefer_self_described_label = "Prefer self-described"
        self.individual.gender_unknown_label = "Unknown"
        self.individual.gender_self_described_label = "Self described"
        self.individual.gender_label = "Gender"

        # Test without required parameter
        fields = self.individual.gender_fields()
        gender_field = fields[0]
        self.assertNotIn(
            "required", gender_field
        )  # Should not have required by default

        # Test with required parameter
        fields = self.individual.gender_fields(
            required={"test_individual.gender": True}
        )
        gender_field = fields[0]
        self.assertEqual(gender_field["required"], True)

        # Test key not in required dict - should not change default
        fields = self.individual.gender_fields(required={"other_field": True})
        gender_field = fields[0]
        self.assertNotIn("required", gender_field)

    def test_pronoun_fields_required(self):
        """Test the required parameter for pronoun_fields method (both bool and dict)"""
        self.individual.instanceName = "test_individual"
        self.individual.pronoun_prefer_self_described_label = "Something else"
        self.individual.pronoun_unknown_label = "Unknown"
        self.individual.pronoun_self_described_label = "Self described pronouns"
        self.individual.pronouns_label = "Self described pronouns"
        self.individual.pronoun_prefer_not_to_say_label = "Prefer not to say"

        # Test with boolean required parameter (existing behavior)
        fields = self.individual.pronoun_fields(
            required=True, choices=[{"They/them/theirs": "they/them/theirs"}]
        )
        pronoun_field = fields[0]
        self.assertEqual(pronoun_field["required"], True)

        # Test with boolean required parameter = False
        fields = self.individual.pronoun_fields(
            required=False, choices=[{"They/them/theirs": "they/them/theirs"}]
        )
        pronoun_field = fields[0]
        self.assertEqual(pronoun_field["required"], False)

        # Test with dictionary required parameter (new behavior)
        fields = self.individual.pronoun_fields(
            required={"test_individual.pronouns": True},
            choices=[{"They/them/theirs": "they/them/theirs"}],
        )
        pronoun_field = fields[0]
        self.assertEqual(pronoun_field["required"], True)

        # Test with dictionary required parameter for different field
        fields = self.individual.pronoun_fields(
            required={"test_individual.pronouns_self_described": True},
            choices=[{"They/them/theirs": "they/them/theirs"}],
        )
        pronoun_field = fields[0]
        self_described_field = fields[1]
        self.assertEqual(
            pronoun_field["required"],
            False,
        )  # First field should still be False
        self.assertEqual(self_described_field["required"], True)

    def test_language_fields_required(self):
        """Test the required parameter for language_fields method"""
        self.individual.instanceName = "test_individual"
        self.individual.language_other_label = "Other language"
        self.individual.language_label = "Language"

        # Test without required parameter
        fields = self.individual.language_fields()
        language_field = fields[0]
        self.assertNotIn(
            "required", language_field
        )  # Should not have required by default

        # Test with required parameter
        fields = self.individual.language_fields(
            required={"test_individual.language": True}
        )
        language_field = fields[0]
        self.assertEqual(language_field["required"], True)

        # Test other language field
        fields = self.individual.language_fields(
            required={"test_individual.language_other": False}
        )
        other_field = fields[1]
        self.assertEqual(other_field["required"], False)


class test_get_visible_al_nav_items(unittest.TestCase):
    def test_case_1(self):
        data = [
            "Selecting_Legal_Category",
            {"personal_injury": "Gather Evidence", "hidden": False},
            {"divorce": "Collect Financial Documents", "hidden": False},
            {
                "business_dispute": [
                    "Interview Witnesses",
                    {"subtask": "Document Communication", "hidden": False},
                ]
            },
        ]
        expected = [
            "Selecting_Legal_Category",
            {"personal_injury": "Gather Evidence"},
            {"divorce": "Collect Financial Documents"},
            {
                "business_dispute": [
                    "Interview Witnesses",
                    {"subtask": "Document Communication"},
                ]
            },
        ]
        self.assertEqual(get_visible_al_nav_items(data), expected)

    def test_case_2(self):
        data = [
            "Drafting_Documents",
            {"pre_nup": "List Assets"},
            "Finding_Legal_Representative",
            {
                "business_formation": [
                    "Choose Business Type",
                    {"subtask": "Decide Ownership Structure", "hidden": True},
                ]
            },
            {"real_estate": "Draft Lease Agreement", "hidden": True},
        ]
        expected = [
            "Drafting_Documents",
            {"pre_nup": "List Assets"},
            "Finding_Legal_Representative",
            {"business_formation": ["Choose Business Type"]},
        ]
        self.assertEqual(get_visible_al_nav_items(data), expected)

    def test_case_3(self):
        data = [
            "Negotiating_Terms",
            "Reviewing_Contracts",
            {
                "estate_planning": [
                    "Draft Will",
                    {"subtask": "Designate Beneficiaries", "hidden": False},
                    {"subtask": "Determine Power of Attorney", "hidden": False},
                ]
            },
        ]
        expected = [
            "Negotiating_Terms",
            "Reviewing_Contracts",
            {
                "estate_planning": [
                    "Draft Will",
                    {"subtask": "Designate Beneficiaries"},
                    {"subtask": "Determine Power of Attorney"},
                ]
            },
        ]
        self.assertEqual(get_visible_al_nav_items(data), expected)

    def test_case_4(self):
        data = [
            {"employment_law": "Understand Employee Rights", "hidden": False},
            "Preparing_for_Court",
            {
                "criminal_defense": [
                    "Know Your Rights",
                    {"subtask": "Hire Defense Attorney", "hidden": True},
                ]
            },
        ]
        expected = [
            {"employment_law": "Understand Employee Rights"},
            "Preparing_for_Court",
            {"criminal_defense": ["Know Your Rights"]},
        ]
        self.assertEqual(get_visible_al_nav_items(data), expected)


class test_demographic_fields(unittest.TestCase):
    def setUp(self):
        self.individual = ALIndividual()
        self.individual.instanceName = "test_person"
        
        # Mock template attributes for demographic fields
        self.individual.race_ethnicity_label = "Race and ethnicity"
        self.individual.race_ethnicity_other_label = "Please specify"
        self.individual.race_ethnicity_help_text = "You may select more than one category that applies to you."
        self.individual.age_range_label = "Age range"
        self.individual.age_range_help_text = "Select the age range that applies to you."
        self.individual.income_range_label = "Household income range"
        self.individual.income_range_help_text = "Select the range that best describes your household's total income before taxes in the last 12 months."
        self.individual.occupation_label = "Occupation"
        self.individual.occupation_other_label = "Please specify your occupation"
        self.individual.occupation_help_text = "Select the category that best describes your current work or situation."

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_race_and_ethnicity_fields_basic(self, mock_value):
        """Test basic race_and_ethnicity_fields functionality"""
        mock_value.return_value = [
            {"American Indian or Alaska Native": "american_indian_alaska_native"},
            {"Asian": "asian"},
            {"White": "white"},
            {"Other": "other"},
            {"Prefer not to say": "prefer_not_to_say"},
        ]

        fields = self.individual.race_and_ethnicity_fields()

        # Should return 2 fields: the main field and the "other" text field
        self.assertEqual(len(fields), 2)

        # Check main field structure
        main_field = fields[0]
        self.assertEqual(main_field["label"], "Race and ethnicity")
        self.assertEqual(main_field["field"], "test_person.race_ethnicity")
        self.assertEqual(main_field["datatype"], "checkboxes")
        self.assertIsInstance(main_field["choices"], list)

        # Check "other" field structure
        other_field = fields[1]
        self.assertEqual(other_field["field"], "test_person.race_ethnicity_other")
        self.assertIn("show if", other_field)

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_age_range_fields_basic(self, mock_value):
        """Test basic age_range_fields functionality"""
        mock_value.return_value = [
            {"Under 18": "under_18"},
            {"25-34": "25_34"},
            {"Prefer not to say": "prefer_not_to_say"},
        ]

        fields = self.individual.age_range_fields()

        # Should return 1 field
        self.assertEqual(len(fields), 1)

        # Check field structure
        field = fields[0]
        self.assertEqual(field["label"], "Age range")
        self.assertEqual(field["field"], "test_person.age_range")
        self.assertEqual(field["input type"], "radio")
        self.assertIsInstance(field["choices"], list)

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_income_range_fields_basic(self, mock_value):
        """Test basic income_range_fields functionality"""
        mock_value.return_value = [
            {"Less than $15,000": "under_15k"},
            {"$50,000 - $74,999": "50k_74k"},
            {"Prefer not to say": "prefer_not_to_say"},
        ]

        fields = self.individual.income_range_fields()

        # Should return 1 field
        self.assertEqual(len(fields), 1)

        # Check field structure
        field = fields[0]
        self.assertEqual(field["label"], "Household income range")
        self.assertEqual(field["field"], "test_person.income_range")
        self.assertEqual(field["input type"], "radio")
        self.assertIsInstance(field["choices"], list)

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_occupation_fields_basic(self, mock_value):
        """Test basic occupation_fields functionality"""
        mock_value.return_value = [
            {"Service": "service"},
            {"Student": "student"},
            {"Other": "other"},
            {"Prefer not to say": "prefer_not_to_say"},
        ]

        fields = self.individual.occupation_fields()

        # Should return 2 fields: the main field and the "other" text field
        self.assertEqual(len(fields), 2)

        # Check main field structure
        main_field = fields[0]
        self.assertEqual(main_field["label"], "Occupation")
        self.assertEqual(main_field["field"], "test_person.occupation")
        self.assertEqual(main_field["input type"], "radio")
        self.assertIsInstance(main_field["choices"], list)

        # Check "other" field structure
        other_field = fields[1]
        self.assertEqual(other_field["field"], "test_person.occupation_other")
        self.assertIn("show if", other_field)

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_demographic_fields_with_show_help(self, mock_value):
        """Test that show_help parameter adds help text"""
        mock_value.return_value = [{"Test": "test"}]

        fields = self.individual.race_and_ethnicity_fields(show_help=True)
        self.assertIn("help", fields[0])

        fields = self.individual.age_range_fields(show_help=True)
        self.assertIn("help", fields[0])

        fields = self.individual.income_range_fields(show_help=True)
        self.assertIn("help", fields[0])

        fields = self.individual.occupation_fields(show_help=True)
        self.assertIn("help", fields[0])

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_demographic_fields_with_show_if(self, mock_value):
        """Test that show_if parameter is applied"""
        mock_value.return_value = [{"Test": "test"}]
        show_if_condition = {"variable": "some_condition", "is": "true"}

        fields = self.individual.race_and_ethnicity_fields(show_if=show_if_condition)
        self.assertEqual(fields[0]["show if"], show_if_condition)

        fields = self.individual.age_range_fields(show_if=show_if_condition)
        self.assertEqual(fields[0]["show if"], show_if_condition)

        fields = self.individual.income_range_fields(show_if=show_if_condition)
        self.assertEqual(fields[0]["show if"], show_if_condition)

        fields = self.individual.occupation_fields(show_if=show_if_condition)
        self.assertEqual(fields[0]["show if"], show_if_condition)

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_demographic_fields_with_required(self, mock_value):
        """Test that required parameter is applied"""
        mock_value.return_value = [{"Test": "test"}]
        required_dict = {"test_person.race_ethnicity": True}

        fields = self.individual.race_and_ethnicity_fields(required=required_dict)
        # Find the main field
        main_field = next(
            f
            for f in fields
            if "race_ethnicity" in f["field"] and "other" not in f["field"]
        )
        self.assertEqual(main_field["required"], True)

        fields = self.individual.age_range_fields(
            required={"test_person.age_range": False}
        )
        self.assertEqual(fields[0]["required"], False)

        fields = self.individual.income_range_fields(
            required={"test_person.income_range": True}
        )
        self.assertEqual(fields[0]["required"], True)

        fields = self.individual.occupation_fields(
            required={"test_person.occupation": False}
        )
        main_field = next(
            f
            for f in fields
            if "occupation" in f["field"] and "other" not in f["field"]
        )
        self.assertEqual(main_field["required"], False)

    def test_demographic_fields_with_custom_choices(self):
        """Test that custom choices parameter works"""
        custom_choices = [{"Custom Option": "custom_value"}]

        fields = self.individual.race_and_ethnicity_fields(choices=custom_choices)
        self.assertEqual(fields[0]["choices"], custom_choices)

        fields = self.individual.age_range_fields(choices=custom_choices)
        self.assertEqual(fields[0]["choices"], custom_choices)

        fields = self.individual.income_range_fields(choices=custom_choices)
        self.assertEqual(fields[0]["choices"], custom_choices)

        fields = self.individual.occupation_fields(choices=custom_choices)
        self.assertEqual(fields[0]["choices"], custom_choices)

    @patch("docassemble.AssemblyLine.al_general.value")
    def test_demographic_fields_with_maxlengths(self, mock_value):
        """Test that maxlengths parameter is applied"""
        mock_value.return_value = [{"Test": "test"}]
        maxlengths = {"test_person.race_ethnicity_other": 100}

        fields = self.individual.race_and_ethnicity_fields(maxlengths=maxlengths)
        # Find the "other" field
        other_field = next(f for f in fields if "race_ethnicity_other" in f["field"])
        self.assertEqual(other_field["maxlength"], 100)


if __name__ == "__main__":
    unittest.main()

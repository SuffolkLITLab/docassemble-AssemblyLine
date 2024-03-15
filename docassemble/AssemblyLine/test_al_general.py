import unittest
from .al_general import ALIndividual, ALAddress, get_visible_al_nav_items
from unittest.mock import Mock
from docassemble.base.util import DADict, DAAttributeError


class test_aladdress(unittest.TestCase):
    def setUp(self):
        self.addr = ALAddress()

    def test_empty_is_empty(self):
        addr = ALAddress(address="", city="")
        self.assertEqual(addr.on_one_line(), "")

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
        # Should raise an exception
        with self.assertRaises(DAAttributeError):
            self.individual.pronoun_objective()

    def test_name_methods(self):
        self.individual.name.first = "John"
        self.individual.name.middle = "Jacob"
        self.individual.name.last = "Jingleheimer"

        self.assertEqual(self.individual.name_full(), "John Jacob Jingleheimer")
        self.assertEqual(self.individual.name_initials(), "John J. Jingleheimer")
        self.assertEqual(self.individual.name_short(), "John Jingleheimer")


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


if __name__ == "__main__":
    unittest.main()

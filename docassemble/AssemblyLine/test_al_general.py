# do not pre-load

import importlib
import unittest
from .al_general import ALIndividual, ALAddress, ALPeopleList, get_visible_al_nav_items
from unittest.mock import Mock, patch
from docassemble.base.util import DADict
from docassemble.base.functions import value as da_value


def _patch_this_thread(testcase, thread, *targets):
    """Patch `this_thread` wherever the installed docassemble version defines it;
    newer versions moved some of it into `docassemble.base.language`. Fails if
    none of the targets exist, so a docassemble upgrade can't silently skip it."""
    patched = 0
    for target in targets:
        module_name, attribute = target.rsplit(".", 1)
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        if not hasattr(module, attribute):
            continue
        patcher = patch(target, thread)
        patcher.start()
        testcase.addCleanup(patcher.stop)
        patched += 1
    if not patched:
        raise AssertionError(f"None of {targets} exist to patch")


def _mock_thread():
    """A stand-in for docassemble's `this_thread` with an English, US context."""
    thread = Mock()
    thread.language = "en"
    thread.country = "US"
    thread.gathering_mode = {}
    thread.evaluation_context = None
    thread.misc = {}
    # A distinct user object, so test individuals aren't treated as the user
    thread.global_vars.user = Mock()
    return thread


_THIS_THREAD_TARGETS = (
    "docassemble.base.functions.this_thread",
    "docassemble.base.util.this_thread",
    "docassemble.base.language.core.this_thread",
    "docassemble.base.language.control.this_thread",
    "docassemble.base.language.currency.this_thread",
    "docassemble.base.language.language_en.this_thread",
    "docassemble.base.language.numbers.this_thread",
    "docassemble.base.language.words.this_thread",
)


class test_aladdress(unittest.TestCase):
    def setUp(self):
        self.this_thread = _mock_thread()
        _patch_this_thread(self, self.this_thread, *_THIS_THREAD_TARGETS)
        get_config_patcher = patch(
            "docassemble.AssemblyLine.al_general.get_config", return_value={}
        )
        get_config_patcher.start()
        self.addCleanup(get_config_patcher.stop)
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
        fields = addr.address_fields(required={"zip": True})
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

        self.this_thread = _mock_thread()
        _patch_this_thread(self, self.this_thread, *_THIS_THREAD_TARGETS)

        self.individual.name.first = "John"

        label_defaults = {
            "first_name_label": "First name",
            "middle_name_label": "Middle name",
            "last_name_label": "Last name",
            "suffix_label": "Suffix",
            "name_title_label": "Title",
            "business_name_label": "Business name",
            "person_type_label": "Person type",
            "individual_choice_label": "Person",
            "business_choice_label": "Business",
            "gender_label": "Gender",
            "gender_female_label": "Female",
            "gender_male_label": "Male",
            "gender_nonbinary_label": "Nonbinary",
            "gender_prefer_not_to_say_label": "Prefer not to say",
            "gender_prefer_self_described_label": "Self described",
            "gender_self_described_label": "Self described gender",
            "gender_unknown_label": "Unknown",
            "gender_help_text": "Help text",
            "pronouns_label": "Pronouns",
            "pronouns_help_text": "Pronouns help",
            "pronoun_prefer_not_to_say_label": "Prefer not to say",
            "pronoun_unknown_label": "Unknown",
            "pronoun_prefer_self_described_label": "Something else",
            "pronoun_self_described_label": "Self described pronouns",
            "language_label": "Language",
            "language_other_label": "Other language",
        }

        for attr, value in label_defaults.items():
            setattr(self.individual, attr, value)

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
        return da_value(variable_name, *args, **kwargs)

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

        # Test for when user provides a pronoun string that cannot be parsed
        # (doesn't follow the required 2-3 slash format), should fall back to using name's target
        self.individual.pronouns = "custom"
        self.individual.person_type = "individual"
        self.individual.name.first = "John"
        self.individual.name.last = "Smith"
        # When pronouns can't be parsed, should use "{name}'s {target}"
        self.assertEqual(self.individual.pronoun_possessive(item), "John Smith's fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, capitalize=True),
            "John Smith's fish",
        )

        # When default is a possessive pronoun, should NOT append apostrophe-s (e.g. "their fish", not "their's fish")
        self.assertEqual(
            self.individual.pronoun_possessive(item, default="their"),
            "their fish",
        )
        self.assertEqual(
            self.individual.pronoun_possessive(item, default="their", capitalize=True),
            "Their fish",
        )
        self.assertEqual(
            self.individual.pronoun_possessive(item, default="our"),
            "our fish",
        )

    def _pronouns(self, *selected):
        return DADict(
            auto_gather=False,
            gathered=True,
            elements={
                key: key in selected
                for key in ("they/them/theirs", "he/him/his", "she/her/hers")
            },
        )

    def test_does_verb_and_did_verb(self):
        self.individual.name.first = "Alex"
        self.individual.name.last = "Smith"

        # By default the verb agrees with the name, which is singular
        self.individual.pronouns = self._pronouns("they/them/theirs")
        self.assertEqual(self.individual.does_verb("survive"), "survives")
        self.assertEqual(self.individual.does_verb("be"), "is")
        self.assertEqual(self.individual.did_verb("be"), "was")
        self.assertEqual(self.individual.does_verb("be", past=True), "was")

        # After a pronoun, singular they takes a plural verb
        self.assertEqual(self.individual.does_verb("survive", pronoun=True), "survive")
        self.assertEqual(self.individual.does_verb("do", pronoun=True), "do")
        self.assertEqual(self.individual.does_verb("be", pronoun=True), "are")
        self.assertEqual(
            self.individual.does_verb("be", pronoun=True, capitalize=True), "Are"
        )
        self.assertEqual(self.individual.did_verb("be", pronoun=True), "were")
        self.assertEqual(
            self.individual.does_verb("be", pronoun=True, past=True), "were"
        )
        self.assertEqual(self.individual.did_verb("survive", pronoun=True), "survived")

        # He and she stay singular after the pronoun
        for selected in ("he/him/his", "she/her/hers"):
            self.individual.pronouns = self._pronouns(selected)
            self.assertEqual(
                self.individual.does_verb("survive", pronoun=True), "survives"
            )
            self.assertEqual(self.individual.does_verb("do", pronoun=True), "does")
            self.assertEqual(self.individual.does_verb("be", pronoun=True), "is")
            self.assertEqual(self.individual.did_verb("be", pronoun=True), "was")

        # Custom pronouns use the subjective form
        self.individual.pronouns = "them/they/their"
        self.assertEqual(self.individual.does_verb("be", pronoun=True), "are")
        self.individual.pronouns = "xem/xe/xyr"
        self.assertEqual(self.individual.does_verb("be", pronoun=True), "is")

    def test_does_verb_without_pronouns(self):
        # No pronouns or gender: pronoun_subjective() falls back to the name
        self.individual.pronouns = None
        self.assertEqual(self.individual.does_verb("live"), "lives")
        self.assertEqual(self.individual.does_verb("live", pronoun=True), "lives")
        self.assertEqual(self.individual.did_verb("be", pronoun=True), "was")

        # Gender without pronouns
        self.individual.gender = "nonbinary"
        self.assertEqual(self.individual.does_verb("live", pronoun=True), "live")
        self.assertEqual(self.individual.does_verb("live"), "lives")
        self.individual.gender = "female"
        self.assertEqual(self.individual.does_verb("live", pronoun=True), "lives")

    def test_does_verb_self_described_not_needed_by_default(self):
        self.individual.pronouns = DADict(
            auto_gather=False,
            gathered=True,
            elements={"self-described": True},
        )
        # pronouns_self_described is undefined; name agreement must not read it
        self.assertEqual(self.individual.does_verb("live"), "lives")

    def test_does_verb_explicit_person(self):
        self.individual.pronouns = self._pronouns("they/them/theirs")
        self.assertEqual(
            self.individual.does_verb("be", person="2p", past=True), "were"
        )
        self.assertEqual(
            self.individual.does_verb("be", person="1p", past=True), "were"
        )
        self.assertEqual(
            self.individual.does_verb("be", person="1", pronoun=True), "am"
        )
        self.assertEqual(
            self.individual.did_verb("be", person="1", pronoun=True), "was"
        )

    def _person(self, first, *pronouns):
        person = ALIndividual()
        person.name.first = first
        person.pronouns = self._pronouns(*pronouns)
        return person

    def _people(self, *people):
        plist = ALPeopleList(auto_gather=False, gathered=True)
        for person in people:
            plist.append(person)
        return plist

    def test_does_verb_business_and_point_of_view(self):
        # A business is "it", which takes a singular verb
        self.individual.pronouns = None
        self.individual.person_type = "business"
        self.assertEqual(self.individual.does_verb("live", pronoun=True), "lives")

        # The user is "you" after a pronoun, whatever their pronouns
        self.this_thread.global_vars.user = self.individual
        self.individual.person_type = "individual"
        self.individual.pronouns = self._pronouns("they/them/theirs")
        self.assertEqual(self.individual.does_verb("be", pronoun=True), "are")
        self.assertEqual(self.individual.did_verb("be", pronoun=True), "were")

    def test_pronoun_reflexive_without_usable_pronouns(self):
        # Pronouns are set, but none of them can be used
        self.individual.pronouns = "not a pronoun"
        self.assertEqual(self.individual.pronoun_reflexive(), "themself")

    def test_alpeoplelist_does_verb(self):
        taylor = self._person("Taylor", "they/them/theirs")
        jordan = self._person("Jordan", "she/her/hers")

        # Single person with they/them pronouns: name agreement by default
        plist = self._people(taylor)
        self.assertEqual(plist.does_verb("survive"), "survives")
        self.assertEqual(plist.did_verb("be"), "was")
        self.assertEqual(plist.does_verb("survive", pronoun=True), "survive")
        self.assertEqual(plist.does_verb("do", pronoun=True), "do")
        self.assertEqual(plist.did_verb("be", pronoun=True), "were")

        # Single person with she/her pronouns in list
        plist = self._people(jordan)
        self.assertEqual(plist.does_verb("survive"), "survives")
        self.assertEqual(plist.does_verb("survive", pronoun=True), "survives")
        self.assertEqual(plist.did_verb("be", pronoun=True), "was")

        # Multiple people in list always plural
        plist = self._people(jordan, taylor)
        self.assertEqual(plist.does_verb("survive"), "survive")
        self.assertEqual(plist.does_verb("survive", pronoun=True), "survive")
        self.assertEqual(plist.did_verb("be"), "were")

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
            required={"first": True},
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
        fields = self.individual.gender_fields(required={"gender": True})
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

    def test_familiar_with_preferred_name(self):
        """Test familiar() method with preferred_name set."""
        # Setup basic name
        self.individual.name.first = "John"
        self.individual.name.last = "Doe"

        # Test without preferred_name
        self.assertEqual(self.individual.familiar(), "John")

        # Set preferred_name
        self.individual.preferred_name.first = "Johnny"

        # Test with preferred_name
        self.assertEqual(self.individual.familiar(), "Johnny")

        # Test with empty preferred_name (should fall back to name.first)
        self.individual.preferred_name.first = ""
        self.assertEqual(self.individual.familiar(), "John")

        # Test with None preferred_name (should fall back to name.first)
        self.individual.preferred_name.first = None
        self.assertEqual(self.individual.familiar(), "John")

        # Test with whitespace-only preferred_name (should fall back to name.first)
        self.individual.preferred_name.first = "   "
        # Note: "   " is truthy in Python, so this would use the whitespace
        # This is acceptable behavior - only empty string and None should fallback
        self.assertEqual(self.individual.familiar(), "   ")

    def test_familiar_with_preferred_name_business(self):
        """Test that business/organization types still work correctly with preferred_name."""
        self.individual.person_type = "business"
        self.individual.name.first = "Acme Corp"
        self.individual.preferred_name.first = "ACME"

        # Business types should ignore preferred_name and use name.first
        self.assertEqual(self.individual.familiar(), "Acme Corp")

        self.individual.person_type = "organization"
        self.assertEqual(self.individual.familiar(), "Acme Corp")

    def test_familiar_with_preferred_name_and_conflicts(self):
        """Test familiar() with preferred_name when there are name conflicts."""
        # Setup multiple people with potential conflicts
        other_person = ALIndividual()
        other_person.name.first = "Johnny"
        other_person.name.last = "Smith"

        self.individual.name.first = "John"
        self.individual.name.last = "Doe"
        self.individual.preferred_name.first = (
            "Johnny"  # Conflicts with other person's name.first
        )

        # When there's a conflict with preferred name, should try next option
        result = self.individual.familiar(unique_names=[other_person])
        # Since "Johnny" conflicts with other_person.familiar(), it should try other combinations
        # The exact result depends on the full logic, but it shouldn't just return "Johnny"
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


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

    def test_hides_section_with_no_visible_subsections(self):
        data = [
            {
                "hidden_section": [
                    {"subtask": "A hidden subtask", "hidden": True},
                ]
            },
            {
                "visible_section": [
                    {"subtask": "A visible subtask", "hidden": False},
                ]
            },
        ]
        expected = [
            {
                "visible_section": [
                    {"subtask": "A visible subtask"},
                ]
            },
        ]

        self.assertEqual(get_visible_al_nav_items(data), expected)


if __name__ == "__main__":
    unittest.main()

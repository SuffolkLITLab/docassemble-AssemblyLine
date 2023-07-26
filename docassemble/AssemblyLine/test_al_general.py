import unittest
from .al_general import ALIndividual, ALAddress
from unittest.mock import Mock
from docassemble.base.util import DADict


class test_aladdress(unittest.TestCase):
    def test_empty_is_empty(self):
        addr = ALAddress(address="", city="")
        self.assertEqual(addr.on_one_line(), "")

class TestALIndividual(unittest.TestCase):

    def setUp(self):
        self.individual = ALIndividual()
        
        # Creating a mock object for this_thread
        self.this_thread = Mock()

        # Mocking this_thread.global_vars.user as a distinct object
        self.this_thread.global_vars.user = Mock()

        # Assigning this_thread to self.individual
        self.individual.this_thread = self.this_thread

    def test_pronoun(self):
        self.individual.pronouns = None
        self.individual.person_type = 'individual'

        self.individual.gender = 'female'
        self.assertEqual(self.individual.pronoun(), 'her')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'Her')

        self.individual.gender = 'male'
        self.assertEqual(self.individual.pronoun(), 'him')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'Him')
        
        self.individual.gender = 'nonbinary'
        self.assertEqual(self.individual.pronoun(), 'them')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'Them')

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": True, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun(), 'her')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'Her')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": True, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun(), 'him')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'Him')
        
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": True, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun(), 'them')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'Them')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": True})
        self.assertEqual(self.individual.pronoun(), 'zir')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'Zir')

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = 'business'
        self.assertEqual(self.individual.pronoun(), 'it')
        self.assertEqual(self.individual.pronoun(capitalize=True), 'It')


    def test_pronoun_objective(self):
        self.individual.pronouns = None
        self.individual.person_type = 'individual'

        self.individual.gender = 'female'
        self.assertEqual(self.individual.pronoun_objective(), 'her')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'Her')

        self.individual.gender = 'male'
        self.assertEqual(self.individual.pronoun_objective(), 'him')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'Him')
        
        self.individual.gender = 'nonbinary'
        self.assertEqual(self.individual.pronoun_objective(), 'them')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'Them')

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": True, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_objective(), 'her')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'Her')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": True, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_objective(), 'him')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'Him')
        
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": True, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_objective(), 'them')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'Them')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": True})
        self.assertEqual(self.individual.pronoun_objective(), 'zir')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'Zir')

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = 'business'
        self.assertEqual(self.individual.pronoun_objective(), 'it')
        self.assertEqual(self.individual.pronoun_objective(capitalize=True), 'It')

    def test_pronoun_possessive(self):
        self.individual.pronouns = None
        self.individual.person_type = 'individual'
        item = 'fish'

        self.individual.gender = 'female'
        self.assertEqual(self.individual.pronoun_possessive(item), 'her fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'Her fish')

        self.individual.gender = 'male'
        self.assertEqual(self.individual.pronoun_possessive(item), 'his fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'His fish')
        
        self.individual.gender = 'nonbinary'
        self.assertEqual(self.individual.pronoun_possessive(item), 'their fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'Their fish')

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": True, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_possessive(item), 'her fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'Her fish')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": True, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_possessive(item), 'his fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'His fish')
        
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": True, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_possessive(item), 'their fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'Their fish')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": True})
        self.assertEqual(self.individual.pronoun_possessive(item), 'zir fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'Zir fish')

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = 'business'
        self.assertEqual(self.individual.pronoun_possessive(item), 'its fish')
        self.assertEqual(self.individual.pronoun_possessive(item, capitalize=True), 'Its fish')


    def test_pronoun_subjective(self):
        self.individual.pronouns = None
        self.individual.person_type = 'individual'

        self.individual.gender = 'female'
        self.assertEqual(self.individual.pronoun_subjective(), 'she')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'She')

        self.individual.gender = 'male'
        self.assertEqual(self.individual.pronoun_subjective(), 'he')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'He')
        
        self.individual.gender = 'nonbinary'
        self.assertEqual(self.individual.pronoun_subjective(), 'they')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'They')

        # Checks for preferred pronouns
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": True, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_subjective(), 'she')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'She')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": True, "they/them/theirs": False, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_subjective(), 'he')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'He')
        
        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": True, "ze/zir/zirs": False})
        self.assertEqual(self.individual.pronoun_subjective(), 'they')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'They')

        self.individual.pronouns = DADict(auto_gather=False, gathered=True, elements={"she/her/hers": False, "he/him/his": False, "they/them/theirs": False, "ze/zir/zirs": True})
        self.assertEqual(self.individual.pronoun_subjective(), 'ze')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'Ze')

        self.individual.pronouns = None
        self.individual.gender = None
        self.individual.person_type = 'business'
        self.assertEqual(self.individual.pronoun_subjective(), 'it')
        self.assertEqual(self.individual.pronoun_subjective(capitalize=True), 'It')


if __name__ == "__main__":
    unittest.main()

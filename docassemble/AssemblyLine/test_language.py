import unittest
from unittest.mock import patch
from .language import (
    get_language_list_dropdown,
    get_language_list_dropdown_item,
    get_tuples,
    get_language_list,
    get_language_list_item,
)
import pycountry
import yaml
import os


class TestLanguage(unittest.TestCase):
    def setUp(self):
        self.language_codes = ["en", "fr"]
        self.mock_url_action = patch(
            "docassemble.AssemblyLine.language.url_action", return_value="mocked_url"
        )
        self.mocked_url_action = self.mock_url_action.start()

        # Define relative directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.relative_path = os.path.join(
            current_dir, "data", "sources", "languages.yml"
        )

    def tearDown(self):
        self.mock_url_action.stop()

    def test_get_tuples(self):
        result = get_tuples(self.language_codes, languages_path=self.relative_path)

        expected_result = [("English", "en"), ("Français", "fr")]

        self.assertEqual(result, expected_result)

    def test_get_language_list_dropdown(self):
        result = get_language_list_dropdown(
            self.language_codes, languages_path=self.relative_path
        )
        self.assertIn('<li class="nav-item dropdown">', result)
        self.assertIn('<a class="dropdown-item" href="mocked_url">Français</a>', result)

    def test_get_language_list_dropdown_item(self):
        language_tuple = ("English", "en")
        result = get_language_list_dropdown_item(language_tuple)
        self.assertIn('<a class="dropdown-item" href="mocked_url">English</a>', result)

    def test_get_language_list(self):
        result = get_language_list(
            lang_codes=self.language_codes, languages_path=self.relative_path
        )
        self.assertIn('<ul class="list-inline">', result)
        self.assertIn('<a target="_self" href="mocked_url">Français</a>', result)

    def test_get_language_list_item(self):
        language_tuple = ("English", "en")
        result = get_language_list_item(language_tuple)
        self.assertIn(
            '<li class="list-inline-item"><a target="_self" href="mocked_url">English</a></li>',
            result,
        )


if __name__ == "__main__":
    unittest.main()

# do not pre-load

import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

import yaml


class TestFeedbackForm(unittest.TestCase):
    def setUp(self):
        visual = Path(__file__).parent / "data" / "questions" / "al_visual.yml"
        blocks = yaml.safe_load_all(visual.read_text(encoding="utf-8"))
        self.code = next(
            block["code"] for block in blocks
            if isinstance(block, dict) and "feedback_form =" in block.get("code", "")
        )
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "feedback.yml"

    def select(self, package, resolved_path):
        resolver = Mock(return_value=resolved_path)
        functions = ModuleType("docassemble.base.functions")
        functions.package_question_filename = resolver
        namespace = {"package_name": package}
        with patch.dict("sys.modules", {"docassemble.base.functions": functions}):
            exec(compile(self.code, "al_visual.yml feedback_form", "exec"), namespace)
        return namespace["feedback_form"], resolver

    def test_installed_package_feedback_is_preferred(self):
        self.path.write_text("question: Feedback\n", encoding="utf-8")
        chosen, resolver = self.select("docassemble.LocalForms", str(self.path))
        self.assertEqual(chosen, "docassemble.LocalForms:feedback.yml")
        resolver.assert_called_once_with("docassemble.LocalForms:feedback.yml")

    def test_missing_feedback_uses_assemblyline(self):
        for path in (None, str(self.path)):
            with self.subTest(path=path):
                chosen, _ = self.select("docassemble.LocalForms", path)
                self.assertEqual(chosen, "docassemble.AssemblyLine:feedback.yml")

    def test_directory_is_not_a_feedback_interview(self):
        self.path.mkdir()
        chosen, _ = self.select("docassemble.LocalForms", str(self.path))
        self.assertEqual(chosen, "docassemble.AssemblyLine:feedback.yml")

    def test_playground_and_empty_package_keep_fallback(self):
        for package in (None, "", "docassemble.playground12", "docassemble.playground12Project"):
            with self.subTest(package=package):
                chosen, resolver = self.select(package, str(self.path))
                self.assertEqual(chosen, "docassemble.AssemblyLine:feedback.yml")
                resolver.assert_not_called()

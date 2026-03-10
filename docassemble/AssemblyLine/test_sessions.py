# do not pre-load

import json
import os
import tempfile
import unittest
from unittest.mock import patch


def _ensure_da_test_config() -> None:
    """Docassemble modules require a config file path during import."""
    if os.environ.get("DA_CONFIG_FILE"):
        return
    config_path = os.path.join(tempfile.gettempdir(), "assemblyline-test-config.yml")
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("secretkey: testing-secret\n")
            f.write("url root: http://localhost\n")
    os.environ["DA_CONFIG_FILE"] = config_path


_ensure_da_test_config()

from . import sessions


class TestAnswerSetImportSafety(unittest.TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.samples_dir = os.path.join(
            current_dir, "data", "sources", "answer_set_import_samples"
        )

    def _sample(self, filename: str) -> str:
        with open(os.path.join(self.samples_dir, filename), "r", encoding="utf-8") as f:
            return f.read()

    def test_parse_rejects_malformed_json_file(self):
        bad_json = self._sample("malformed_trailing_comma.json")
        with self.assertRaises(ValueError):
            sessions._parse_json_with_limits(bad_json, sessions._import_limits())

    def test_parse_rejects_dunder_object_key(self):
        bad_json = self._sample("malicious_dunder_key.json")
        with self.assertRaises(ValueError) as cm:
            sessions._parse_json_with_limits(bad_json, sessions._import_limits())
        self.assertIn("forbidden key", str(cm.exception))

    def test_sanitize_filters_internal_key(self):
        bad_json = self._sample("malicious_internal_key.json")
        payload = sessions._parse_json_with_limits(bad_json, sessions._import_limits())
        accepted, report = sessions._sanitize_json_import_payload(payload)
        self.assertEqual(accepted, {"users_name": "Alex", "city": "Boston"})
        self.assertTrue(any(item["path"] == "_internal" for item in report["rejected"]))

    def test_parse_rejects_when_list_item_limit_exceeded(self):
        limits = sessions._import_limits()
        limits["max_list_items"] = 3
        payload = json.dumps({"names": ["a", "b", "c", "d"]})
        with self.assertRaises(ValueError) as cm:
            sessions._parse_json_with_limits(payload, limits)
        self.assertIn("too many items", str(cm.exception))

    @patch("docassemble.AssemblyLine.sessions.get_config")
    def test_sanitize_respects_allowlist(self, mock_get_config):
        mock_get_config.return_value = {
            "answer set import allowed variables": ["users_name"],
            "answer set import require signed": False,
        }
        payload = {
            "users_name": "Alex",
            "users_city": "Boston",
            "user_started_case": True,
        }

        accepted, report = sessions._sanitize_json_import_payload(payload)

        self.assertEqual(accepted, {"users_name": "Alex"})
        self.assertTrue(
            any(item["reason"] == "not in allowlist" for item in report["rejected"])
        )
        self.assertTrue(
            any(item["reason"] == "protected variable" for item in report["rejected"])
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_load_interview_json_partial_import_with_report(self, mock_set_variables):
        payload = json.dumps(
            {
                "users_name": "Alex",
                "user_started_case": True,
            }
        )

        result = sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()

        self.assertTrue(result)
        mock_set_variables.assert_called_once_with(
            {"users_name": "Alex"}, process_objects=False
        )
        self.assertIn("users_name", report["accepted"])
        self.assertTrue(
            any(item["path"] == "user_started_case" for item in report["rejected"])
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_load_interview_json_allows_object_graph_and_references(
        self, mock_set_variables
    ):
        object_json = self._sample("object_graph_with_reference.json")

        result = sessions.load_interview_json(object_json)
        report = sessions.get_last_import_report()

        self.assertTrue(result)
        args, kwargs = mock_set_variables.call_args
        self.assertIn("users", args[0])
        self.assertTrue(kwargs.get("process_objects"))
        users_obj = args[0]["users"]
        self.assertEqual(
            users_obj["_class"], "docassemble.AssemblyLine.al_general.ALPeopleList"
        )
        self.assertEqual(users_obj["elements"][0]["agent"]["instanceName"], "spouse")
        self.assertEqual(users_obj["elements"][0]["custom_text"], "notes")
        self.assertEqual(users_obj["elements"][0]["custom_float"], 1.25)
        self.assertIn("users", report["accepted"])
        self.assertTrue(report.get("contains_objects"))

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_load_interview_json_rejects_unknown_object_class(self, mock_set_variables):
        object_json = self._sample("object_graph_unknown_class.json")

        result = sessions.load_interview_json(object_json)
        report = sessions.get_last_import_report()

        self.assertFalse(result)
        mock_set_variables.assert_not_called()
        self.assertTrue(any(item["path"] == "users" for item in report["rejected"]))

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_load_interview_json_remaps_known_playground_classes(
        self, mock_set_variables
    ):
        object_json = self._sample("object_graph_playground_alias.json")

        result = sessions.load_interview_json(object_json)
        report = sessions.get_last_import_report()

        self.assertTrue(result)
        args, kwargs = mock_set_variables.call_args
        self.assertTrue(kwargs.get("process_objects"))
        users_obj = args[0]["users"]
        self.assertEqual(
            users_obj["_class"], "docassemble.AssemblyLine.al_general.ALPeopleList"
        )
        self.assertEqual(
            users_obj["object_type"]["name"],
            "docassemble.AssemblyLine.al_general.ALIndividual",
        )
        self.assertEqual(
            users_obj["elements"][0]["_class"],
            "docassemble.AssemblyLine.al_general.ALIndividual",
        )
        self.assertEqual(
            users_obj["elements"][0]["name"]["_class"],
            "docassemble.base.util.IndividualName",
        )
        self.assertTrue(len(report.get("remapped_classes", [])) >= 1)

    def test_load_interview_json_returns_false_for_invalid_json(self):
        bad_json = self._sample("malformed_trailing_comma.json")

        result = sessions.load_interview_json(bad_json)
        report = sessions.get_last_import_report()

        self.assertFalse(result)
        self.assertTrue(any(item["path"] == "$" for item in report["rejected"]))

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_rejects_dunder_in_instance_name(self, mock_set_variables):
        payload = json.dumps(
            {
                "evil": {
                    "_class": "docassemble.base.util.DAObject",
                    "instanceName": "evil.__class__",
                }
            }
        )

        result = sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()

        self.assertFalse(result)
        mock_set_variables.assert_not_called()
        self.assertTrue(
            any("instanceName" in item.get("reason", "") for item in report["rejected"])
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_type_envelope_bypass(self, mock_set_variables):
        # Tries to bypass type envelope allowlisting but specifying an unauthorized class
        payload = json.dumps(
            {
                "evil_type": {
                    "_class": "type",
                    "name": "subprocess.Popen",
                }
            }
        )
        sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()
        self.assertTrue(
            any(
                item["path"] == "evil_type" and "not allowed" in item.get("reason", "")
                for item in report["rejected"]
            )
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_object_attr_dunder(self, mock_set_variables):
        # Tries to overwrite __globals__ via object attribute
        payload = json.dumps(
            {
                "users": {
                    "_class": "docassemble.base.util.DAObject",
                    "instanceName": "users",
                    "__globals__": {"evil": "code"},
                }
            }
        )
        sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()
        # the key check fails at structural parsing phase before getting to sanitizer object validation,
        # which means the entire document is rejected with path '$'
        self.assertTrue(
            any(
                item["path"] == "$"
                and "forbidden key '__globals__'" in item.get("reason", "")
                for item in report["rejected"]
            )
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_deep_nesting(self, mock_set_variables):
        # Depth limit bypass attempt
        payload = {"bomb": "a"}
        for i in range(45):
            payload = {"bomb": payload}

        with self.assertRaises(ValueError) as cm:
            sessions._parse_json_with_limits(
                json.dumps(payload), sessions._import_limits()
            )
        self.assertIn("too deep", str(cm.exception))

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_massive_string(self, mock_set_variables):
        # Tries to eat memory with huge string
        payload = {"big_string": "A" * 300000}
        with self.assertRaises(ValueError) as cm:
            sessions._parse_json_with_limits(
                json.dumps(payload), sessions._import_limits()
            )
        self.assertIn("too long", str(cm.exception))

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_number_overflow(self, mock_set_variables):
        # Tries to DOS via large float parsing/math
        payload = {"big_num": 1e20}
        with self.assertRaises(ValueError) as cm:
            sessions._parse_json_with_limits(
                json.dumps(payload), sessions._import_limits()
            )
        self.assertIn("outside allowed range", str(cm.exception))

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_newline_in_var_name(self, mock_set_variables):
        # Exploits ^/$ regex bugs with newlines
        payload = json.dumps(
            {
                "users\nname": "evil",
            }
        )
        sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()
        self.assertTrue(
            any(
                item["path"] == "users\nname" and "unsafe" in item.get("reason", "")
                for item in report["rejected"]
            )
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_protected_import_vars(self, mock_set_variables):
        # Tries to overwrite crucial DA modules
        payload = json.dumps(
            {"server": "hacked", "daconfig": "hacked", "pickle": "hacked"}
        )
        sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()
        for var in ["server", "daconfig", "pickle"]:  # handled in _safe_variable_name
            self.assertTrue(
                any(
                    item["path"] == var
                    and "unsafe variable name" in item.get("reason", "")
                    for item in report["rejected"]
                )
            )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_unicode_normalization_bypass(self, mock_set_variables):
        # Tries to bypass variable allowlist with homoglyphs
        # 'ＯＳ' is FULLWIDTH LATIN CAPITAL LETTER O and S
        payload = json.dumps(
            {
                "ＯＳ": "evil",
            }
        )
        sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()
        self.assertTrue(
            any(
                item["path"] == "ＯＳ" and "unsafe" in item.get("reason", "")
                for item in report["rejected"]
            )
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_type_envelope_malformed(self, mock_set_variables):
        # Tests that a malformed _class=type envelope is completely rejected
        payload = json.dumps(
            {
                "valid_var": {
                    "_class": "type",
                    "name": "docassemble.base.util.DAObject",
                    "evil_extra_key": "injected",
                }
            }
        )
        sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()
        self.assertTrue(
            any(
                item["path"] == "valid_var" and "only include" in item.get("reason", "")
                for item in report["rejected"]
            )
        )

    @patch("docassemble.AssemblyLine.sessions.set_variables")
    def test_adversarial_object_envelope_malformed(self, mock_set_variables):
        # Tests that a docassemble object envelope without an instanceName is rejected
        payload = json.dumps(
            {
                "users": {
                    "_class": "docassemble.base.util.DAObject",
                }
            }
        )
        sessions.load_interview_json(payload)
        report = sessions.get_last_import_report()
        self.assertTrue(
            any(
                item["path"] == "users"
                and "metadata must include both" in item.get("reason", "")
                for item in report["rejected"]
            )
        )

    @patch("docassemble.AssemblyLine.sessions.validation_error")
    def test_is_valid_json_reports_validation_error(self, mock_validation_error):
        bad_json = self._sample("malformed_trailing_comma.json")

        is_valid = sessions.is_valid_json(bad_json)

        self.assertFalse(is_valid)
        mock_validation_error.assert_called_once()

    @patch("docassemble.base.interview_cache.get_interview")
    @patch("docassemble.AssemblyLine.sessions.current_context")
    @patch("docassemble.AssemblyLine.sessions.set_variables")
    @patch("docassemble.AssemblyLine.sessions.get_config")
    def test_target_interview_vars(
        self, mock_get_config, mock_set_vars, mock_current_context, mock_get_interview
    ):
        mock_get_config.return_value = {}

        class QStub:
            pass

        class MockInterview:
            def __init__(self):
                self.names_used = {"user_name"}
                q1 = QStub()
                q1.mako_names = {"mako_var"}
                q1.names_used = {"name_var"}
                q1.fields_used = {"field_var"}
                self.questions_list = [q1]
                self.questions = {"q_val"}

        class MockCurrentContext:
            def __init__(self):
                self.filename = "docassemble.MyTest:test.yml"
                self.session = "123"

        mock_get_interview.return_value = MockInterview()
        mock_current_context.return_value = MockCurrentContext()

        payload = json.dumps(
            {
                "user_name": "Alice",
                "mako_var": "val1",
                "q_val": "val2",
                "bad_var": "hacked",
            }
        )

        sessions.load_interview_json(payload)

        report = sessions.get_last_import_report()
        accepted_keys = report["accepted"]
        rejected_keys = [r["path"] for r in report["rejected"]]

        self.assertIn("user_name", accepted_keys)
        self.assertIn("mako_var", accepted_keys)
        self.assertIn("q_val", accepted_keys)
        self.assertIn("bad_var", rejected_keys)
        self.assertTrue(
            any(
                "not in allowlist" in r["reason"]
                for r in report["rejected"]
                if r["path"] == "bad_var"
            )
        )


if __name__ == "__main__":
    unittest.main()

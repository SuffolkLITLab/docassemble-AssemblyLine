import json
import unittest
from unittest.mock import patch, MagicMock

@patch('docassemble.base.functions.get_config')
def run_test(mock_get_config):
    mock_get_config.return_value = {}

    from docassemble.AssemblyLine import sessions

    class MockInterview:
        def __init__(self):
            self.names_used = {"user_name"}
            
            q1 = MagicMock()
            q1.mako_names = {"mako_var"}
            q1.names_used = {"name_var"}
            q1.fields_used = {"field_var"}
            
            self.questions_list = [q1]
            self.questions = {"q_val"}

    class MockCurrentContext:
        def __init__(self):
            self.filename = "docassemble.MyTest:test.yml"
            self.session = "123"

    class AdhocTests(unittest.TestCase):
        @patch('docassemble.base.interview_cache.get_interview')
        @patch('docassemble.base.functions.current_context')
        @patch('docassemble.AssemblyLine.sessions.set_variables')
        def test_target_interview_vars(self, mock_set_vars, mock_current_context, mock_get_interview):
            mock_get_interview.return_value = MockInterview()
            mock_current_context.return_value = MockCurrentContext()
            
            payload = json.dumps({
                "user_name": "Alice",          # In names_used
                "mako_var": "val1",            # In questions_list[...].mako_names
                "q_val": "val2",               # In questions
                "bad_var": "hacked"            # NOT in any interview list
            })
            
            sessions.load_interview_json(payload)
            
            report = sessions.get_last_import_report()
            accepted_keys = [a['path'] for a in report['accepted']]
            rejected_keys = [r['path'] for r in report['rejected']]
            
            self.assertIn("user_name", accepted_keys)
            self.assertIn("mako_var", accepted_keys)
            self.assertIn("q_val", accepted_keys)
            self.assertIn("bad_var", rejected_keys)
            self.assertTrue(any('not in allowlist' in r['reason'] for r in report['rejected'] if r['path'] == "bad_var"))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AdhocTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    run_test()

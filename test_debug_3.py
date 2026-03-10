import json
from unittest.mock import patch, MagicMock
from docassemble.AssemblyLine import sessions

class QStub: pass
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

@patch('docassemble.base.functions.get_config', return_value={})
@patch('docassemble.base.interview_cache.get_interview', return_value=MockInterview())
@patch('docassemble.base.functions.current_context', return_value=MockCurrentContext())
@patch('docassemble.AssemblyLine.sessions.set_variables')
def run_debug(*args):
    payload = json.dumps({
        "user_name": "Alice",          
        "mako_var": "val1",            
        "q_val": "val2",               
        "bad_var": "hacked"            
    })
    sessions.load_interview_json(payload)
    print("REPORT IS", json.dumps(sessions.get_last_import_report(), indent=2))

if __name__ == "__main__":
    run_debug()

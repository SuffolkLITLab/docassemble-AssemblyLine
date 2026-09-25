# do not pre-load
"""Exercise the copy action with Docassemble's real interview engine.

Creating an answer set assembles another interview. On Docassemble 1.9.8,
that can discard the caller's ``forgive_missing_question`` state when the
YAML parser has been used, causing issue #1001 after the copy succeeds.
"""

from contextlib import contextmanager
from pathlib import Path

import pytest
import yaml

from docassemble.base import functions, parse


@contextmanager
def nested_interview_context():
    """Use the same context isolation as Docassemble's create_session()."""
    if hasattr(functions, "backup_thread_variables"):
        backup = functions.backup_thread_variables()
        try:
            yield
        finally:
            functions.restore_thread_variables(backup)
    else:
        from docassemble.base.thread_context import (
            copy_of_globals,
            global_context,
            this_thread,
        )

        with global_context(copy_of_globals(this_thread)):
            yield


def make_interview(blocks):
    source = parse.InterviewSourceString(
        content=yaml.safe_dump_all(blocks), package="docassemble.AssemblyLine"
    )
    return parse.Interview(source=source)


def assemble(interview, user_dict, session_uid):
    status = parse.InterviewStatus(
        current_info={
            "user": {
                "session_uid": session_uid,
                "device_id": "copy-test-device",
                "the_user_id": "1",
            }
        }
    )
    if hasattr(functions, "backup_thread_variables"):
        interview.assemble(user_dict, status)
    else:
        from docassemble.base.thread_context import user_dict_context

        with user_dict_context(user_dict):
            interview.assemble(user_dict, status)
    return status


@pytest.mark.parametrize("nested_assembly", [False, True])
def test_copy_action_prompts_saves_and_can_be_repeated(nested_assembly):
    source = Path(__file__).parent / "data/questions/interview_list.yml"
    blocks = list(yaml.safe_load_all(source.read_text()))
    name_question = next(b for b in blocks if b.get("id") == "copy to answer set")
    copy_block = next(
        b for b in blocks if "save_interview_answers(" in b.get("code", "")
    )
    saved = []

    def save_answers(**kwargs):
        if nested_assembly:
            # Parse here to reproduce the cold-parser path, then assemble the
            # target as create_session() does. Database writes are unnecessary.
            target = make_interview(
                [
                    {
                        "mandatory": True,
                        "question": "Saved answer set",
                        "subquestion": "${ preview_variables }",
                    },
                    {"template": "preview_variables", "content": "Preview"},
                ]
            )
            with nested_interview_context():
                assemble(target, parse.get_initial_dict(), "answer-set")
        saved.append(kwargs)
        return "copied-session"

    arguments = {
        "filename": "source.yml",
        "session": "source-session",
        "title": "Original title",
        "original_interview_filename": "Original interview",
    }
    with nested_interview_context():
        interview = make_interview(
            [
                {"mandatory": True, "question": "In progress forms", "id": "list"},
                name_question,
                copy_block,
            ]
        )
        user_dict = parse.get_initial_dict()
        user_dict.update(
            save_interview_answers=save_answers,
            action_argument=arguments.get,
        )
        for title in ["First copy", "Second copy"]:
            user_dict.pop("al_sessions_copy_as_answer_set_label", None)
            user_dict["_internal"]["event_stack"]["list"] = [
                {"action": "interview_list_copy_action", "arguments": arguments}
            ]
            before = len(saved)
            status = assemble(interview, user_dict, "list")
            assert status.question.id == "copy to answer set"
            assert len(saved) == before

            user_dict["al_sessions_copy_as_answer_set_label"] = title
            status = assemble(interview, user_dict, "list")
            assert status.question.id == "list"
            assert user_dict["_internal"]["event_stack"]["list"] == []
            assert len(saved) == before + 1
            assert saved[-1] == {
                "source_filename": "source.yml",
                "source_session": "source-session",
                "metadata": {"title": title},
                "original_interview_filename": "Original interview",
            }

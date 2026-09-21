# do not pre-load

"""Regression tests for saved-session names used by action forms."""

import os
import tempfile
from types import SimpleNamespace

import pytest

# Importing sessions initializes docassemble's database configuration. Supply
# an isolated empty config when the test runner has not provided one.
_test_config_dir = None
if not os.environ.get("DA_CONFIG_FILE"):
    _test_config_dir = tempfile.TemporaryDirectory(prefix="assemblyline-test-config-")
    os.environ["DA_CONFIG_FILE"] = os.path.join(_test_config_dir.name, "config.yml")
    with open(os.environ["DA_CONFIG_FILE"], "w", encoding="utf-8") as config:
        config.write("{}\n")

from docassemble.AssemblyLine import sessions


@pytest.fixture(autouse=True)
def empty_system_interviews(monkeypatch):
    monkeypatch.setattr(sessions, "system_interviews", [])


def test_raw_subtitle_preserves_raw_manual_title():
    answer = {
        "filename": "docassemble.demo:data/questions/form.yml",
        "title": "McDonaldCase",
    }

    assert (
        sessions.nice_interview_subtitle(answer, add_zero_width_spaces=False)
        == "McDonaldCase"
    )
    assert "\u200b" in sessions.nice_interview_subtitle(answer)


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (
            {
                "filename": "docassemble.demo:data/questions/form.yml",
                "auto_title": "A custom case",
            },
            "A custom case",
        ),
        (
            {
                "filename": "docassemble.demo:data/questions/form.yml",
                "auto_title": "Form",
            },
            "Form",
        ),
        (
            {
                "filename": "docassemble.demo:data/questions/form.yml",
                "title": "Manual",
                "auto_title": "Automatic",
            },
            "Manual",
        ),
        ({"filename": "docassemble.demo:data/questions/form.yml"}, "Form"),
    ],
)
def test_raw_subtitle_matches_display_precedence(answer, expected):
    assert (
        sessions.nice_interview_subtitle(answer, add_zero_width_spaces=False)
        or sessions.nice_interview_title(answer)
    ) == expected


def test_raw_subtitle_suppresses_case_only_auto_title():
    answer = {
        "filename": "docassemble.demo:data/questions/form.yml",
        "auto_title": "fORM",
    }

    assert sessions.nice_interview_subtitle(answer) == ""
    assert (
        sessions.nice_interview_subtitle(answer, add_zero_width_spaces=False)
        or sessions.nice_interview_title(answer)
    ) == "Form"


@pytest.mark.parametrize(
    ("metadata", "dispatch", "expected"),
    [
        ({"title": "McDonaldCase", "auto_title": "Automatic"}, [], "McDonaldCase"),
        ({"auto_title": "AutoCase"}, [], "AutoCase"),
        ({}, [], "Form"),
        ({"title": "", "auto_title": ""}, [], "Form"),
        ({"auto_title": "fORM"}, [], "Form"),
        (
            {},
            [
                {
                    "filename": "docassemble.demo:data/questions/form.yml",
                    "title": "Dispatch Form",
                }
            ],
            "Dispatch Form",
        ),
    ],
)
def test_session_list_actions_use_raw_display_name(
    monkeypatch, metadata, dispatch, expected
):
    answer = {
        "key": "session-1",
        "filename": "docassemble.demo:data/questions/form.yml",
        "modtime": "2025-01-01T00:00:00",
        "steps": 2,
        **metadata,
    }
    actions = []

    def capture_url_ask(steps):
        actions.append(steps)
        return "#action"

    monkeypatch.setattr(sessions, "url_ask", capture_url_ask)
    monkeypatch.setattr(
        sessions, "current_context", lambda: SimpleNamespace(session=None)
    )
    monkeypatch.setattr(sessions, "get_config", lambda *args, **kwargs: {})
    monkeypatch.setattr(sessions, "interview_url", lambda **kwargs: "#interview")
    monkeypatch.setattr(
        sessions, "local_date", lambda value: SimpleNamespace(time=lambda: "00:00")
    )
    monkeypatch.setattr(sessions, "format_time", lambda *args, **kwargs: "00:00")
    monkeypatch.setattr(sessions, "system_interviews", dispatch)

    html = sessions.session_list_html(answers=[answer])

    assert expected in html.replace("\u200b", "")
    assert actions[0][1]["arguments"]["title"] == expected
    assert actions[1][1]["arguments"]["title"] == expected

# do not pre-load

"""Regression tests for saved-session names used by action forms."""

import os
from datetime import datetime
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
        ({"title": "\u200bMc\u200bDonald\u200bCase\u200b"}, [], "McDonaldCase"),
        ({"auto_title": "Auto\u200bCase"}, [], "AutoCase"),
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
        (
            {},
            [
                {
                    "filename": "docassemble.demo:data/questions/form.yml",
                    "title": "Dispatch\u200bForm",
                }
            ],
            "DispatchForm",
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
    monkeypatch.setattr(sessions, "local_date", lambda value: datetime(2025, 1, 1))
    monkeypatch.setattr(sessions, "system_interviews", dispatch)

    html = sessions.session_list_html(answers=[answer])

    assert expected in html.replace("\u200b", "")
    assert actions[0][1]["arguments"]["title"] == expected
    assert actions[1][1]["arguments"]["title"] == expected


@pytest.mark.parametrize(
    "helper", [sessions.session_list_html, sessions.interview_list_html]
)
def test_labels_follow_language_and_escape_quotes(monkeypatch, helper):
    from html import escape

    monkeypatch.setattr(sessions, "url_ask", lambda *a, **kw: "#")
    monkeypatch.setattr(sessions, "url_action", lambda *a, **kw: "#")
    monkeypatch.setattr(sessions, "interview_url", lambda **kw: "#")
    monkeypatch.setattr(
        sessions, "current_context", lambda: SimpleNamespace(session=None)
    )
    monkeypatch.setattr(sessions, "get_config", lambda *a, **kw: {})
    monkeypatch.setattr(sessions, "local_date", lambda value: datetime(2025, 1, 1))
    answer = {
        "key": "test",
        "filename": "form.yml",
        "modtime": "2025-01-01",
        "steps": 2,
    }
    from docassemble.base import functions

    labels = {"en": 'Delete " < > &', "es": 'Borrar " < > &'}
    for language, label in labels.items():
        monkeypatch.setitem(
            functions.word_collection,
            language,
            {**functions.word_collection.get(language, {}), "Delete": label},
        )
    for language in ["en", "es", "en"]:
        monkeypatch.setattr(functions.this_thread, "language", language)
        label = labels[language]
        html = helper(answers=[answer])
        assert f'title="{escape(label)}"' in html
        assert label not in html
        html = helper(answers=[answer], delete_label="Custom & label")
        assert 'title="Custom &amp; label"' in html
        html = helper(answers=[answer], delete_label="")
        assert 'title=""' in html


def test_page_number_uses_catalog_word_order(monkeypatch):
    from pathlib import Path
    from html import escape
    from docassemble.base import functions

    for path in (Path(__file__).parent / "data/sources").glob("*-words.yml"):
        for language, catalog in functions.safeyaml.load(path.read_text()).items():
            monkeypatch.setitem(functions.word_collection, language, catalog)
            monkeypatch.setattr(functions.this_thread, "language", language)
            assert sessions.radial_progress({"steps": 3}) == escape(
                catalog["Page {number}"].format(number=3)
            )


@pytest.mark.parametrize(
    "language", ["en", "es", "spanish", "ht", "zh-Hans", "zh-Hant"]
)
@pytest.mark.parametrize(
    "helper", [sessions.session_list_html, sessions.interview_list_html]
)
def test_session_dates_do_not_require_a_babel_locale(monkeypatch, language, helper):
    from docassemble.base import functions

    monkeypatch.setattr(functions.this_thread, "language", language)
    monkeypatch.setattr(sessions, "get_default_timezone", lambda: "America/New_York")
    monkeypatch.setattr(sessions, "url_ask", lambda *a, **kw: "#")
    monkeypatch.setattr(sessions, "url_action", lambda *a, **kw: "#")
    monkeypatch.setattr(sessions, "interview_url", lambda **kw: "#")
    monkeypatch.setattr(
        sessions, "current_context", lambda: SimpleNamespace(session=None)
    )
    monkeypatch.setattr(sessions, "get_config", lambda *a, **kw: {})
    answer = {
        "key": "test",
        "filename": "form.yml",
        "modtime": "2026-09-14T03:05:00",
        "steps": 2,
    }
    html = helper(answers=[answer])
    assert "Bad date" not in html
    assert "unknown locale" not in html
    if helper is sessions.session_list_html:
        # UTC storage still converts to the configured timezone before formatting.
        assert "September 13, 2026" in html
        assert "11:05 PM" in html
    else:
        assert "September 14, 2026" in html

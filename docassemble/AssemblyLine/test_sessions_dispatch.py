# do not pre-load

import os
import tempfile

import pytest

# sessions needs a docassemble config to import, so use an empty one if none is set
_test_config_dir = None
if not os.environ.get("DA_CONFIG_FILE"):
    _test_config_dir = tempfile.TemporaryDirectory(prefix="assemblyline-test-config-")
    os.environ["DA_CONFIG_FILE"] = os.path.join(_test_config_dir.name, "config.yml")
    with open(os.environ["DA_CONFIG_FILE"], "w", encoding="utf-8") as config:
        config.write("{}\n")

from docassemble.AssemblyLine import sessions

FILENAME = "docassemble.demo:data/questions/form.yml"
ANSWER = {"filename": FILENAME}


def menu(title, broken=False):
    status = "dainterviewhaserror" if broken else None
    return [{"filename": FILENAME, "title": title, "status_class": status}]


class FakeMenu:
    def __init__(self):
        self.results = []
        self.calls = 0
        self.now = 0

    def __call__(self):
        self.calls += 1
        return self.results.pop(0)


@pytest.fixture
def fake_menu(monkeypatch):
    fake = FakeMenu()
    monkeypatch.setattr(sessions, "system_interviews", [])
    monkeypatch.setattr(sessions, "_dispatch_checked_at", None)
    monkeypatch.setattr(sessions, "_dispatch_had_errors", False)
    monkeypatch.setattr(sessions, "interview_menu", fake)
    monkeypatch.setattr(sessions, "get_interview", lambda filename: None)
    monkeypatch.setattr(sessions.time, "monotonic", lambda: fake.now)
    return fake


def test_menu_not_built_until_needed(fake_menu):
    fake_menu.results = [menu("A nice title")]

    assert fake_menu.calls == 0
    assert sessions.nice_interview_title(ANSWER) == "A nice title"
    assert fake_menu.calls == 1


def test_menu_built_once_when_it_loads(fake_menu):
    fake_menu.results = [menu("A nice title")]

    sessions.nice_interview_title(ANSWER)
    fake_menu.now = 10000
    sessions.nice_interview_title(ANSWER)

    assert fake_menu.calls == 1


def test_broken_entry_is_retried_after_a_minute(fake_menu):
    fake_menu.results = [menu(FILENAME, broken=True), menu("A nice title")]

    assert sessions.nice_interview_title(ANSWER) == "Form"
    fake_menu.now = 30
    assert sessions.nice_interview_title(ANSWER) == "Form"
    assert fake_menu.calls == 1

    fake_menu.now = 61
    assert sessions.nice_interview_title(ANSWER) == "A nice title"
    assert fake_menu.calls == 2

    fake_menu.now = 200
    sessions.nice_interview_title(ANSWER)
    assert fake_menu.calls == 2


def test_failure_reason_is_logged(fake_menu, monkeypatch):
    messages = []

    def fail(filename):
        raise ValueError("overwrites previous label")

    fake_menu.results = [menu(FILENAME, broken=True)]
    monkeypatch.setattr(sessions, "get_interview", fail)
    monkeypatch.setattr(sessions, "log", messages.append)

    sessions.nice_interview_title(ANSWER)

    assert len(messages) == 1
    assert FILENAME in messages[0]
    assert "overwrites previous label" in messages[0]

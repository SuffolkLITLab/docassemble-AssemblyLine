# do not pre-load
"""Tests for dispatch menu cache lifetime and authentication boundaries."""

import os
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

# Supply an isolated config when running this module on its own.
_test_config_dir = None
if not os.environ.get("DA_CONFIG_FILE"):
    _test_config_dir = tempfile.TemporaryDirectory(prefix="assemblyline-test-config-")
    os.environ["DA_CONFIG_FILE"] = os.path.join(_test_config_dir.name, "config.yml")
    with open(os.environ["DA_CONFIG_FILE"], "w", encoding="utf-8") as config:
        config.write("{}\n")

from docassemble.AssemblyLine import sessions


@pytest.fixture
def menu_cache(monkeypatch):
    clock = Mock(return_value=100.0)
    menu = Mock(return_value=[{"filename": "form.yml", "title": "Form title"}])
    monkeypatch.setattr(sessions, "system_interviews", [])
    monkeypatch.setattr(sessions, "_system_interviews_expires_at", 0.0)
    monkeypatch.setattr(sessions, "time", SimpleNamespace(monotonic=clock))
    monkeypatch.setattr(sessions, "interview_menu", menu)
    monkeypatch.setattr(sessions, "user_logged_in", lambda: True)
    return clock, menu


def test_successful_menu_expires_after_one_day(menu_cache):
    clock, menu = menu_cache
    assert sessions.nice_interview_title({"filename": "form.yml"}) == "Form title"
    clock.return_value += 86399
    sessions._get_system_interviews()
    assert menu.call_count == 1
    clock.return_value += 1
    sessions._get_system_interviews()
    assert menu.call_count == 2


def test_failed_menu_retries_after_one_minute(menu_cache):
    clock, menu = menu_cache
    menu.return_value = [
        {
            "filename": "form.yml",
            "title": "form.yml",
            "status_class": "dainterviewhaserror",
        }
    ]
    assert sessions.nice_interview_title({"filename": "form.yml"}) == "Form"
    clock.return_value += 59
    sessions._get_system_interviews()
    assert menu.call_count == 1
    clock.return_value += 1
    menu.return_value = [{"filename": "form.yml", "title": "Recovered"}]
    assert sessions.nice_interview_title({"filename": "form.yml"}) == "Recovered"
    assert menu.call_count == 2


def test_anonymous_menu_does_not_read_or_populate_shared_cache(menu_cache, monkeypatch):
    _, menu = menu_cache
    monkeypatch.setattr(sessions, "user_logged_in", lambda: False)
    menu.return_value = []
    assert sessions._get_system_interviews() == []
    assert sessions._system_interviews_expires_at == 0
    monkeypatch.setattr(sessions, "user_logged_in", lambda: True)
    menu.return_value = [{"filename": "staff.yml", "title": "Staff"}]
    assert sessions._get_system_interviews() == menu.return_value
    monkeypatch.setattr(sessions, "user_logged_in", lambda: False)
    menu.return_value = []
    assert sessions._get_system_interviews() == []
    assert sessions.system_interviews == [{"filename": "staff.yml", "title": "Staff"}]

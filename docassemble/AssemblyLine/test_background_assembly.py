# do not pre-load

"""Exercise durable background assembly completion, failure, and retry."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

BLOCKS = list(
    yaml.safe_load_all(
        (Path(__file__).parent / "data/questions/al_document.yml").read_text()
    )
)
MODES = [
    (
        "generate_preview_task",
        "preview_ready",
        "_preview_file",
        "al_preview_waiting_screen",
    ),
    (
        "generate_downloads_task",
        "downloads_ready",
        "_downloadable_files",
        "al_download_waiting_screen",
    ),
    (
        "generate_downloads_with_docx_task",
        "downloads_with_docx_ready",
        "_downloadable_files",
        "al_download_waiting_screen",
    ),
]
ERROR_MODES = [
    (
        "generate_preview_task",
        "_preview_error",
        "preview_error_screen",
        "retry_preview",
        "generate_preview_event",
        "save_preview_error",
    ),
    (
        "generate_downloads_task",
        "_download_error",
        "downloads_error_screen",
        "retry_downloads",
        "create_downloads",
        "save_download_error",
    ),
    (
        "generate_downloads_with_docx_task",
        "_download_error",
        "downloads_error_screen",
        "retry_downloads",
        "create_downloads_with_docx",
        "save_download_error",
    ),
]


def code_defining(attribute):
    return next(
        block["code"]
        for block in BLOCKS
        if block
        and any(
            line.startswith(f"x.{attribute} =")
            for line in block.get("code", "").splitlines()
        )
    )


def context(bundle):
    def undefine(*names):
        for name in names:
            bundle.__dict__.pop(name.split(".", 1)[1], None)

    return {
        "x": bundle,
        "defined": lambda name: name.split(".", 1)[1] in vars(bundle),
        "undefine": undefine,
        "background_action": Mock(
            return_value=Mock(
                ready=Mock(return_value=False), failed=Mock(return_value=False)
            )
        ),
    }


def event_block(event):
    return next(
        block for block in BLOCKS if block and block.get("event") == "x." + event
    )


@pytest.mark.parametrize("task,gate,cache,waiting", MODES)
@pytest.mark.parametrize("saved_result", [None, (), "saved file"])
def test_saved_callback_result_survives_expired_task(
    task, gate, cache, waiting, saved_result
):
    bundle = SimpleNamespace(attr_name=lambda name: "bundle." + name)
    expired = Mock()
    expired.ready.return_value = False
    setattr(bundle, task, expired)
    setattr(bundle, cache, saved_result)
    env = context(bundle)
    exec(code_defining(gate), env)
    assert getattr(bundle, gate) is True
    expired.ready.assert_not_called()
    expired.failed.assert_not_called()
    env["background_action"].assert_not_called()


@pytest.mark.parametrize("task,gate,cache,waiting", MODES)
@pytest.mark.parametrize("task_ready", [False, True])
def test_missing_callback_result_waits_without_marking_complete(
    task, gate, cache, waiting, task_ready
):
    bundle = SimpleNamespace(attr_name=lambda name: "bundle." + name)
    pending = Mock(ready=Mock(return_value=task_ready), failed=Mock(return_value=False))
    setattr(bundle, task, pending)
    with pytest.raises(NameError, match=waiting):
        exec(code_defining(gate), context(bundle))
    assert gate not in vars(bundle)
    if task_ready:
        pending.failed.assert_called_once_with()
    else:
        pending.failed.assert_not_called()


@pytest.mark.parametrize("task,gate,cache,waiting", MODES)
def test_restarting_task_discards_old_files_and_completion(task, gate, cache, waiting):
    bundle = SimpleNamespace(attr_name=lambda name: "bundle." + name)
    setattr(bundle, gate, True)
    setattr(bundle, cache, "outdated file")
    env = context(bundle)
    exec(code_defining(task), env)
    assert gate not in vars(bundle)
    assert cache not in vars(bundle)
    env["background_action"].assert_called_once()
    with pytest.raises(NameError, match=waiting):
        exec(code_defining(gate), env)
    setattr(bundle, cache, "replacement file")
    exec(code_defining(gate), env)
    assert getattr(bundle, gate) is True


@pytest.mark.parametrize(
    "task,other_task",
    [
        ("generate_downloads_task", "generate_downloads_with_docx_task"),
        ("generate_downloads_with_docx_task", "generate_downloads_task"),
    ],
)
def test_switching_download_mode_invalidates_shared_results(task, other_task):
    bundle = SimpleNamespace(
        attr_name=lambda name: "bundle." + name,
        downloads_ready=True,
        downloads_with_docx_ready=True,
        _downloadable_files="files from the other mode",
    )
    setattr(bundle, other_task, Mock())
    exec(code_defining(task), context(bundle))
    for stale in (
        other_task,
        "downloads_ready",
        "downloads_with_docx_ready",
        "_downloadable_files",
    ):
        assert stale not in vars(bundle)
    assert task in vars(bundle)


@pytest.mark.parametrize("task,error,screen,retry,create,save", ERROR_MODES)
def test_failed_task_stops_waiting_without_marking_complete(
    task, error, screen, retry, create, save
):
    gate = next(mode[1] for mode in MODES if mode[0] == task)
    bundle = SimpleNamespace(attr_name=lambda name: "bundle." + name)
    failed = Mock(ready=Mock(return_value=True), failed=Mock(return_value=True))
    setattr(bundle, task, failed)
    with pytest.raises(AttributeError, match=screen):
        exec(code_defining(gate), context(bundle))
    assert gate not in vars(bundle)
    failed.failed.assert_called_once_with()


@pytest.mark.parametrize("task,error,screen,retry,create,save", ERROR_MODES)
def test_saved_failure_survives_expiration_and_retry(
    task, error, screen, retry, create, save
):
    gate, cache, waiting = next(mode[1:] for mode in MODES if mode[0] == task)
    bundle = SimpleNamespace(attr_name=lambda name: "bundle." + name)
    expired = Mock(failed=Mock(return_value=False), ready=Mock(return_value=False))
    setattr(bundle, task, expired)
    env = context(bundle)
    env["background_response"] = Mock()
    exec(event_block(save)["code"], env)
    assert getattr(bundle, error) is True
    env["background_response"].assert_called_once_with()

    with pytest.raises(AttributeError, match=screen):
        exec(code_defining(gate), env)
    assert gate not in vars(bundle)
    expired.failed.assert_not_called()
    expired.ready.assert_not_called()
    env["background_action"].assert_not_called()

    def reconsider(name):
        assert name == "bundle." + task
        exec(code_defining(task), env)

    env["reconsider"] = Mock(side_effect=reconsider)
    exec(event_block(retry)["code"], env)
    env["reconsider"].assert_called_once_with("bundle." + task)
    assert error not in vars(bundle)
    env["background_action"].assert_called_once()
    with pytest.raises(NameError, match=waiting):
        exec(code_defining(gate), env)
    setattr(bundle, cache, "replacement file")
    exec(code_defining(gate), env)
    assert getattr(bundle, gate) is True


@pytest.mark.parametrize("task,error,screen,retry,create,save", ERROR_MODES)
def test_error_callback_registered_before_assembly(
    task, error, screen, retry, create, save
):
    assemble = Mock(side_effect=RuntimeError("attachment failed"))
    registered = Mock()
    bundle = SimpleNamespace(
        attr_name=lambda name: "bundle." + name,
        get_cacheable_documents=assemble,
        as_pdf=assemble,
    )
    calls = Mock()
    calls.attach_mock(registered, "register")
    calls.attach_mock(assemble, "assemble")
    with pytest.raises(RuntimeError, match="attachment failed"):
        exec(
            event_block(create)["code"],
            {"x": bundle, "background_error_action": registered},
        )
    registered.assert_called_once_with("bundle." + save)
    assert [call[0] for call in calls.mock_calls] == ["register", "assemble"]


@pytest.mark.parametrize("task,error,screen,retry,create,save", ERROR_MODES)
def test_regeneration_clears_failure_for_its_output_only(
    task, error, screen, retry, create, save
):
    bundle = SimpleNamespace(
        attr_name=lambda name: "bundle." + name,
        _download_error=True,
        _preview_error=True,
    )
    exec(code_defining(task), context(bundle))
    assert error not in vars(bundle)
    other_error = "_download_error" if error == "_preview_error" else "_preview_error"
    assert getattr(bundle, other_error) is True


@pytest.mark.parametrize(
    "screen,retry",
    [
        ("downloads_error_screen", "retry_downloads"),
        ("preview_error_screen", "retry_preview"),
    ],
)
def test_error_screen_offers_retry_without_reloading(screen, retry):
    block = event_block(screen)
    assert not block.get("reload")
    assert "url_action(x.attr_name('" + retry + "'))" in block["subquestion"]

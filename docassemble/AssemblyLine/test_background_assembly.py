# do not pre-load

"""Exercise the standard YAML gates with an expired Celery result."""

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
        "background_action": Mock(return_value=Mock()),
    }


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
    env["background_action"].assert_not_called()


@pytest.mark.parametrize("task,gate,cache,waiting", MODES)
def test_missing_callback_result_waits_without_marking_complete(
    task, gate, cache, waiting
):
    bundle = SimpleNamespace(attr_name=lambda name: "bundle." + name)
    setattr(bundle, task, Mock())
    with pytest.raises(NameError, match=waiting):
        exec(code_defining(gate), context(bundle))
    assert gate not in vars(bundle)


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

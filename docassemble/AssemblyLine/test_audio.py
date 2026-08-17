# do not pre-load
from pathlib import Path

import yaml

PACKAGE_PATH = Path(__file__).parent
AUDIO_LABELS = {"Listen", "Restart", "Pause", "Stop"}


def test_audio_control_labels_use_browser_translations() -> None:
    audio_javascript = (PACKAGE_PATH / "data" / "static" / "al_audio.js").read_text(
        encoding="utf-8"
    )

    for label in AUDIO_LABELS:
        assert f"alTranslate('{label}')" in audio_javascript


def test_every_word_catalog_translates_audio_control_labels() -> None:
    source_path = PACKAGE_PATH / "data" / "sources"
    word_files = sorted(source_path.glob("*-words.yml"))
    assert word_files

    for word_file in word_files:
        catalogs = yaml.safe_load(word_file.read_text(encoding="utf-8"))
        assert catalogs
        for language, translations in catalogs.items():
            assert AUDIO_LABELS <= translations.keys(), f"{word_file.name}:{language}"

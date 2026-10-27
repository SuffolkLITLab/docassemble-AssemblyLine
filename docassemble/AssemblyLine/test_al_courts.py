# do not pre-load

from types import SimpleNamespace

from docassemble.base import functions
import pandas as pd
import pytest

from .al_courts import ALCourtLoader


@pytest.fixture
def courts(monkeypatch):
    frame = pd.DataFrame(
        {
            "name": ["North Court", "South Court", "Other Court"],
            "department": ["District", "District", "Superior"],
            "division_abbr": ["N", "S", "N"],
            "address_county": ["Essex", "Essex", "Middlesex"],
        },
        index=[4, 8, 12],
    )
    monkeypatch.setattr(
        functions.this_thread,
        "current_question",
        SimpleNamespace(package="docassemble.AssemblyLine"),
    )
    loader = ALCourtLoader("courts", filename="courts.xlsx")
    monkeypatch.setattr(loader, "_load_courts", lambda: frame)
    return loader, frame


def test_multiple_columns_match_the_same_court(courts):
    loader, _ = courts
    assert loader.filter_courts(
        filters={"division_abbr": "N", "address_county": "Essex"}
    ) == [(4, "North Court")]


def test_filters_combine_with_legacy_department_and_search(courts):
    loader, frame = courts
    assert loader.filter_courts(
        "District",
        filters={"division_abbr": ["N", "S"]},
        search_string="south",
        search_columns="name",
    ) == [(8, "South Court")]
    assert "__search_col" not in frame.columns


def test_empty_filter_list_matches_no_courts(courts):
    loader, _ = courts
    assert loader.filter_courts(filters={"division_abbr": []}) == []


def test_existing_single_column_and_unfiltered_calls(courts):
    loader, _ = courts
    assert loader.filter_courts("Superior") == [(12, "Other Court")]
    assert len(loader.filter_courts(None)) == 3

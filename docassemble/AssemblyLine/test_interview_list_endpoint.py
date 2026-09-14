# do not pre-load

import re
from datetime import datetime
from unittest.mock import patch

import pytest
from jinja2 import Environment
from markupsafe import Markup

try:
    from docassemble.webapp.app_object import app
    from docassemble.AssemblyLine import interview_list_endpoint as endpoint
except SystemExit as ex:
    pytest.skip(
        f"requires a running docassemble server: {ex}",
        allow_module_level=True,
    )


class FakeUser:
    id = 1
    email = "test@example.com"
    first_name = "Test"
    last_name = "User"
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def get_id(self):
        return "1"


def make_view_model(**overrides):
    view_model = {
        "title": "Test Interview",
        "subtitle": "",
        "filename": "docassemble.playground1:test.yml",
        "session_key": "abc123",
        "url": "/interview?i=test",
        "date_str": "September 14, 2026",
        "time_str": "3:05 AM",
        "progress_html": Markup("<div>30%</div>"),
    }
    view_model.update(overrides)
    return view_model


def fake_url_for(endpoint_name, **kwargs):
    clean = {k: v for k, v in kwargs.items() if v is not None}
    query = "&".join(f"{k}={v}" for k, v in clean.items())
    return f"/{endpoint_name}" + (f"?{query}" if query else "")


def render_page(**context):
    """Render just this template's own markup, not docassemble's real base
    template.
    """
    template_source = re.sub(
        r"^\{%-?\s*extends.*?%\}\n?", "", endpoint.PAGE_TEMPLATE, count=1
    )
    env = Environment(autoescape=True)
    env.globals["url_for"] = fake_url_for
    return env.from_string(template_source).render(**context)


def base_context(**overrides):
    context = {
        "cfg": {
            "page_heading": "In progress forms",
            "page_intro": None,
            "new_form_label": "Start a new form",
            "new_form_url": "/",
            "enable_answer_sets": False,
            "exclude_filenames": endpoint.DEFAULT_EXCLUDED_FILENAMES,
        },
        "sessions": [],
        "filename_options": [],
        "csrf_token": "test-token",
        "page": 0,
        "page_size": endpoint.PAGE_SIZE,
        "keyword": "",
        "limit_filename": "",
        "package_name": "docassemble.AssemblyLine",
    }
    context.update(overrides)
    return context


# what the template itself does with the data it's handed
def test_session_view_model_wraps_progress_as_markup():
    fake_session = {
        "filename": "docassemble.playground1:test.yml",
        "key": "abc123",
        "modtime": None,
    }
    with patch.object(
        endpoint, "nice_interview_title", return_value="Test Interview"
    ), patch.object(endpoint, "nice_interview_subtitle", return_value=""), patch.object(
        endpoint, "interview_url", return_value="/interview?i=test"
    ), patch.object(
        endpoint, "local_date", return_value=datetime(2026, 9, 14, 3, 5)
    ), patch.object(
        endpoint, "radial_progress", return_value="<div>30%</div>"
    ):
        view_model = endpoint._session_view_model(fake_session)

    assert view_model["title"] == "Test Interview"
    assert isinstance(view_model["progress_html"], Markup)
    assert str(view_model["progress_html"]) == "<div>30%</div>"


def test_empty_session_list_shows_placeholder():
    html = render_page(**base_context(sessions=[]))
    assert "No saved forms yet." in html
    assert "al-saved-answer-table" not in html


def test_normal_rows_render():
    sessions = [
        make_view_model(title="First Form", session_key="1"),
        make_view_model(title="Second Form", session_key="2"),
    ]
    html = render_page(**base_context(sessions=sessions))
    assert "First Form" in html
    assert "Second Form" in html
    assert html.count("al-saved-answer-table-row") == 2


def test_answer_sets_hidden_by_default():
    html = render_page(**base_context(sessions=[make_view_model()]))
    assert "Copy to answer set" not in html


def test_answer_sets_shown_when_enabled():
    context = base_context(sessions=[make_view_model()])
    context["cfg"]["enable_answer_sets"] = True
    html = render_page(**context)
    assert "Copy to answer set" in html


def test_search_and_filter_values_stay_on_the_page():
    context = base_context(
        keyword="eviction",
        limit_filename="docassemble.playground1:test.yml",
        filename_options=[{"docassemble.playground1:test.yml": "Test Form"}],
    )
    html = render_page(**context)
    assert 'value="eviction"' in html
    assert 'value="docassemble.playground1:test.yml" selected' in html


def test_pagination_links_keep_the_search_state():
    full_page = [make_view_model(session_key=str(i)) for i in range(endpoint.PAGE_SIZE)]
    context = base_context(sessions=full_page, keyword="eviction", page=1)
    html = render_page(**context)
    assert "keyword=eviction" in html
    assert "page=0" in html
    assert "page=2" in html


def test_session_title_with_script_tag_is_escaped():
    malicious = make_view_model(title="<script>alert(1)</script>")
    html = render_page(**base_context(sessions=[malicious]))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


# what the route does with a request, not how the page renders
def call_route(query_string=""):
    with app.test_request_context(f"/al_interview_list?{query_string}"):
        with patch("flask_login.utils._get_user", return_value=FakeUser()):
            endpoint.al_interview_list()


def test_route_uses_get_saved_interview_list_with_no_search_terms():
    with patch.object(
        endpoint, "render_template_string", return_value="ok"
    ) as mock_render, patch.object(
        endpoint, "_list_config", return_value=base_context()["cfg"]
    ), patch.object(
        endpoint, "get_saved_interview_list", return_value=[]
    ) as mock_list, patch.object(
        endpoint, "find_matching_sessions"
    ) as mock_search, patch.object(
        endpoint, "get_combined_filename_list", return_value=[]
    ), patch.object(
        endpoint, "generate_csrf", return_value="token"
    ):
        call_route()

    mock_list.assert_called_once()
    mock_search.assert_not_called()
    assert mock_render.call_args.kwargs["keyword"] == ""


def test_route_uses_find_matching_sessions_when_keyword_given():
    with patch.object(
        endpoint, "render_template_string", return_value="ok"
    ), patch.object(
        endpoint, "_list_config", return_value=base_context()["cfg"]
    ), patch.object(
        endpoint, "get_saved_interview_list"
    ) as mock_list, patch.object(
        endpoint, "find_matching_sessions", return_value=[]
    ) as mock_search, patch.object(
        endpoint, "get_combined_filename_list", return_value=[]
    ), patch.object(
        endpoint, "generate_csrf", return_value="token"
    ):
        call_route("keyword=eviction")

    mock_search.assert_called_once()
    mock_list.assert_not_called()

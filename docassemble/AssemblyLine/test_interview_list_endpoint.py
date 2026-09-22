# do not pre-load

import re
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from jinja2 import Environment
from markupsafe import Markup

try:
    try:
        from docassemble.webapp.flask_app import flaskapp as app
    except ModuleNotFoundError:
        from docassemble.webapp.app_object import app
    from docassemble.AssemblyLine import interview_list_endpoint as endpoint
    from docassemble.AssemblyLine import sessions as session_helpers
except (SystemExit, ModuleNotFoundError) as ex:
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
        r"^\{%-?\s*extends.*?%\}\n?",
        "",
        endpoint.PAGE_TEMPLATE,
        count=1,
        flags=re.MULTILINE,
    )
    # The real base template renders page_title in its navbar. Render it here too
    # so branding configuration remains covered without loading docassemble's base.
    template_source += "\n{{ page_title }}"
    env = Environment(autoescape=True)
    env.globals["url_for"] = fake_url_for
    return env.from_string(template_source).render(**context)


def base_context(**overrides):
    context = {
        "cfg": {
            "page_title": "In progress forms",
            "page_heading": "In progress forms",
            "page_intro": None,
            "new_form_label": "Start a new form",
            "new_form_url": "/",
            "enable_answer_sets": False,
            "answer_sets_title": "Answer sets",
            "logo_url": None,
            "logo_image_url": None,
            "logo_image_alt": "",
            "logo_title_row_1": None,
            "logo_title_row_2": None,
            "exclude_filenames": endpoint.DEFAULT_EXCLUDED_FILENAMES,
        },
        "sessions": [],
        "filename_options": [],
        "csrf_token": "test-token",
        "page": 0,
        "page_size": endpoint.PAGE_SIZE,
        "keyword": "",
        "limit_filename": "",
        "active_tab": "in_progress",
        "search_submitted": False,
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


def test_search_controls_only_appear_on_search_tab():
    in_progress_html = render_page(**base_context())
    search_html = render_page(**base_context(active_tab="search"))

    assert 'id="keyword"' not in in_progress_html
    assert 'id="limit_filename"' not in in_progress_html
    assert 'id="keyword"' in search_html
    assert 'id="limit_filename"' in search_html


def test_answer_set_tab_uses_custom_title_and_hides_copy_action():
    context = base_context(active_tab="answer_sets", sessions=[make_view_model()])
    context["cfg"]["enable_answer_sets"] = True
    context["cfg"]["answer_sets_title"] = "Reusable answers"

    html = render_page(**context)

    assert "Reusable answers" in html
    assert "Copy to answer set" not in html
    assert 'class="al-session-form-title" href=' not in html


def test_custom_logo_settings_are_rendered_and_escaped():
    context = base_context()
    context["cfg"].update(
        {
            "logo_url": "/custom-home",
            "logo_image_url": "/custom-logo.png",
            "logo_image_alt": 'Legal aid "logo"',
            "logo_title_row_1": "Legal Aid",
            "logo_title_row_2": "Saved forms",
        }
    )

    html = render_page(**context)

    assert 'src="/custom-logo.png"' in html
    assert 'alt="Legal aid &#34;logo&#34;"' in html
    assert "Legal Aid" in html
    assert "Saved forms" in html
    assert 'brandLink.href = "/custom-home"' in html


def test_search_and_filter_values_stay_on_the_page():
    context = base_context(
        active_tab="search",
        search_submitted=True,
        keyword="eviction",
        limit_filename="docassemble.playground1:test.yml",
        filename_options=[{"docassemble.playground1:test.yml": "Test Form"}],
    )
    html = render_page(**context)
    assert 'value="eviction"' in html
    assert 'value="docassemble.playground1:test.yml" selected' in html


def test_pagination_links_keep_the_search_state():
    full_page = [make_view_model(session_key=str(i)) for i in range(endpoint.PAGE_SIZE)]
    context = base_context(
        active_tab="search",
        search_submitted=True,
        sessions=full_page,
        keyword="eviction",
        page=1,
    )
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


def call_post_route(route, data):
    with app.test_request_context(
        "/al_interview_list/action", method="POST", data=data
    ):
        with patch(
            "flask_login.utils._get_user", return_value=FakeUser()
        ), patch.object(endpoint, "flash"), patch.object(
            endpoint, "url_for", return_value="/al_interview_list"
        ):
            route()


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


def test_answer_sets_tab_queries_only_the_answer_set_store():
    cfg = base_context()["cfg"]
    cfg["enable_answer_sets"] = True
    with patch.object(
        endpoint, "render_template_string", return_value="ok"
    ) as mock_render, patch.object(
        endpoint, "_list_config", return_value=cfg
    ), patch.object(
        endpoint, "get_saved_interview_list", return_value=[]
    ) as mock_list, patch.object(
        endpoint, "find_matching_sessions"
    ) as mock_search, patch.object(
        endpoint, "get_combined_filename_list"
    ) as mock_filenames, patch.object(
        endpoint, "generate_csrf", return_value="token"
    ):
        call_route("tab=answer_sets")

    mock_list.assert_called_once_with(
        filename=endpoint.al_session_store_default_filename,
        user_id=FakeUser.id,
        exclude_current_filename=False,
        exclude_newly_started_sessions=False,
        limit=endpoint.PAGE_SIZE,
        offset=0,
    )
    mock_search.assert_not_called()
    mock_filenames.assert_not_called()
    assert mock_render.call_args.kwargs["active_tab"] == "answer_sets"


def test_blank_search_tab_does_not_query_sessions():
    with patch.object(
        endpoint, "render_template_string", return_value="ok"
    ) as mock_render, patch.object(
        endpoint, "_list_config", return_value=base_context()["cfg"]
    ), patch.object(
        endpoint, "get_saved_interview_list"
    ) as mock_list, patch.object(
        endpoint, "find_matching_sessions"
    ) as mock_search, patch.object(
        endpoint, "get_combined_filename_list", return_value=[]
    ) as mock_filenames, patch.object(
        endpoint, "generate_csrf", return_value="token"
    ):
        call_route("tab=search")

    mock_list.assert_not_called()
    mock_search.assert_not_called()
    mock_filenames.assert_called_once_with(
        user_id=FakeUser.id,
        exclude_filenames=base_context()["cfg"]["exclude_filenames"],
    )
    assert mock_render.call_args.kwargs["search_submitted"] is False


@pytest.mark.parametrize(
    ("route_name", "mutation_name"),
    [
        ("al_interview_list_rename", "rename_interview_answers"),
        ("al_interview_list_copy", "save_interview_answers"),
    ],
)
def test_mutation_routes_reject_sessions_not_owned_by_current_user(
    route_name, mutation_name
):
    route = getattr(endpoint, route_name)
    data = {
        "filename": "docassemble.OtherPackage:data/questions/form.yml",
        "session": "shared-session-key",
        "new_name": "Stolen answers",
    }
    with patch.object(
        endpoint, "is_session_owned_by_user", return_value=False
    ) as mock_owned, patch.object(
        endpoint, mutation_name
    ) as mock_mutation, patch.object(
        endpoint, "_set_current_info"
    ) as mock_set_info, patch.object(
        endpoint, "log"
    ):
        call_post_route(route, data)

    mock_owned.assert_called_once_with(
        filename=data["filename"], session_id=data["session"], user_id=FakeUser.id
    )
    mock_mutation.assert_not_called()
    mock_set_info.assert_not_called()


def test_config_preserves_nested_and_legacy_customization():
    assembly_line_config = {
        "enable answer sets": True,
        "exclude from interview list": ["legacy:excluded.yml"],
        "interview list": {
            "exclude from interview list": [
                "docassemble.CustomDashboard",
                "custom:excluded.yml",
            ]
        },
    }
    configured_labels = {
        "page title": "Saved work",
        "page question": "Your forms",
        "page subquestion": "Choose a form to continue.",
        "new form label": "Begin",
        "new form url": "/start",
        "answer sets title": "Reusable answers",
        "logo url": "/custom-home",
        "logo image url": "/custom-logo.png",
        "logo alt": "Legal aid logo",
        "logo title row 1": "Legal Aid",
        "logo title row 2": "Saved forms",
    }

    with patch.object(
        endpoint, "get_config", return_value=assembly_line_config
    ), patch.object(
        endpoint,
        "config_with_language_fallback",
        side_effect=lambda key, fallback=None: configured_labels.get(key),
    ):
        config = endpoint._list_config()

    assert config == {
        "page_title": "Saved work",
        "page_heading": "Your forms",
        "page_intro": "Choose a form to continue.",
        "new_form_label": "Begin",
        "new_form_url": "/start",
        "enable_answer_sets": True,
        "answer_sets_title": "Reusable answers",
        "logo_url": "/custom-home",
        "logo_image_url": "/custom-logo.png",
        "logo_image_alt": "Legal aid logo",
        "logo_title_row_1": "Legal Aid",
        "logo_title_row_2": "Saved forms",
        "exclude_filenames": [
            "docassemble.CustomDashboard",
            "custom:excluded.yml",
        ],
    }


def test_config_uses_legacy_top_level_exclusion_setting_as_fallback():
    assembly_line_config = {
        "exclude from interview list": ["docassemble.LegacyDashboard"],
        "interview list": {},
    }
    with patch.object(
        endpoint, "get_config", return_value=assembly_line_config
    ), patch.object(endpoint, "config_with_language_fallback", return_value=None):
        config = endpoint._list_config()

    assert config["exclude_filenames"] == ["docassemble.LegacyDashboard"]


@pytest.mark.parametrize(
    "query_function,kwargs",
    [
        (
            session_helpers.get_saved_interview_list,
            {"filename": None, "exclude_current_filename": False},
        ),
        (
            session_helpers.find_matching_sessions,
            {"keyword": "", "exclude_current_filename": False},
        ),
    ],
)
def test_session_queries_apply_custom_exact_and_package_exclusions_before_paging(
    query_function, kwargs
):
    database_session = MagicMock()
    database_session.execute.return_value = []
    session_context = MagicMock()
    session_context.__enter__.return_value = database_session

    with patch.object(session_helpers, "_get_session", return_value=session_context):
        query_function(
            user_id=FakeUser.id,
            exclude_filenames=[
                "docassemble.CustomDashboard",
                "custom:excluded.yml",
            ],
            limit=20,
            offset=40,
            **kwargs,
        )

    query, parameters = database_session.execute.call_args.args
    query_text = str(query)
    assert "userdict.filename LIKE :excluded_package_0" in query_text
    assert query_text.index(
        "userdict.filename LIKE :excluded_package_0"
    ) < query_text.index("LIMIT :limit")
    assert parameters["excluded_package_0"] == "docassemble.CustomDashboard%"
    assert "custom:excluded.yml" in parameters["filenames_to_exclude"]
    assert "docassemble.CustomDashboard" not in parameters["filenames_to_exclude"]
    assert parameters["limit"] == 20
    assert parameters["offset"] == 40


def test_get_filenames_having_sessions_uses_userdictkeys():
    db_session = MagicMock()
    db_session.execute.return_value.mappings.return_value.all.return_value = [
        {"filename": "docassemble.playground1:test.yml"}
    ]

    session_context = MagicMock()
    session_context.__enter__.return_value = db_session

    with patch.object(session_helpers, "_get_session", return_value=session_context):
        filenames = session_helpers.get_filenames_having_sessions(user_id=FakeUser.id)

    query, params = db_session.execute.call_args.args
    query_text = str(query)

    assert "FROM userdictkeys AS k" in query_text
    assert "k.user_id = :user_id" in query_text
    assert "EXISTS" in query_text
    assert params == {"user_id": FakeUser.id}
    assert filenames == ["docassemble.playground1:test.yml"]


def test_get_combined_filename_list_applies_exclusions():
    with patch.object(
        session_helpers,
        "get_filenames_having_sessions",
        return_value=[
            "docassemble.playground1:test.yml",
            "custom:excluded.yml",
            "docassemble.CustomDashboard:data/questions/default.yml",
        ],
    ), patch.object(
        session_helpers,
        "interview_menu",
        return_value=[
            {
                "filename": "docassemble.playground1:test.yml",
                "title": "Test Interview",
            }
        ],
    ):
        result = session_helpers.get_combined_filename_list(
            user_id=FakeUser.id,
            exclude_filenames=[
                "docassemble.CustomDashboard",
                "custom:excluded.yml",
            ],
        )

    assert result == [{"docassemble.playground1:test.yml": "Test Interview"}]

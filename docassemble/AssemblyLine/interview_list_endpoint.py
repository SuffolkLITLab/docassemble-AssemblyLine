# pre-load
from flask import request, redirect, url_for, flash, render_template_string
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from markupsafe import escape

from docassemble.webapp.app_object import app
from docassemble.webapp.server import user_interviews
from docassemble.base.functions import this_thread, interview_url, log, get_config
from docassemble.AssemblyLine.sessions import (
    get_saved_interview_list,
    find_matching_sessions,
    delete_interview_sessions,
    rename_interview_answers,
    save_interview_answers,
    nice_interview_title,
    nice_interview_subtitle,
    radial_progress,
    local_date,
    config_with_language_fallback,
    get_combined_filename_list,
)

PAGE_SIZE = 20

PAGE_TEMPLATE = """
{%- extends 'flask_user/public_base.html' %}
{%- block content %}
<link rel="stylesheet" href="/packagestatic/docassemble.AssemblyLine/interview_list.css">
<style>
.al-icon-btn {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    color: #0d6efd;
    text-decoration: none;
}
.al-icon-btn:hover, .al-icon-btn:focus {
    text-decoration: underline;
}
.al-icon-btn i {
    color: #0d6efd;
}
.al-icon-btn.al-danger, .al-icon-btn.al-danger i {
    color: #dc3545;
}
.al-icon-btn span {
    font-size: 0.85rem;
}
</style>
{{ content|safe }}
{%- endblock %}
"""

DEFAULT_EXCLUDED_FILENAMES = [
    "docassemble.ALDashboard",
    "docassemble.AssemblyLine:data/questions/al_saved_sessions_store.yml",
    "docassemble.AssemblyLine:data/questions/interview_list.yml",
]


def _list_config():
    """Pulls the same "assembly line: interview list" settings interview_list.yml
    reads, so this page stays in sync with however each site has it configured."""
    interview_list_config = get_config("assembly line", {}).get("interview list", {})
    exclude_filenames = interview_list_config.get(
        "exclude from interview list",
        get_config("assembly line", {}).get(
            "exclude from interview list", DEFAULT_EXCLUDED_FILENAMES
        ),
    )
    return {
        "page_heading": config_with_language_fallback(
            "page question", "interview page heading"
        )
        or "In progress forms",
        "page_intro": config_with_language_fallback("interview page pre"),
        "new_form_label": config_with_language_fallback("new form label")
        or "Start a new form",
        "new_form_url": config_with_language_fallback("new form url", "app homepage"),
        "enable_answer_sets": bool(
            get_config("assembly line", {}).get("enable answer sets")
        ),
        "exclude_filenames": exclude_filenames,
    }


def _set_current_info():
    """Set up the login info docassemble's session functions need, since we're not inside a real interview"""
    # rename_interview_answers/save_interview_answers/user_interviews all read
    # this_thread.current_info for the acting user, which usually is populated
    # by docassemble's own interview dispatch. Since this is a plain Flask
    # route, we have to populate it ourselves before calling into them
    this_thread.current_info = {
        "user": {
            "is_authenticated": True,
            "is_anonymous": False,
            "theid": current_user.id,
            "the_user_id": current_user.id,
            "email": current_user.email,
            "firstname": current_user.first_name,
            "lastname": current_user.last_name,
            "roles": (
                [r.name for r in current_user.roles]
                if hasattr(current_user, "roles")
                else []
            ),
            "device_id": "al_interview_list",
            "session_uid": "al_interview_list",
        },
        "session": None,
        "secret": None,
        "yaml_filename": None,
    }


def _toggleable_action_icon(icon_class, label, target_id, danger=False, tooltip=None):
    """Make a small icon link that shows or hides a form when clicked."""
    danger_class = " al-danger" if danger else ""
    tooltip_text = tooltip or label
    return f"""
        <a href="#" class="al-icon-btn{ danger_class } d-inline-flex align-items-center gap-1" title="{ tooltip_text }" aria-label="{ tooltip_text }"
           onclick="var f=document.getElementById('{ target_id }'); f.style.display = f.style.display === 'none' ? 'flex' : 'none'; return false;">
            <i class="{ icon_class }" aria-hidden="true"></i>
            <span>{ label }</span>
        </a>
    """


def _toggleable_action_form(
    route_name, filename, session_key, csrf_token, placeholder, target_id
):
    """Make the hidden name box that shows up when you click rename or copy"""
    field_id = f"{ target_id }-name"
    return f"""
        <form id="{ target_id }" method="POST" action="{ url_for(route_name) }" style="display:none; flex-direction:column; gap:2px; margin-top:4px; max-width:16rem;">
            <input type="hidden" name="csrf_token" value="{ csrf_token }">
            <input type="hidden" name="filename" value="{ filename }">
            <input type="hidden" name="session" value="{ session_key }">
            <label for="{ field_id }" class="small mb-0">{ placeholder }<span class="text-danger">*</span></label>
            <div class="d-flex gap-2">
                <input id="{ field_id }" type="text" name="new_name" required class="form-control form-control-sm" style="width:9rem;">
                <button type="submit" class="btn btn-sm btn-secondary">Save</button>
            </div>
        </form>
    """


def _render_session_rows(sessions, csrf_token, enable_answer_sets):
    """Build the table showing all the saved sessions and their action buttons"""
    if not sessions:
        return "<p>No saved forms yet.</p>"

    rows = (
        '<div class="table-responsive">'
        '<table class="table table-striped al-saved-answer-table">'
        "<thead><tr>"
        '<th scope="col">Title</th>'
        '<th scope="col">Date modified</th>'
        '<th scope="col">Progress</th>'
        '<th scope="col">Actions</th>'
        "</tr></thead><tbody>"
    )

    for s in sessions:
        title = escape(nice_interview_title(s))
        subtitle = escape(nice_interview_subtitle(s))
        filename = escape(s["filename"])
        session_key = escape(s["key"])
        modtime = local_date(s.get("modtime"))
        subtitle_html = (
            f'<br/><span class="al-session-form-subtitle">{ subtitle }</span>'
            if subtitle
            else ""
        )

        rename_target = f"rename-{ session_key }"
        rename_icon = _toggleable_action_icon(
            "fa-solid fa-tag", "Rename", rename_target
        )
        rename_form = _toggleable_action_form(
            "al_interview_list_rename",
            filename,
            session_key,
            csrf_token,
            "New name",
            rename_target,
        )

        copy_icon = ""
        copy_form = ""
        if enable_answer_sets:
            copy_target = f"copy-{ session_key }"
            copy_icon = _toggleable_action_icon(
                "fa-regular fa-clone",
                "Copy to answer set",
                copy_target,
                tooltip="Saves these answers so you can reuse them to start a different form later.",
            )
            copy_form = _toggleable_action_form(
                "al_interview_list_copy",
                filename,
                session_key,
                csrf_token,
                "Answer set name",
                copy_target,
            )

        rows += f"""<tr class="al-saved-answer-table-row">
            <td class="text-break">
                <a class="al-session-form-title" href="{ interview_url(i=s['filename'], session=s['key'], style='full') }">{ title }</a>
                { subtitle_html }
            </td>
            <td>
                <span class="al-session-date-modified">{ modtime.strftime('%B %-d, %Y') }</span><br/>
                <span class="al-session-time-modified">{ modtime.strftime('%-I:%M %p') }</span>
            </td>
            <td class="al-progress-box">{ radial_progress(s) }</td>
            <td>
                <div class="d-flex flex-wrap gap-3">
                    { rename_icon }
                    { copy_icon }
                    <form id="delete-{ session_key }" method="POST" action="{ url_for('al_interview_list_delete') }" style="display:inline" onsubmit="return confirm('Delete this item?')">
                        <input type="hidden" name="csrf_token" value="{ csrf_token }">
                        <input type="hidden" name="filename" value="{ filename }">
                        <input type="hidden" name="session" value="{ session_key }">
                        <button type="submit" class="al-icon-btn al-danger d-inline-flex align-items-center gap-1" title="Delete" aria-label="Delete">
                            <i class="far fa-trash-alt" aria-hidden="true"></i>
                            <span>Delete</span>
                        </button>
                    </form>
                </div>
                { rename_form }
                { copy_form }
            </td>
        </tr>"""

    rows += "</tbody></table></div>"
    return rows


if "al_interview_list" not in app.view_functions:

    @app.route("/al_interview_list", methods=["GET"])
    @login_required
    def al_interview_list():
        """Show the current user's saved interview sessions, with search and paging."""
        cfg = _list_config()

        page = max(request.args.get("page", 0, type=int), 0)
        offset = page * PAGE_SIZE
        keyword = request.args.get("keyword", "").strip()
        limit_filename = request.args.get("limit_filename", "").strip()

        if keyword or limit_filename:
            sessions = find_matching_sessions(
                keyword=keyword,
                filenames={limit_filename} if limit_filename else None,
                user_id=current_user.id,
                exclude_current_filename=False,
                exclude_filenames=cfg["exclude_filenames"],
                limit=PAGE_SIZE,
                offset=offset,
            )
        else:
            sessions = get_saved_interview_list(
                filename=None,
                user_id=current_user.id,
                exclude_current_filename=False,
                exclude_filenames=cfg["exclude_filenames"],
                exclude_newly_started_sessions=True,
                limit=PAGE_SIZE,
                offset=offset,
            )
            # get_saved_interview_list() has a bug where
            # exclude_filenames is ignored (it loops over an empty list)
            sessions = [
                s
                for s in sessions
                if not any(
                    s["filename"] == excl
                    or (":" not in excl and s["filename"].startswith(excl))
                    for excl in cfg["exclude_filenames"]
                )
            ]

        csrf_token = generate_csrf()
        rows = _render_session_rows(sessions, csrf_token, cfg["enable_answer_sets"])

        new_form_button = f"""
        <a class="btn btn-primary btn-md" href="{ escape(cfg['new_form_url'] or '#') }">
            <i class="fa-solid fa-circle-plus" aria-hidden="true"></i> { escape(cfg['new_form_label']) }
        </a>
        """
        page_intro = (
            f"<p>{ escape(cfg['page_intro']) }</p>" if cfg["page_intro"] else ""
        )

        filename_options = get_combined_filename_list(user_id=current_user.id)
        filename_dropdown_options = ""
        for option in filename_options:
            for fname, nice_name in option.items():
                selected = " selected" if fname == limit_filename else ""
                filename_dropdown_options += f'<option value="{ escape(fname) }"{ selected }>{ escape(nice_name) }</option>'

        search_box = f"""
        <form method="GET" action="{ url_for('al_interview_list') }">
            <p class="small text-muted mb-1">Use a keyword to find results that match the title or description of a form.</p>
            <div class="d-flex flex-wrap align-items-end gap-2 mb-2">
                <div>
                    <label for="limit_filename" class="d-block small mb-1">Limit by form title (optional)</label>
                    <select id="limit_filename" name="limit_filename" class="form-select form-select-sm" style="width:auto;">
                        <option value="">All forms</option>
                        { filename_dropdown_options }
                    </select>
                </div>
                <div>
                    <label for="keyword" class="d-block small mb-1">Search term (optional)</label>
                    <input id="keyword" type="text" name="keyword" value="{ escape(keyword) }" class="form-control form-control-sm">
                </div>
                <button type="submit" class="btn btn-sm btn-primary">Search</button>
            </div>
        </form>
        """
        delete_all_form = f"""
        <form method="POST" action="{ url_for('al_interview_list_delete_all') }" onsubmit="return confirm('Delete all your sessions? This cannot be undone.')">
            <input type="hidden" name="csrf_token" value="{ csrf_token }">
            <button type="submit" class="btn btn-sm btn-danger">Delete All</button>
        </form>
        """

        pagination = '<nav aria-label="Page navigation"><ul class="pagination justify-content-center">'
        if page > 0:
            prev_args = {"page": page - 1}
            if keyword:
                prev_args["keyword"] = keyword
            if limit_filename:
                prev_args["limit_filename"] = limit_filename
            pagination += f'<li class="page-item"><a class="page-link" href="{ url_for("al_interview_list", **prev_args) }">Previous</a></li>'
        if len(sessions) >= PAGE_SIZE:
            next_args = {"page": page + 1}
            if keyword:
                next_args["keyword"] = keyword
            if limit_filename:
                next_args["limit_filename"] = limit_filename
            pagination += f'<li class="page-item"><a class="page-link" href="{ url_for("al_interview_list", **next_args) }">Next</a></li>'
        pagination += "</ul></nav>"

        content = f"""
        <h1 class="da-page-header h3">{ escape(cfg['page_heading']) } { new_form_button }</h1>
        { page_intro }
        { search_box }
        { rows }
        { pagination }
        { delete_all_form }
        """

        return render_template_string(PAGE_TEMPLATE, content=content)

    @app.route("/al_interview_list/delete", methods=["POST"])
    @login_required
    def al_interview_list_delete():
        """Delete a single saved session"""
        filename = request.form.get("filename")
        session_id = request.form.get("session")
        if not filename or not session_id:
            flash("Missing information, could not delete.", "danger")
            return redirect(url_for("al_interview_list"))
        _set_current_info()
        try:
            user_interviews(
                user_id=current_user.id,
                action="delete",
                filename=filename,
                session=session_id,
            )
            flash("Deleted.", "success")
        except Exception as e:
            log(f"al_interview_list_delete error: {e}")
            flash("Could not delete that item.", "danger")
        return redirect(url_for("al_interview_list"))

    @app.route("/al_interview_list/delete_all", methods=["POST"])
    @login_required
    def al_interview_list_delete_all():
        """Delete all of the current user's saved sessions."""
        _set_current_info()
        try:
            delete_interview_sessions(
                user_id=current_user.id, exclude_current_filename=False
            )
            flash("Deleted all saved sessions.", "success")
        except Exception as e:
            log(f"al_interview_list_delete_all error: {e}")
            flash("Could not delete sessions.", "danger")
        return redirect(url_for("al_interview_list"))

    @app.route("/al_interview_list/rename", methods=["POST"])
    @login_required
    def al_interview_list_rename():
        """Rename a single saved session"""
        filename = request.form.get("filename")
        session_id = request.form.get("session")
        new_name = request.form.get("new_name")
        if not filename or not session_id or not new_name:
            flash("Missing information, could not rename.", "danger")
            return redirect(url_for("al_interview_list"))
        _set_current_info()
        try:
            rename_interview_answers(
                filename=filename, session_id=session_id, new_name=new_name
            )
            flash("Renamed.", "success")
        except Exception as e:
            log(f"al_interview_list_rename error: {e}")
            flash("Could not rename that item.", "danger")
        return redirect(url_for("al_interview_list"))

    @app.route("/al_interview_list/copy_to_answer_set", methods=["POST"])
    @login_required
    def al_interview_list_copy():
        """Copy a single session's answers into a new answer set"""
        filename = request.form.get("filename")
        session_id = request.form.get("session")
        new_name = request.form.get("new_name")
        original_interview_filename = (
            request.form.get("original_interview_filename") or filename
        )
        if not filename or not session_id or not new_name:
            flash("Missing information, could not copy.", "danger")
            return redirect(url_for("al_interview_list"))
        _set_current_info()
        try:
            save_interview_answers(
                source_filename=filename,
                source_session=session_id,
                metadata={"title": new_name},
                original_interview_filename=original_interview_filename,
            )
            flash("Copied to answer set.", "success")
        except Exception as e:
            log(f"al_interview_list_copy error: {e}")
            flash(
                "Sorry, these answers couldn't be copied right now. Try starting a new form instead.",
                "danger",
            )
        return redirect(url_for("al_interview_list"))

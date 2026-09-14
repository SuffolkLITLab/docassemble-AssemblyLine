# pre-load
from pathlib import Path
from typing import Any

from flask import request, redirect, url_for, flash, render_template_string
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from markupsafe import Markup

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
    _package_name,
)

PAGE_SIZE = 20

PAGE_TEMPLATE = (
    Path(__file__).parent / "data" / "templates" / "al_interview_list_page.html"
).read_text()

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


def _session_view_model(s):
    """Turn one raw saved-session record into the plain data the template needs,
    so AL helper calls stay out of the template itself
    """
    modtime = local_date(s.get("modtime"))
    return {
        "title": nice_interview_title(s),
        "subtitle": nice_interview_subtitle(s),
        "filename": s["filename"],
        "session_key": s["key"],
        "url": interview_url(i=s["filename"], session=s["key"], style="full"),
        "date_str": modtime.strftime("%B %-d, %Y"),
        "time_str": modtime.strftime("%-I:%M %p"),
        # radial_progress() returns HTML we generate ourselves, so it's
        # wrapped in Markup to skip escaping. Everything else here is plain text and gets Jinja's normal autoescaping.
        "progress_html": Markup(radial_progress(s)),
    }


if "al_interview_list" not in app.view_functions:

    @app.route("/al_interview_list", methods=["GET"])
    @login_required
    def al_interview_list() -> str:
        """Show the current user's saved interview sessions, with search and paging.

        Returns:
            str: the rendered page.
        """
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

        session_count = len(sessions)
        session_view_models = [_session_view_model(s) for s in sessions]

        filename_options = get_combined_filename_list(user_id=current_user.id)

        return render_template_string(
            PAGE_TEMPLATE,
            cfg=cfg,
            sessions=session_view_models,
            filename_options=filename_options,
            csrf_token=generate_csrf(),
            page=page,
            page_size=PAGE_SIZE,
            keyword=keyword,
            limit_filename=limit_filename,
            package_name=_package_name(),
        )

    @app.route("/al_interview_list/delete", methods=["POST"])
    @login_required
    def al_interview_list_delete() -> Any:
        """Delete a single saved session.

        Returns:
            Any: a redirect back to the interview list page
        """
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
    def al_interview_list_delete_all() -> Any:
        """Delete all of the current user's saved sessions

        Returns:
            Any: a redirect back to the interview list page
        """
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
    def al_interview_list_rename() -> Any:
        """Rename a single saved session

        Returns:
            Any: a redirect back to the interview list page
        """
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
    def al_interview_list_copy() -> Any:
        """Copy a single session's answers into a new answer set

        Returns:
            Any: a redirect back to the interview list page
        """
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

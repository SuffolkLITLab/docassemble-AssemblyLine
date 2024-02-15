from collections.abc import Iterable
from typing import List, Dict, Any, Optional, Set, Union, Optional
from docassemble.base.util import (
    all_variables,
    as_datetime,
    create_session,
    DADateTime,
    DAFile,
    DAFileCollection,
    DAFileList,
    DALazyTemplate,
    DAList,
    DAObject,
    DASet,
    format_time,
    get_config,
    get_language,
    get_default_timezone,
    get_session_variables,
    interview_menu,
    interview_url,
    log,
    set_parts,
    set_session_variables,
    set_variables,
    url_action,
    url_ask,
    user_has_privilege,
    user_info,
    user_logged_in,
    validation_error,
    variables_snapshot_connection,
    word,
)
from docassemble.webapp.db_object import init_sqlalchemy
from sqlalchemy.sql import text
from docassemble.base.functions import server, safe_json, serializable_dict
from .al_document import (
    ALDocument,
    ALDocumentBundle,
    ALExhibit,
    ALExhibitList,
    ALStaticDocument,
)
import json
import os
import re

try:
    import zoneinfo  # type: ignore
except ImportError:
    import backports.zoneinfo as zoneinfo  # type: ignore

__all__ = [
    "al_session_store_default_filename",
    "config_with_language_fallback",
    "delete_interview_sessions",
    "export_interview_variables",
    "get_filtered_session_variables_string",
    "get_filtered_session_variables",
    "get_interview_metadata",
    "get_saved_interview_list",
    "interview_list_html",
    "is_file_like",
    "is_valid_json",
    "load_interview_answers",
    "load_interview_json",
    "rename_current_session",
    "rename_interview_answers",
    "save_interview_answers",
    "session_list_html",
    "set_current_session_metadata",
    "set_interview_metadata",
]

db = init_sqlalchemy()

al_sessions_variables_to_remove: Set = {
    # Internal fields
    "_internal",
    "allow_cron",
    "device_local",
    "feedback_form",
    "github_repo_name",
    "github_user",
    "interview_short_title",
    "metadata_title",
    "multi_user",
    "nav",
    "session_local",
    "speak_text",
    "url_args",
    "user_local",
    # Database-like fields we don't need to copy
    "all_courts",
    "court_emails",
    "macourts",
    # AssemblyLine form-specific fields
    "al_form_type",
    "al_version",
    "form_approved_for_email_filing",
    "interview_metadata",
    "package_name",
    "package_version_number",
    "user_has_saved_answers",
    # Variables that should be calculated fresh
    "about_this_interview_version_info",
    "al_court_bundle",
    "AL_DEFAULT_COUNTRY",
    "AL_DEFAULT_LANGUAGE",
    "AL_DEFAULT_OVERFLOW_MESSAGE",
    "AL_DEFAULT_STATE",
    "al_enable_incomplete_downloads",
    "al_interview_languages",
    "al_logo",
    "AL_ORGANIZATION_HOMEPAGE",
    "AL_ORGANIZATION_TITLE",
    "al_terms_of_use",
    "al_user_bundle",
    "al_user_default_language",
    "al_user_language",
    "case_name",
    "enable_al_language",
    "signature_date",
    # Variables from saving/loading state
    "al_formatted_sessions",
    "al_session_store_default_filename",
    "al_sessions_copy_success",
    "al_sessions_fast_forward_filtered_vars",
    "al_sessions_fast_forward_session",
    "al_sessions_filtered_vars",
    "al_sessions_interview_title",
    "al_sessions_launch_new_session",
    "al_sessions_list",
    "al_sessions_new_session_id",
    "al_sessions_preview_variables",
    "al_sessions_save_session_snapshot_success",
    "al_sessions_save_session_snapshot",
    "al_sessions_snapshot_label",
    "al_sessions_snapshot_results",
    "al_sessions_source_session",
    "al_sessions_url_ask_fast_forward",
    "al_sessions_url_ask_snapshot",
    "al_sessions_variables_to_remove_from_new_interview",
    "al_sessions_variables_to_remove",
    "al_sessions_additional_variables_to_filter",
    "al_simple_filtered_vars",
    "filtered_vars_tmp",
    "is_file_like",
    "simple_filtered_vars_tmp",
    # Some type annotations from Typing that seem plausible we'll use (not everything)
    "Annotated",
    "Any",
    "AnyStr",
    "BinaryIO",
    "Callable",
    "ChainMap",
    "ClassVar",
    "Concatenate",
    "Counter",
    "DefaultDict",
    "Deque",
    "Dict",
    "Final",
    "FrozenSet",
    "Generic",
    "IO",
    "Iterable",
    "List",
    "Match",
    "NamedTuple",
    "NewType",
    "Optional",
    "OrderedDict",
    "ParamSpec",
    "Pattern",
    "Protocol",
    "Set",
    "Text",
    "TextIO",
    "Tuple",
    "TypedDict",
    "TypeGuard",
    "TypeLiteral",
    "TypeVar",
    "Union",
    # Variables that should always be created by code, so safe to recalculate
    "al_menu_items",
    "al_menu_items_default_items",
    "al_menu_items_custom_items",
    "menu_items",
    "user_role",
    "user_started_case",
}

al_sessions_variables_to_remove_from_new_interview = [
    "docket_number",
    "docket_numbers",
    "user_ask_role",
]

system_interviews: List[Dict[str, Any]] = interview_menu()


def _package_name(package_name: Optional[str] = None):
    """Get package name without the name of the current module, like: docassemble.ALWeaver instead of
    docassemble.ALWeaver.advertise_capabilities

    Args:
        package_name (str, optional): The package name to process. If `None`, will use the existing package name `__name__` instead

    Returns:
        str: The package name without the current module name.
    """
    if not package_name:
        package_name = __name__
    try:
        return ".".join(package_name.split(".")[:-1])
    except:
        return package_name


al_session_store_default_filename = f"{_package_name()}:al_saved_sessions_store.yml"


def is_file_like(obj: Any) -> bool:
    """
    Return True if the object is a file-like object.

    Args:
        obj (Any): The object to test

    Returns:
        bool: True if the object is a file-like object.
    """
    if isinstance(
        obj,
        (
            DAFile,
            DAFileCollection,
            DAFileList,
            ALDocument,
            ALDocumentBundle,
            ALStaticDocument,
            ALExhibit,
            ALExhibitList,
            DALazyTemplate,
        ),
    ):
        return True

    return False


def set_interview_metadata(
    filename: str, session_id: int, data: Dict, metadata_key_name="metadata"
) -> None:
    """Add searchable interview metadata for the specified filename and session ID.
    Intended to be used to add an interview title, etc.
    Standardized metadata dictionary:
    - title
    - subtitle
    - original_interview_filename
    - variable_count

    Args:
        filename (str): The filename of the interview to add metadata for
        session_id (int): The session ID of the interview to add metadata for
        data (Dict): The metadata to add
        metadata_key_name (str, optional): The name of the metadata key. Defaults to "metadata".
    """
    server.write_answer_json(
        session_id, filename, safe_json(data), tags=metadata_key_name, persistent=True
    )


def get_interview_metadata(
    filename: str, session_id: int, metadata_key_name: str = "metadata"
) -> Dict[str, Any]:
    """Retrieve the unencrypted metadata associated with an interview.
    We implement this with the docassemble jsonstorage table and a dedicated `tag` which defaults to `metadata`.

    Args:
        filename (str): The filename of the interview to retrieve metadata for
        session_id (int): The session ID of the interview to retrieve metadata for
        metadata_key_name (str, optional): The name of the metadata key. Defaults to "metadata".

    Returns:
        Dict[str, Any]: The metadata associated with the interview
    """
    conn = variables_snapshot_connection()
    with conn.cursor() as cur:
        query = "select data from jsonstorage where filename=%(filename)s and tags=%(tags)s and key=%(session_id)s"
        cur.execute(
            query,
            {"filename": filename, "tags": metadata_key_name, "session_id": session_id},
        )
        val = cur.fetchone()
    conn.close()
    if val and len(val):
        return val[0]  # cur.fetchone() returns a tuple
    return val or {}


def get_saved_interview_list(
    filename: Optional[str] = al_session_store_default_filename,
    user_id: Union[int, str, None] = None,
    metadata_key_name: str = "metadata",
    limit: int = 50,
    offset: int = 0,
    filename_to_exclude: str = "",
    exclude_current_filename: bool = True,
    exclude_filenames: Optional[List[str]] = None,
    exclude_newly_started_sessions: bool = False,
) -> List[Dict[str, Any]]:
    """Get a list of saved sessions for the specified filename. If the save_interview_answers function was used
    to add metadata, the result list will include columns containing the metadata.
    If the user is a developer or administrator, setting user_id = None will list all interviews on the server. Otherwise,
    the user is limited to their own sessions.

    Setting `exclude_newly_started_sessions` to True will exclude any results from the list that are still on
    "step 1". Note that while this may be useful to filter out interviews that were accidentally started
    and likely do not need to be resumed, it will also have the side effect of excluding all answer sets from the
    results. Answer sets generally have exactly one "step", which is the step where information was copied from
    an existing interview to the answer set.

    Args:
        filename (str, optional): The filename of the interview to retrieve sessions for. Defaults to al_session_store_default_filename.
        user_id (Union[int, str, None], optional): The user ID to retrieve sessions for. Defaults to None.
        metadata_key_name (str, optional): The name of the metadata key. Defaults to "metadata".
        limit (int, optional): The maximum number of results to return. Defaults to 50.
        offset (int, optional): The offset to start returning results from. Defaults to 0.
        filename_to_exclude (str, optional): The filename to exclude from the results. Defaults to "".
        exclude_current_filename (bool, optional): Whether to exclude the current filename from the results. Defaults to True.
        exclude_filenames (Optional[List[str]], optional): A list of filenames to exclude from the results. Defaults to None.
        exclude_newly_started_sessions (bool, optional): Whether to exclude sessions that are still on "step 1". Defaults to False.

    Returns:
        List[Dict[str, Any]]: A list of saved sessions for the specified filename.
    """
    # We use an `offset` instead of a cursor because it is simpler and clearer
    # while it appears to be performant enough for real-world usage.
    # Up to ~ 1,000 sessions performs well and is higher than expected for an end-user
    get_sessions_query = text(
        """
           SELECT  userdict.indexno
           ,userdict.filename as filename
           ,num_keys
           ,userdictkeys.user_id as user_id
           ,userdict.modtime as modtime
           ,userdict.key as key
           ,jsonstorage.data->'auto_title' as auto_title
           ,jsonstorage.data->'title' as title
           ,jsonstorage.data->'description' as description
           ,jsonstorage.data->'steps' as steps
           ,jsonstorage.data->'progress' as progress
           ,jsonstorage.data->'original_interview_filename' as original_interview_filename
           ,jsonstorage.data->'answer_count' as answer_count
           ,jsonstorage.data as data
    FROM userdict 
    NATURAL JOIN 
    (
      SELECT  key
             ,MAX(modtime) AS modtime
             ,COUNT(key)   AS num_keys
      FROM userdict
      GROUP BY  key
    ) mostrecent
    LEFT JOIN userdictkeys
    ON userdictkeys.key = userdict.key
    LEFT JOIN jsonstorage
    ON userdict.key = jsonstorage.key AND (jsonstorage.tags = :metadata)
    WHERE (userdictkeys.user_id = :user_id or :user_id is null)
    
    AND
    (userdict.filename = :filename OR :filename is null)
    AND (userdict.filename NOT IN :filenames_to_exclude)
    AND (NOT :exclude_newly_started_sessions OR num_keys > 1)
    ORDER BY modtime desc 
    LIMIT :limit
    OFFSET :offset;
    """
    )

    if offset < 0:
        offset = 0

    if not filename:
        filename = None  # Explicitly treat empty string as equivalent to None
    if exclude_current_filename:
        current_filename = user_info().filename
    else:
        current_filename = ""
    if not filename_to_exclude:
        filename_to_exclude = ""
    filenames_to_exclude = []
    if exclude_filenames:
        filenames_to_exclude.extend(exclude_filenames)
    filenames_to_exclude.extend([current_filename, filename_to_exclude])
    if user_id is None:
        if user_logged_in():
            user_id = user_info().id
        else:
            log("Asked to get interview list for user that is not logged in")
            return []

    if user_id == "all":
        if user_has_privilege(["developer", "admin"]):
            user_id = None
        elif user_logged_in():
            user_id = user_info().id
            log(
                f"User {user_info().email} does not have permission to list interview sessions belonging to other users"
            )
        else:
            log("Asked to get interview list for user that is not logged in")
            return []

    with db.connect() as con:
        rs = con.execute(
            get_sessions_query,
            {
                "metadata": metadata_key_name,
                "user_id": user_id,
                "filename": filename,
                "limit": limit,
                "offset": offset,
                "filenames_to_exclude": tuple(filenames_to_exclude),
                "exclude_newly_started_sessions": exclude_newly_started_sessions,
            },
        )
    sessions = []
    for session in rs:
        sessions.append(dict(session._mapping))

    return sessions


def delete_interview_sessions(
    user_id: Optional[int] = None,
    filename_to_exclude: str = al_session_store_default_filename,
    exclude_current_filename: bool = True,
) -> None:
    """
    Delete all sessions for the specified user, excluding the current filename
    and by default, the intentionally saved "answer sets". Created because
    interview_list(action="delete_all") is both quite slow and because it deletes answer sets.

    Args:
        user_id (Optional[int], optional): The user ID to delete sessions for. Defaults to None.
        filename_to_exclude (str, optional): The filename to exclude from the results. Defaults to al_session_store_default_filename.
        exclude_current_filename (bool, optional): Whether to exclude the current filename from the results. Defaults to True.
    """
    if not user_logged_in():
        log(
            "User that is not logged in does not have permission to delete any sessions"
        )
        return None
    delete_sessions_query = text(
        """
        DELETE FROM userdictkeys
        WHERE user_id = :user_id
        AND
        filename != :filename_to_exclude
        AND
        filename != :current_filename
        ;
        """
    )
    if not user_id:
        user_id = user_info().id
    if user_id != user_info().id and not user_has_privilege(["developer", "admin"]):
        user_id = user_info().id
        log(
            f"User {user_info().id} does not have permission to delete sessions that do not belong to them."
        )
    if exclude_current_filename:
        current_filename = user_info().filename or ""
    else:
        current_filename = ""
    if not filename_to_exclude:
        filename_to_exclude = ""

    log(f"Deleting sessions with {user_id} {filename_to_exclude} {current_filename}")

    with db.connect() as connection:
        connection.execute(
            delete_sessions_query,
            {
                "user_id": user_id,
                "filename_to_exclude": filename_to_exclude,
                "current_filename": current_filename,
            },
        )


def interview_list_html(
    filename: str = al_session_store_default_filename,
    user_id: Union[int, str, None] = None,
    metadata_key_name: str = "metadata",
    exclude_newly_started_sessions=False,
    # name_label: str = word("Title"),
    date_label: str = word("Date"),
    details_label: str = word("Details"),
    actions_label: str = word("Actions"),
    delete_label: str = word("Delete"),
    view_label: str = word("View"),
    load_action: str = "al_sessions_fast_forward_session",
    delete_action: str = "al_sessions_delete_session",
    view_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    display_interview_title: bool = True,
    show_view_button: bool = True,
) -> str:
    """Return a string containing an HTML-formatted table with the list of saved answers
    associated with the specified filename.

    Designed to return a list of "answer sets" and by default clicking a title will
    trigger an action to load the answers into the current session. This only works as
    designed when inside an AssemblyLine line interview.

    `exclude_newly_started_sessions` should almost always be set to False, because most answer sets
    are on "page 1" (exactly 1 step was taken to copy the answers and the user isn't able to interact with the answer set
    itself in a way that adds additional steps)

    Args:
        filename (str, optional): Name of the file. Defaults to `al_session_store_default_filename`.
        user_id (Union[int, str, None], optional): User's ID. Defaults to None.
        metadata_key_name (str, optional): Name of the metadata key. Defaults to "metadata".
        exclude_newly_started_sessions (bool, optional): If True, newly started sessions are excluded. Defaults to False.
        date_label (str, optional): Label for the date column. Defaults to translated word "Date".
        details_label (str, optional): Label for the details column. Defaults to translated word "Details".
        actions_label (str, optional): Label for the actions column. Defaults to translated word "Actions".
        delete_label (str, optional): Label for the delete action. Defaults to translated word "Delete".
        view_label (str, optional): Label for the view action. Defaults to translated word "View".
        load_action (str, optional): Name of the load action. Defaults to "al_sessions_fast_forward_session".
        delete_action (str, optional): Name of the delete action. Defaults to "al_sessions_delete_session".
        view_only (bool, optional): If True, only view is allowed. Defaults to False.
        limit (int, optional): Limit for the number of sessions returned. Defaults to 50.
        offset (int, optional): Offset for the session list. Defaults to 0.
        display_interview_title (bool, optional): If True, displays the title of the interview. Defaults to True.
        show_view_button (bool, optional): If True, shows the view button. Defaults to True.

    Returns:
        str: HTML-formatted table containing the list of saved answers.
    """
    # TODO: Currently, using the `word()` function for translation, but templates
    # might be more flexible
    answers = get_saved_interview_list(
        filename=filename,
        user_id=user_id,
        metadata_key_name=metadata_key_name,
        limit=limit,
        offset=offset,
        exclude_current_filename=False,
        exclude_newly_started_sessions=exclude_newly_started_sessions,
    )

    if not answers:
        return ""

    table = '<div class="table-responsive"><table class="table table-striped al-saved-answer-table text-break">'
    table += f"""
    <thead>
      <th scope="col">
        &nbsp;
      </th>
      <th scope="col">{ date_label }</th>
      <th scope="col">{ details_label }</th>
      <th scope="col">{ actions_label }</th>
      </th>
    </thead>
    <tbody>
"""

    for answer in answers:
        answer = dict(answer)
        # Never display the current interview session
        if answer.get("key") == user_info().session:
            continue
        table += """<tr class="al-saved-answer-table-row">"""
        if view_only:
            table += f"""
            <td>{ nice_interview_subtitle(answer) or nice_interview_title(answer) }</td>
            """
        else:
            table += f"""
            <td class="text-break"><a href="{ url_action(load_action, i=answer.get("filename"), session=answer.get("key")) }">{ nice_interview_subtitle(answer) or nice_interview_title(answer) }</a></td>
            """
        table += f"""
        <td>{ as_datetime(answer.get("modtime")) }</td>
        <td>Page { answer.get("steps") or answer.get("num_keys") }"""
        if display_interview_title:
            table += f"""
                 <br/>{answer.get("original_interview_filename") or answer.get("filename") or "" }
            """
        table += f"""
        </td>
        <td>
          <a href="{ url_action(delete_action, filename=answer.get("filename"), session=answer.get("key")) }"><i class="far fa-trash-alt" title="{ delete_label }" aria-hidden="true"></i><span class="sr-only">{ delete_label }</span></a>
          """
        if show_view_button:
            table += f"""
                <a target="_blank" href="{ interview_url(i=answer.get("filename"), session=answer.get("key")) }">
                    <i class="far fa-eye" aria-hidden="true" title="{ view_label }"></i>
                    <span class="sr-only">{ view_label }</span>
                </a>
            """
        table += """
        </td>
        """
        table += "</tr>"
    table += "</tbody></table></div>"

    return table


def nice_interview_title(
    answer: Dict[str, str],
) -> str:
    """
    Return a human readable version of the interview name. Will try several strategies
    in descending priority order.
    1. Try looking up the interview title from the `dispatch` directive
    1. Try removing the package and path from the filename and replace _ with spaces.
    4. Finally, return "Untitled interview" or translated phrase from system-wide words.yml

    Args:
        answer (Dict[str, str]): The answer dictionary to get the interview title from

    Returns:
        str: The human readable interview title
    """
    if answer.get("filename"):
        for interview in system_interviews:
            if answer.get("filename") == interview.get("filename") and interview.get(
                "title"
            ):
                return interview["title"]
        filename = os.path.splitext(os.path.basename(answer.get("filename", "")))[0]
        if ":" in filename:
            filename = filename.split(":")[1]
        return filename.replace("_", " ").capitalize()
    else:
        return word("Untitled interview")


def pascal_to_zwspace(text: str) -> str:
    """
    Insert a zero-width space into words that are PascalCased to help
    with word breaks on small viewports.

    Args:
        text (str): The text to insert zero-width spaces into

    Returns:
        str: The text with zero-width spaces inserted
    """
    re_outer = re.compile(r"([^A-Z ])([A-Z])")
    re_inner = re.compile(r"(?<!^)([A-Z])([^A-Z])")
    return re_outer.sub(r"\1​\2", re_inner.sub(r"​\1\2", text))


def nice_interview_subtitle(answer: Dict[str, str], exclude_identical=True) -> str:
    """
    Return first defined of the "title" metadata, the "auto_title" metadata, or empty string.

    If exclude_identical, return empty string when title is the same as the subtitle.

    Args:
        answer (Dict[str, str]): The answer dictionary to get the interview subtitle from
        exclude_identical (bool, optional): If True, excludes the subtitle if it is identical to the title. Defaults to True.

    Returns:
        str: The human readable interview subtitle
    """
    if answer.get("title"):
        return pascal_to_zwspace(answer["title"])
    elif answer.get("auto_title") and (
        not exclude_identical
        or not (
            answer.get("auto_title", "").lower() == nice_interview_title(answer).lower()
        )
    ):
        return pascal_to_zwspace(answer["auto_title"])
    return ""


def radial_progress(answer: Dict[str, Union[str, int]]) -> str:
    """
    Return HTML for a radial progress bar, or the number of steps if progress isn't available in the metadata.

    Args:
        answer (Dict[str, Union[str, int]]): The answer dictionary to get the interview progress from

    Returns:
        str: the HTML as a string
    """
    if not answer.get("progress"):
        return f"Page {answer.get('steps') or answer.get('num_keys') or 1}"

    # For simulation purposes, assume a form is complete at page 30
    progress: int = (
        int(answer["progress"])
        or int(answer["steps"])
        or (int(answer["num_keys"]) or 1) * 4
    )

    # Get a number divisible by 10 and between 0 and 100 (percentage)
    nearest_10 = min(max(round(progress / 10) * 10, 0), 100)
    return f"""
      <div class="radialProgressBar progress-{ nearest_10 }">
          <div class="overlay">{ nearest_10 }%</div>
        </div>
    """


def local_date(utcstring: Optional[str]) -> DADateTime:
    """
    Return a localized date from a UTC string.

    Args:
        utcstring (Optional[str]): The UTC string to convert to a localized date

    Returns:
        DADateTime: The localized date
    """
    if not utcstring:
        return DADateTime()
    return (
        as_datetime(utcstring)
        .replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
        .astimezone(zoneinfo.ZoneInfo(get_default_timezone()))
    )


def session_list_html(
    filename: Optional[str] = None,
    user_id: Union[int, str, None] = None,
    metadata_key_name: str = "metadata",
    filename_to_exclude: str = al_session_store_default_filename,
    exclude_current_filename: bool = True,
    exclude_filenames: Optional[List[str]] = None,
    exclude_newly_started_sessions: bool = False,
    name_label: str = word("Title"),
    date_label: str = word("Date modified"),
    details_label: str = word("Progress"),
    actions_label: str = word("Actions"),
    delete_label: str = word("Delete"),
    rename_label: str = word("Rename"),
    rename_action: str = "interview_list_rename_action",
    delete_action: str = "interview_list_delete_session",
    copy_action: str = "interview_list_copy_action",
    clone_label: str = word("Copy as answer set"),
    show_title: bool = True,
    show_copy_button: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """Return a string containing an HTML-formatted table with the list of user sessions.
    While interview_list_html() is for answer sets, this feature is for standard
    user sessions. The results exclude the answer set filename by default.

    Args:
        filename (Optional[str], optional): Name of the file. Defaults to None.
        user_id (Union[int, str, None], optional): User's ID. Defaults to None.
        metadata_key_name (str, optional): Name of the metadata key. Defaults to "metadata".
        filename_to_exclude (str, optional): Name of the file to exclude. Defaults to `al_session_store_default_filename`.
        exclude_current_filename (bool, optional): If True, excludes the current filename. Defaults to True.
        exclude_filenames (Optional[List[str]], optional): List of filenames to exclude. Defaults to None.
        exclude_newly_started_sessions (bool, optional): If True, excludes newly started sessions. Defaults to False.
        name_label (str, optional): Label for the session name/title. Defaults to translated word "Title".
        date_label (str, optional): Label for the date column. Defaults to translated word "Date modified".
        details_label (str, optional): Label describing the progress of the session. Defaults to translated word "Progress".
        actions_label (str, optional): Label for actions applicable to the session. Defaults to translated word "Actions".
        delete_label (str, optional): Label for the delete action. Defaults to translated word "Delete".
        rename_label (str, optional): Label for the rename action. Defaults to translated word "Rename".
        rename_action (str, optional): Name of the rename action. Defaults to "interview_list_rename_action".
        delete_action (str, optional): Name of the delete action. Defaults to "interview_list_delete_session".
        copy_action (str, optional): Name of the copy action. Defaults to "interview_list_copy_action".
        clone_label (str, optional): Label for the action to copy as an answer set. Defaults to translated word "Copy as answer set".
        show_title (bool, optional): If True, shows the title of the session. Defaults to True.
        show_copy_button (bool, optional): If True, show a copy button for answer sets. Defaults to True.
        limit (int, optional): Limit for the number of sessions returned. Defaults to 50.
        offset (int, optional): Offset for the session list. Defaults to 0.

    Returns:
        str: HTML-formatted table containing the list of user sessions.
    """

    # TODO: think through how to translate this function. Templates probably work best but aren't
    # convenient to pass around
    answers = get_saved_interview_list(
        filename=filename,
        user_id=user_id,
        metadata_key_name=metadata_key_name,
        limit=limit,
        offset=offset,
        filename_to_exclude=filename_to_exclude,
        exclude_current_filename=exclude_current_filename,
        exclude_filenames=exclude_filenames,
        exclude_newly_started_sessions=exclude_newly_started_sessions,
    )

    if not answers:
        return ""

    table = '<div class="table-responsive"><table class="table table-striped al-saved-answer-table">'
    table += f"""
    <thead>
      <th scope="col">
       { name_label }
      </th>
      <th scope="col">{ date_label }</th>
      <th scope="col">{ details_label }</th>
      <th scope="col">{ actions_label }</th>
      </th>
    </thead>
    <tbody>
"""

    for answer in answers:
        answer = dict(answer)
        # Never display the current interview session
        if answer.get("key") == user_info().session:
            continue
        url_ask_rename = url_ask(
            [
                {"undefine": ["al_sessions_snapshot_new_label"]},
                {
                    "action": rename_action,
                    "arguments": {
                        "session": answer.get("key"),
                        "filename": answer.get("filename"),
                        "title": nice_interview_subtitle(answer)
                        or nice_interview_title(answer),
                    },
                },
            ]
        )
        url_ask_copy = url_ask(
            [
                {"undefine": ["al_sessions_copy_as_answer_set_label"]},
                {
                    "action": copy_action,
                    "arguments": {
                        "session": answer.get("key"),
                        "filename": answer.get("filename"),
                        "title": answer.get("title") or "",
                        "original_interview_filename": nice_interview_title(answer),
                    },
                },
            ]
        )
        url_ask_delete = url_ask(
            [
                {
                    "action": delete_action,
                    "arguments": {
                        "session": answer.get("key"),
                        "filename": answer.get("filename"),
                    },
                }
            ]
        )

        table += """<tr class="al-saved-answer-table-row">"""
        if show_title:
            table += f"""
            <td class="text-break">
            <a class="al-session-form-title" href="{ interview_url(i=answer.get("filename"), session=answer.get("key")) }">{ nice_interview_title(answer) }</a>
            {"<br/>" if nice_interview_subtitle(answer) else ""}
            <span class="al-session-form-subtitle">{ nice_interview_subtitle(answer) if nice_interview_subtitle(answer) else "" }</span>
            </td>
            """
        else:
            table += f"""
            <td class="text-break">
            <a class="al-session-form-title" href="{ interview_url(i=answer.get("filename"), session=answer.get("key")) }">{ nice_interview_subtitle(answer) or nice_interview_title(answer) }</a>
            </td>
            """
        table += f"""
        <td>
            <span class="al-session-date-modified">{ local_date(answer.get("modtime")) }</span> <br/>
            <span class="al-session-time-modified">{ format_time(local_date(answer.get("modtime")).time(), format="h:mm a") }</span>
        </td>
        <td class="al-progress-box">{ radial_progress(answer) }
        </td>
        <td>
          <a class="al-sessions-action-rename" href="{ url_ask_rename }"><i class="fa-solid fa-tag" aria-hidden="true" title="{ rename_label }"></i><span class="sr-only">{ rename_label }</span></a>
        """
        if (
            get_config("assembly line", {}).get("enable answer sets")
            and show_copy_button
        ):
            table += f"""
          &nbsp;
          <a class="al-sessions-actions-clone" href="{ url_ask_copy }"><i class="fa-regular fa-clone" aria-hidden="true" title="{clone_label}"></i><span class="sr-only">{ clone_label }</span></a>
          """
        table += f"""
          &nbsp;
          <a href="{ url_ask_delete }" class="text-danger al-delete-session"><i class="far fa-trash-alt text-danger" title="{ delete_label }" aria-hidden="true"></i><span class="sr-only">{ delete_label }</span></a>
        </td>
        """
        table += "</tr>"
    table += "</tbody></table></div>"

    return table


def rename_interview_answers(
    filename: str,
    session_id: int,
    new_name: str,
    metadata_key_name: str = "metadata",
) -> None:
    """Update the 'title' metadata of an interview, as stored in the dedicated `metadata` column, without touching other
    metadata that may be present.

    Args:
        filename (str): The filename of the interview to rename
        session_id (int): The session ID of the interview to rename
        new_name (str): The new name to set for the interview
        metadata_key_name (str, optional): The name of the metadata key. Defaults to "metadata".

    If exception is raised in set_session_variables, this will silently fail but log the error.
    """
    existing_metadata = get_interview_metadata(
        filename, session_id, metadata_key_name=metadata_key_name
    )
    existing_metadata["title"] = new_name
    set_interview_metadata(
        filename, session_id, existing_metadata, metadata_key_name=metadata_key_name
    )
    if session_id == user_info().session:
        set_parts(subtitle=new_name)
    else:
        try:
            set_session_variables(
                filename,
                session_id,
                {"_internal['subtitle']": new_name},
                overwrite=True,
            )
        except:
            log(
                f"Unable to update internal interview subtitle for session {filename}:{session_id} with new name {new_name}"
            )


def set_current_session_metadata(
    data: Dict[str, Any],
    metadata_key_name: str = "metadata",
) -> None:
    """
    Set metadata for the current session, such as the title, in an unencrypted database entry.

    Args:
        data (Dict[str, Any]): The metadata to set
        metadata_key_name (str, optional): The name of the metadata key. Defaults to "metadata".
    """
    return set_interview_metadata(
        user_info().filename,
        user_info().session,
        data,
        metadata_key_name=metadata_key_name,
    )


def rename_current_session(
    new_name: str,
    metadata_key_name: str = "metadata",
) -> None:
    """Update the "title" metadata entry for the current session without changing any other
    metadata that might be present.

    Args:
        new_name (str): The new name to set for the interview
        metadata_key_name (str, optional): The name of the metadata key. Defaults to "metadata".
    """
    return rename_interview_answers(
        user_info().filename,
        user_info().session,
        new_name,
        metadata_key_name=metadata_key_name,
    )


def save_interview_answers(
    filename: str = al_session_store_default_filename,
    variables_to_filter: Union[Set[str], List[str], None] = None,
    metadata: Optional[Dict] = None,
    metadata_key_name: str = "metadata",
    original_interview_filename=None,
    source_filename=None,
    source_session=None,
    additional_variables_to_filter=None,
) -> str:
    """
    Copies the answers from a given session into a new session with a specified interview filename.

    Args:
        filename (str, optional): The desired filename for the new session. Defaults to `al_session_store_default_filename`.
        variables_to_filter (Union[Set[str], List[str], None], optional): The "base" list or set of variables to filter out. Defaults to `al_sessions_variables_to_remove`. There's usually no reason to change this and changing it might break sessions.
        metadata (Optional[Dict], optional): Dictionary containing metadata. Defaults to an empty dictionary.
        metadata_key_name (str, optional): Key name for metadata storage. Defaults to "metadata".
        original_interview_filename (str, optional): Original filename of the interview. Defaults to None.
        source_filename (str, optional): Source filename to get session variables from. Defaults to None.
        source_session (str, optional): Session ID of the source file. Defaults to None.
        additional_variables_to_filter (Union[Set[str], List[str], None], optional): List or set of variables to filter out. Defaults to None.

    Returns:
        str: ID of the new session.
    """
    # Avoid using mutable default parameter
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove
    if not additional_variables_to_filter:
        additional_variables_to_filter = []
    if not metadata:
        metadata = {}

    # Get session variables, from either the specified or current session
    all_vars = get_filtered_session_variables(
        filename=source_filename,
        session_id=source_session,
        variables_to_filter=variables_to_filter,
        additional_variables_to_filter=additional_variables_to_filter,
    )

    try:
        # Sometimes include_internal breaks things
        metadata["steps"] = (
            all_variables(include_internal=True).get("_internal").get("steps", -1)
        )
    except:
        metadata["steps"] = -1

    if original_interview_filename:
        metadata["original_interview_filename"] = original_interview_filename
    else:
        metadata["original_interview_filename"] = all_variables(special="metadata").get(
            "title", user_info().filename.replace(":", " ").replace(".", " ")
        )
    metadata["answer_count"] = len(all_vars)

    # Create a new session
    new_session_id = create_session(filename)

    # Copy in the variables from the specified session
    set_session_variables(filename, new_session_id, all_vars, overwrite=True)

    # Add the metadata
    set_interview_metadata(
        filename, new_session_id, metadata, metadata_key_name=metadata_key_name
    )
    # Make the title display as the subtitle on the "My interviews" page
    if metadata.get("title"):
        try:
            set_session_variables(
                filename,
                new_session_id,
                {"_internal['subtitle']": metadata.get("title")},
                overwrite=True,
            )
        except:
            log(
                f"Unable to set internal interview subtitle for session {filename}:{new_session_id} with name {metadata.get('title')}"
            )

    return new_session_id


def get_filtered_session_variables(
    filename: Optional[str] = None,
    session_id: Optional[int] = None,
    variables_to_filter: Optional[Union[Set[str], List[str]]] = None,
    additional_variables_to_filter: Optional[Union[Set[str], List[str]]] = None,
) -> Dict[str, Any]:
    """
    Retrieves a filtered subset of variables from a specified interview and session.
    If no filename and session ID are given, it will return a filtered list of variables
    from the current interview.

    Args:
        filename (Optional[str], optional): Filename of the session. Defaults to None.
        session_id (Optional[int], optional): Session ID to retrieve variables from. Defaults to None.
        variables_to_filter (Union[Set[str], List[str], None], optional): List or set of variables to exclude. Defaults to `al_sessions_variables_to_remove`.
        additional_variables_to_filter (Union[Set[str], List[str], None], optional): List or set of additional variables to exclude. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary of filtered session variables.
    """
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove
    if not additional_variables_to_filter:
        additional_variables_to_filter = []
    variables_to_filter = set(variables_to_filter).union(
        set(additional_variables_to_filter)
    )

    if filename and session_id:
        all_vars = get_session_variables(filename, session_id, simplify=False)
    else:
        all_vars = all_variables(simplify=False, make_copy=True)

    all_vars = {k: v for k, v in all_vars.items() if k not in variables_to_filter}

    items_to_check = list(all_vars.items())

    while items_to_check:
        key, value = items_to_check.pop()

        # This condition only will apply to "top level" variables
        if is_file_like(value):
            del all_vars[key]
            continue

        if isinstance(value, DAObject):
            # docassemble overrides both __dir__ and __getattr__ for reasons unknown
            # we need to use the base Python versions to get what we expect
            attr_list = list(
                value.__dict__.keys()
            )  # skip over properties etc. vs using object.dir()
            for attr in attr_list:
                attr_val = object.__getattribute__(value, attr)
                if is_file_like(attr_val):
                    delattr(value, attr)
                elif isinstance(attr_val, (DAList, DASet, DAObject)):
                    items_to_check.append(
                        (None, attr_val)
                    )  # mimic dict.items() but the key isn't used

        if isinstance(value, (DAList, DASet)):
            new_elements = []
            for subitem in value.elements:
                if not is_file_like(subitem):
                    new_elements.append(subitem)
                    if isinstance(subitem, (DAList, DASet, DAObject)):
                        items_to_check.append((None, subitem))
            value.elements = (
                new_elements if isinstance(value, DAList) else set(new_elements)
            )

    return all_vars


def get_filtered_session_variables_string(
    filename: Optional[str] = None,
    session_id: Optional[int] = None,
    variables_to_filter: Union[Set[str], List[str], None] = None,
    additional_variables_to_filter: Optional[Union[Set[str], List[str]]] = None,
) -> str:
    """
    Returns a JSON string that represents the filtered contents of a specified filename and session ID.
    If no filename and session ID are provided, the current session's variables will be used.

    Args:
        filename (Optional[str], optional): Filename of the session. Defaults to None.
        session_id (Optional[int], optional): Session ID to retrieve variables from. Defaults to None.
        variables_to_filter (Union[Set[str], List[str], None], optional): List or set of variables to exclude. Defaults to `al_sessions_variables_to_remove`.
        additional_variables_to_filter (Union[Set[str], List[str], None], optional): List or set of additional variables to exclude. Defaults to None.

    Returns:
        str: A JSON-formatted string of filtered session variables.
    """
    simple_vars = serializable_dict(
        get_filtered_session_variables(
            filename=filename,
            session_id=session_id,
            variables_to_filter=variables_to_filter,
            additional_variables_to_filter=additional_variables_to_filter,
        )
    )
    return json.dumps(simple_vars)


def load_interview_answers(
    old_interview_filename: str,
    old_session_id: int,
    new_session: bool = False,
    new_interview_filename: Optional[str] = None,
    variables_to_filter: Optional[List[str]] = None,
    additional_variables_to_filter: Optional[List[str]] = None,
) -> Optional[Union[int, bool]]:
    """
    Loads answers from a specified session. If the parameter `new_session` is set to True, it will create
    a new session with the provided or current interview filename. Otherwise, it will load the answers into
    the active session. This function is primarily used for migrating answers between sessions.

    Args:
        old_interview_filename (str): Filename of the old interview.
        old_session_id (int): Session ID of the old interview.
        new_session (bool, optional): Determines whether to create a new session. Defaults to False.
        new_interview_filename (Optional[str], optional): Filename for the new session. Defaults to None.
        variables_to_filter (Optional[List[str]], optional): List of variables to exclude. Defaults to None.
        additional_variables_to_filter (Optional[List[str]], optional): List of additional variables to exclude. Defaults to None.

    Returns:
        Optional[Union[int, bool]]: ID of the newly created session if `new_session` is True, otherwise True or False based on success.
    """

    old_variables = get_filtered_session_variables(
        filename=old_interview_filename,
        session_id=old_session_id,
        variables_to_filter=variables_to_filter,
        additional_variables_to_filter=additional_variables_to_filter,
    )

    if new_session:
        if not new_interview_filename:
            new_interview_filename = user_info().filename
        new_session_id = create_session(new_interview_filename)
        set_session_variables(new_interview_filename, new_session_id, old_variables)
        return new_session_id
    else:
        try:
            set_variables(old_variables)
            return True
        except:
            return False


def load_interview_json(
    json_string: str,
    new_session: bool = False,
    new_interview_filename: Optional[str] = None,
    variables_to_filter: Optional[List[str]] = None,
) -> Optional[int]:
    """
    Given a JSON string, this function loads the specified variables into a Docassemble session.
    JSON strings containing annotated class names will be transformed into Docassemble objects.
    If the `new_session` argument is not set, the JSON answers will be loaded into the current interview.

    Args:
        json_string (str): A JSON-formatted string containing session variables.
        new_session (bool, optional): Specifies whether to create a new session or load into the current one. Defaults to False.
        new_interview_filename (Optional[str], optional): Filename for the new session. Defaults to None.
        variables_to_filter (Optional[List[str]], optional): List of variables to exclude. Defaults to None.

    Returns:
        Optional[Union[int, bool]]: ID of the newly created session if `new_session` is True, otherwise True or False based on success.
    """
    json_processed = json.loads(json_string)

    if new_session:
        if not new_interview_filename:
            new_interview_filename = user_info().filename
        new_session_id = create_session(new_interview_filename)
        set_session_variables(
            new_interview_filename, new_session_id, json_processed, process_objects=True
        )
        return new_session_id
    else:
        try:
            set_variables(json_processed, process_objects=True)
            return True
        except:
            return False


def export_interview_variables(
    filename: Optional[str] = None,
    session_id: Optional[int] = None,
    variables_to_filter: Union[Set, List[str], None] = None,
    output: DAFile = None,
    additional_variables_to_filter: Union[Set, List[str], None] = None,
) -> DAFile:
    """
    Generates a DAFile containing a JSON representation of a specified session's interview answers.
    The resultant output is compatible with `set_session_variables(process_objects=True)` and
    `set_variables(process_objects=True)` methods.

    Args:
        filename (Optional[str], optional): Filename of the session. Defaults to None.
        session_id (Optional[int], optional): Session ID to retrieve variables from. Defaults to None.
        variables_to_filter (Union[Set, List[str], None], optional): List or set of variables to exclude. Defaults to None.
        output (DAFile, optional): DAFile to write the JSON output to. If None, a new DAFile is created.
        additional_variables_to_filter (Union[Set, List[str], None], optional): List or set of additional variables to exclude. Defaults to None.

    Returns:
        DAFile: DAFile with a JSON representation of the answers
    """
    if not output:
        output = DAFile()
    output.initialize(filename="variables.json")
    variables_string = get_filtered_session_variables_string(
        filename=filename,
        session_id=session_id,
        variables_to_filter=variables_to_filter,
        additional_variables_to_filter=additional_variables_to_filter,
    )

    output.write(variables_string)
    output.commit()
    return output


def is_valid_json(json_string: str) -> bool:
    """
    Checks if the provided string is a valid JSON-formatted string.

    Args:
        json_string (str): The string to be checked for JSON validity.

    Returns:
        bool: True if the string is a valid JSON, otherwise it raises a validation error and returns False.
    """
    try:
        json.loads(json_string)
    except:
        validation_error("Enter a valid JSON-formatted string")
        return False
    return True


def config_with_language_fallback(
    config_key: str, top_level_config_key: Optional[str] = None
) -> Optional[str]:
    """Returns the value of a config key under `assembly line` `interview list` with options to fallback
    to an alternative key at the top level of the global configuration.

    Used in interview_list.yml to allow overriding some of the labels in the interview list
    with options specified in the global configuration. top_level_config should be reserved
    to handle backwards compatibility (e.g., changed location of some configuration keys)

    Example configuration, showing both the single-string and language-specific string options:
        assembly line:
            interview list:
                title:
                    en: In progress forms
                    es: Formularios en progreso
                short title: My forms

    Args:
        config_key (str): The config key to look up. The config can be a single string or a dictionary with language keys.
        top_level_config_key (str, optional): Optional, alternative top-level config key to look up. Defaults to None.

    Returns:
        str: The value of the config key, or the alternative key, or None.
    """
    interview_list_config = get_config("assembly line", {}).get("interview list", {})
    if interview_list_config.get(config_key):
        if isinstance(interview_list_config.get(config_key), dict):
            if get_language() in interview_list_config.get(config_key):
                return interview_list_config.get(config_key)[get_language()]
            else:
                return next(iter(interview_list_config.get(config_key).values()), None)
        else:
            return interview_list_config.get(config_key)
    else:
        return get_config(top_level_config_key or config_key)

from collections.abc import Iterable
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from docassemble.base.util import (
    DAFile,
    DAFileCollection,
    DAFileList,
    get_session_variables,
    set_session_variables,
    set_variables,
    all_variables,
    user_info,
    variables_snapshot_connection,
    word,
    user_has_privilege,
    log,
    interview_url,
    action_button_html,
    url_action,
    url_ask,
    as_datetime,
    create_session,
    set_parts,
    user_logged_in,
)
from docassemble.webapp.users.models import UserModel
from docassemble.webapp.db_object import init_sqlalchemy
from sqlalchemy.sql import text
from docassemble.base.functions import server, safe_json
from .al_document import (
    ALDocument,
    ALDocumentBundle,
    ALStaticDocument,
    ALExhibit,
    ALExhibitList,
)

__all__ = [
    "is_file_like",
    "set_interview_metadata",
    "get_interview_metadata",
    "rename_interview_answers",
    "save_interview_answers",
    "get_filtered_session_variables",
    "load_interview_answers",
    "get_saved_interview_list",
    "interview_list_html",
]

db = init_sqlalchemy()

al_sessions_variables_to_remove = {
    # Internal fields
    "_internal",
    "nav",
    "url_args",
    "device_local",
    "allow_cron",
    "feedback_form",
    "github_repo_name",
    "github_user",
    "interview_short_title",
    "metadata_title",
    "multi_user",
    "session_local",
    "speak_text",
    "user_local",
    # Database-like fields we don't need to copy
    "all_courts",
    "macourts",
    "court_emails",
    # AssemblyLine form-specific fields
    "al_form_type",
    "al_version",
    "form_approved_for_email_filing",
    "interview_metadata",
    "package_name",
    "package_version_number",
    "user_has_saved_answers",
    # Variables that should be calculated fresh
    "signature_date",
    "al_court_bundle",
    "al_user_bundle",
    "case_name",
    "al_logo",
    "AL_ORGANIZATION_HOMEPAGE",
    "AL_DEFAULT_STATE",
    "AL_DEFAULT_COUNTRY",
    "AL_DEFAULT_LANGUAGE",
    "AL_DEFAULT_OVERFLOW_MESSAGE",
    "AL_ORGANIZATION_TITLE",
    "about_this_interview_version_info",
    # Variables from saving/loading state
    "al_formatted_sessions",
    "al_sessions_copy_success",
    "al_sessions_fast_forward_filtered_vars",
    "al_sessions_fast_forward_session",
    "al_sessions_filtered_vars",
    "al_sessions_launch_new_session",
    "al_sessions_list",
    "al_sessions_new_session_id",
    "al_sessions_preview_variables",
    "al_sessions_save_session_snapshot",
    "al_sessions_save_session_snapshot_success",
    "al_sessions_snapshot_label",
    "al_sessions_snapshot_results",
    "al_sessions_source_session",
    "al_sessions_variables_to_remove",
    "al_simple_filtered_vars",
    "filtered_vars_tmp",
    "simple_filtered_vars_tmp",
    "al_sessions_url_ask_snapshot",
    "al_sessions_url_ask_fast_forward",
    "al_sessions_variables_to_remove_from_new_interview",
    "is_file_like",
    # Some type annotations from Typing that seem plausible we'll use (not everything)
    "Any",
    "Callable",
    "Dict",
    "Generic",
    "Iterable",
    "List",
    "Optional",
    "Set",
    "Tuple",
    "TypeVar",
    "Union",
    "Concatenate",
    "TypeLiteral",
    "ClassVar",
    "Final",
    "Annotated",
    "TypeGuard",
    "ParamSpec",
    "AnyStr",
    "Protocol",
    "NamedTuple",
    "NewType",
    "TypedDict",
    "FrozenSet",
    "DefaultDict",
    "OrderedDict",
    "ChainMap",
    "Counter",
    "Deque",
    "IO",
    "TextIO",
    "BinaryIO",
    "Pattern",
    "Match",
    "Text",
    # Variables that should always be created by code, so safe to recalculate
    "user_started_case",
    "user_role",
    "menu_items",
    "al_menu_items",
}

al_sessions_variables_to_remove_from_new_interview = [
    "docket_number",
    "docket_numbers",
    "user_ask_role",
]

al_session_store_default_filename = f"{user_info().package}:al_saved_sessions_store.yml"


def is_file_like(obj):
    return isinstance(
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
        ),
    )


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
    """
    server.write_answer_json(
        session_id, filename, safe_json(data), tags=metadata_key_name, persistent=True
    )


def get_interview_metadata(
    filename: str, session_id: int, metadata_key_name: str = "metadata"
) -> Dict:
    """Retrieve the unencrypted metadata associated with an interview.
    We implement this with the docassemble jsonstorage table and a dedicated `tag` which defaults to `metadata`.
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
    filename: str = al_session_store_default_filename,
    user_id: Union[int, str] = None,
    metadata_key_name: str = "metadata",
) -> Tuple[Dict, int]:
    """Get a list of saved sessions for the specified filename. If the save_interview_answers function was used
    to add metadata, the result list will include columns containing the metadata.
    If the user is a developer or administrator, setting user_id = None will list all interviews on the server. Otherwise,
    the user is limited to their own sessions.
    """
    get_sessions_query = text(
        """
           SELECT  userdict.indexno
           ,userdict.filename as filename
           ,num_keys
           ,userdictkeys.user_id as user_id
           ,userdict.modtime as modtime
           ,userdict.key as key
           ,jsonstorage.data->'title' as title
           ,jsonstorage.data->'description' as description
           ,jsonstorage.data->'steps' as steps
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
    ORDER BY modtime desc 
    LIMIT 500;
    """
    )

    # TODO: decide if we need to handle paging

    if not filename:
        filename = None  # Explicitly treat empty string as equivalent to None
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
            metadata=metadata_key_name,
            user_id=user_id,
            filename=filename,
        )
    sessions = []
    for session in rs:
        sessions.append(session)

    return sessions


def interview_list_html(
    filename: str = al_session_store_default_filename,
    user_id: Union[int, str] = None,
    metadata_key_name: str = "metadata",
    # name_label: str = word("Title"),
    date_label: str = word("Date"),
    details_label: str = word("Details"),
    actions_label: str = word("Actions"),
    load_action: str = "al_sessions_fast_forward_session",
    delete_action: str = "al_sessions_delete_session",
) -> str:
    """Return a string containing an HTML-formatted table with the list of saved answers.
    Clicking the "load" icon
    """

    # TODO: think through how to translate this function. Templates probably work best but aren't
    # convenient to pass around
    answers = get_saved_interview_list(
        filename=filename, user_id=user_id, metadata_key_name=metadata_key_name
    )

    if not answers:
        return ""

    table = '<div class="table-responsive"><table class="table table-striped al-saved-answer-table">'
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
        table += f"""
        <td><a href="{ url_action(load_action, i=answer.get("filename"), session=answer.get("key")) }"><i class="fa fa-regular fa-folder-open" aria-hidden="true"></i>&nbsp;{answer.get("title") or answer.get("filename").replace(":", " ") or "Untitled interview" }</a></td>
        <td>{ as_datetime(answer.get("modtime")) }</td>
        <td>Page { answer.get("steps") or answer.get("num_keys") } <br/>
            {answer.get("original_interview_filename") or answer.get("filename") or "" }
        </td>
        <td>
          <a href="{ url_action(delete_action, filename=answer.get("filename"), session=answer.get("key")) }"><i class="far fa-trash-alt" title="Delete" aria-hidden="true"></i><span class="sr-only">Delete</span></a>
          <a target="_blank" href="{ interview_url(i=answer.get("filename"), session=answer.get("key")) }">
              <i class="far fa-eye" aria-hidden="true" title="View"></i>
              <span class="sr-only">View</span>
          </a>
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
    """Function that changes just the 'title' of an interview, as stored in the dedicated `metadata` column."""
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


def save_interview_answers(
    filename: str = al_session_store_default_filename,
    variables_to_filter: Iterable = None,
    metadata: Dict = None,
    metadata_key_name: str = "metadata",
) -> str:
    """Copy the answers from the running session into a new session with the given
    interview filename."""
    # Avoid using mutable default parameter
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove
    if not metadata:
        metadata = {}

    # Get variables from the current session
    all_vars = all_variables(simplify=False)

    all_vars = {
        item: all_vars[item]
        for item in all_vars
        if not item in variables_to_filter and not is_file_like(all_vars[item])
    }

    try:
        # Sometimes include_internal breaks things
        metadata["steps"] = (
            all_variables(include_internal=True).get("_internal").get("steps", -1)
        )
    except:
        metadata["steps"] = -1

    metadata["original_interview_filename"] = all_variables(special="metadata").get(
        "title", user_info().filename.replace(":", " ").replace(".", " ")
    )
    metadata["answer_count"] = len(all_vars)

    # Create a new session
    new_session_id = create_session(filename)

    # Copy in the variables from this session
    set_session_variables(filename, new_session_id, all_vars, overwrite=True)

    # Add the metadata
    set_interview_metadata(filename, new_session_id, metadata)
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
    filename: str, session_id: int, variables_to_filter: List[str] = None
) -> Dict[str, Any]:
    """
    Get a filtered subset of the variables from the specified interview filename and session.
    """
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove

    all_vars = get_session_variables(filename, session_id, simplify=False)

    # Remove items that we were explicitly told to remove
    # Delete all files and ALDocuments
    return {
        item: all_vars[item]
        for item in all_vars
        if not item in variables_to_filter and not is_file_like(all_vars[item])
    }


def load_interview_answers(
    old_interview_filename: str,
    old_session_id: str,
    new_session: bool = False,
    new_interview_filename: str = None,
    variables_to_filter: List[str] = None,
) -> Optional[int]:
    """
    Load answers from the specified session. If the parameter new_session = True, create a new session of
    the specified or current interview filename. Otherwise, load the answers into the active session.
    Returns the ID of the newly created session
    Create a new session with the variables from the specified session ID. Returns the ID of the newly
    created and "filled" session.
    """
    old_variables = get_filtered_session_variables(
        old_interview_filename, old_session_id, variables_to_filter
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

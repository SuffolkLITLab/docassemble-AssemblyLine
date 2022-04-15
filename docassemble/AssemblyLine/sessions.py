from typing import List, Dict, Any
from docassemble.base.util import (
    DAFile, 
    DAFileCollection, 
    DAFileList, 
    get_session_variables, 
    set_session_variables,
    all_variables,
    user_info,
    variables_snapshot_connection,  
)

from docassemble.base.functions import server, safe_json

from .al_document import ALDocument, ALDocumentBundle

__all__ = [
    "file_like",
    "add_interview_metadata",
    "get_interview_metadata",
    "rename_interview_answers",
    "save_interview_answers",
    "get_filtered_session_variables",
    "load_interview_answers",
]

al_sessions_variables_to_remove = [
    # Internal fields
    '_internal',
    'nav',
    'url_args',
    'device_local',
    'allow_cron',
    'feedback_form',
    'github_repo_name',
    'github_user',
    'interview_short_title',
    'metadata_title',
    'multi_user',
    'session_local',
    'speak_text',
    'user_local',
    # Database-like fields we don't need to copy
    'all_courts',
    'macourts',
    'court_emails',    
    # AssemblyLine form-specific fields     
    'al_form_type',
    'al_version',    
    'form_approved_for_email_filing',    
    'interview_metadata',    
    'package_name',
    'package_version_number',
    'user_has_saved_answers',        
    # Variables that should be calculated fresh
    'signature_date',
    'al_court_bundle',
    'al_user_bundle',
    'case_name',
    'al_logo',    
    'AL_ORGANIZATION_HOMEPAGE',
    'AL_DEFAULT_STATE',
    'AL_DEFAULT_COUNTRY',
    'AL_DEFAULT_LANGUAGE',
    'AL_DEFAULT_OVERFLOW_MESSAGE',
    'AL_ORGANIZATION_TITLE',
    'about_this_interview_version_info',    
    # Variables from saving/loading state
    'al_formatted_sessions',
    'al_sessions_copy_success',
    'al_sessions_fast_forward_filtered_vars',
    'al_sessions_fast_forward_session',
    'al_sessions_filtered_vars',
    'al_sessions_launch_new_session',
    'al_sessions_list',
    'al_sessions_new_session_id',
    'al_sessions_preview_variables',
    'al_sessions_save_session_snapshot',
    'al_sessions_save_session_snapshot_success',
    'al_sessions_snapshot_label',
    'al_sessions_snapshot_results',
    'al_sessions_source_session',
    'al_sessions_variables_to_remove',
    'al_simple_filtered_vars',
    'filtered_vars_tmp',
    'simple_filtered_vars_tmp',
    'al_sessions_url_ask_snapshot',
    'al_sessions_url_ask_fast_forward',
    'al_sessions_variables_to_remove_from_new_interview',
    'file_like',
    # Some type annotations from Typing that seem plausible we'll use (not everything)
    'Any',
    'Callable',
    'Dict',
    'Generic',
    'Iterable',    
    'List',
    'Optional',
    'Set',
    'Tuple',
    'TypeVar',
    'Union',
    'Concatenate',
    'TypeLiteral',
    'ClassVar',
    'Final',
    'Annotated',
    'TypeGuard',
    'ParamSpec',
    'AnyStr',
    'Protocol',
    'NamedTuple',
    'NewType',
    'TypedDict',
    'FrozenSet',
    'DefaultDict',
    'OrderedDict',
    'ChainMap',
    'Counter',
    'Deque',
    'IO',
    'TextIO',
    'BinaryIO',
    'Pattern',
    'Match',
    'Text',
    # Variables that should always be created by code, so safe to recalculate
    'user_started_case',    
    'user_role',
]

al_sessions_variables_to_remove_from_new_interview = [
    'docket_number',
    'docket_numbers',
    'user_ask_role',
]

def file_like(obj):
    return isinstance(obj, DAFile) or isinstance(obj, DAFileCollection) or isinstance(obj, DAFileList) or isinstance(obj, ALDocument) or isinstance(obj, ALDocumentBundle)

  
def add_interview_metadata(filename:str, session_id:int, data:Dict, metadata_key_name="metadata") -> None:
    """Add searchable interview metadata for the specified filename and session ID.
       Intended to be used to add an interview title, etc.
       Standardized metadata dictionary:
       - title
       - subtitle
       - original_interview_filename
       - variable_count
    """      
    server.write_answer_json(session_id, filename, safe_json(data), tags=metadata_key_name, persistent=True)

def get_interview_metadata(filename:str, session_id:int, metadata_key_name:str = "metadata") -> Dict:
    """Retrieve the unencrypted metadata associated with an interview. 
    We implement this with the docassemble jsonstorage table and a dedicated `tag` which defaults to `metadata`.
    """
    conn = variables_snapshot_connection()
    with conn.cursor() as cur:
        query = "select data from jsonstorage where filename=%(filename)s and tags=%(tags)s"
        cur.execute(query, {"filename": filename, "tags": metadata_key_name})
        val = cur.fetchone()
    conn.close()
    return val # is this a string or a dictionary?
  
def rename_interview_answers(filename:str, session_id:int, new_name:str, metadata_key_name:str = "metadata") -> None:
    """Function that changes just the 'title' of an interview, as stored in the dedicated `metadata` column."""
    existing_metadata = get_interview_metadata(filename, session_id, metadata_key_name=metadata_key_name)
    existing_metadata["title"] = new_name
    add_interview_metadata(filename, session_id, existing_metadata, metadata_key_name=metadata_key_name)

def save_interview_answers(filename:str, variables_to_filter:List[str] = None, metadata:Dict = None, metadata_key_name:str = "metadata") -> str:
    """Copy the answers from the running session into a new session with the given
    interview filename."""
    # Avoid using mutable default parameter
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove
    if not metadata:
        metadata = {}    
    
    # Get variables from the current session
    all_vars = all_variables()
    for var in variables_to_filter:
        all_vars.pop(var, None)    
    
    all_vars = {
            item:all_vars[item] 
            for item in all_vars 
            if not file_like(all_vars[item])
        }
    
    try:
        # Sometimes include_internal breaks things
        metadata["steps"] = all_variables(include_internal=True).get("_internal").get("steps", -1)
    except:
        metadata["steps"] = -1
    
    metadata["original_interview_filename"] = user_info().filename
    metadata["question_id"] = user_info().question_id
    metadata["answer_count"] = len(all_vars)
    
    # Create a new session
    new_session_id = create_session(filename)
    
    # Copy in the variables from this session
    set_session_variables(filename, new_session_id, all_vars)
    
    # Add the metadata
    add_interview_metadata(filename, new_session_id, metadata)
    
    return new_session_id
    
def get_filtered_session_variables(
        filename:str, 
        session_id:int, 
        variables_to_filter:List[str] = None
    ) -> Dict[str, Any]:
    """
    Get a filtered subset of the variables from the specified interview filename and session.
    """
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove
        
    all_vars = get_session_variables(
        filename,
        session_id,
        simplify=False
    )
    
    # Remove items that we were explicitly told to remove
    for var in variables_to_filter:
        all_vars.pop(var, None)

    # Delete all files and ALDocuments
    return {
            item:all_vars[item] 
            for item in all_vars 
            if not file_like(all_vars[item])
        }
    
  
def load_interview_answers(
        new_interview_filename:str, 
        old_interview_filename:str,
        old_session_id:str, 
        variables_to_filter:List[str] = None
    )->str:
    """Create a new session with the variables from the specified session ID. Returns the ID of the newly
    created and "filled" session.
    """
    new_session_id = create_session(new_interview_filename)
    old_variables = get_filtered_session_variables(old_interview_filename, old_session_id, variables_to_filter)
    
    set_session_variables(new_interview_filename, new_session_id, old_variables)
    
    return new_session_id
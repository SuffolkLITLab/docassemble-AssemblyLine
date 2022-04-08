from typing import List, Dict, Any
from docassemble.base.util import DAFile, DAFileCollection, DAFileList, get_session_variables, set_session_variables
from .al_document import ALDocument, ALDocumentBundle

__all__ = ["file_like", "fast_forward_session"]

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

  
def store_variables_snapshot(filename:str, session_id:int, data=None, key=None, persistent=True):
    """Stores a snapshot of the interview answers in non-encrypted JSON format."""
    session = get_uid()
    
    filename = this_thread.current_info.get('yaml_filename', None)
    if session is None or filename is None:
        raise DAError("store_variables_snapshot: could not identify the session")
    if key is not None and not isinstance(key, str):
        raise DAError("store_variables_snapshot: key must be a string")
    if data is None:
        the_data = serializable_dict(get_user_dict(), include_internal=include_internal)
    else:
        the_data = safe_json(data)
    server.write_answer_json(session, filename, the_data, tags=key, persistent=True if persistent else False)
  

def save_interview_answers(filename:str, variables_to_filter:List[str] = [], metadata:Dict = None) -> str:
    """Copy the answers from the running session into a new session with the given
    interview filename."""
    # Avoid using mutable default parameter
    if not variables_to_filter:
        variables_to_filter = []
    if not metadata:
        metadata = {}
    
    
def get_filtered_session_variables(
        filename:str, 
        session_id:int, 
        variables_to_filter:List[str] = None
    ) -> Dict[str, Any]:
    """Get a filtered subset of the variables from the specified interview filename and session."""
    if not variables_to_filter:
        variables_to_filter = []
    all_vars = get_session_variables(
      filename,
      session_id,
      simplify=False)
    
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
        variables_to_filter:List[str] = al_sessions_variables_to_remove
    )->str:
    """Create a new session with the variables from the specified session ID. Returns the ID of the newly
    created and "filled" session.
    """
    new_session_id = create_session(interview_file_name)
    
    set_session_variables(al_sessions_destination_session, al_sessions_new_session_id, al_sessions_fast_forward_filtered_vars)
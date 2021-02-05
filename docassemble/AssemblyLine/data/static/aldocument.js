function aldocument_send_action(event_name, wants_editable, email) {
  da_action_perform(event_name, {wants_editable, email})
  // var wants_edit = $("#al_wants_editable_'''+name+'''")[0].checked;
  // var email = $("#al_doc_email_'''+name+'''")[0].value;
  // action_perform("'''+event_name+'''", {wants_edit, email});
};
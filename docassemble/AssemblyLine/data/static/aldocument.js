/*
 * given a docassemble event name, and text ID containing email address and whether
 * or not user wants to send editable files, trigger docassemble event to
 * email an ALDocumentBundle
 */
function aldocument_send_action(event_name, wants_editable_id, email_id) {
  var editable = false;
  
  console.log( email_id );
  var editable_choice_node = $('#' + wants_editable_id);
  if ( editable_choice_node && editable_choice_node[0] ) {
    editable = $('#' + wants_editable_id)[0].checked;
  }
  
  var email = $('#' + email_id)[0].value;
  da_action_perform(event_name, {editable: editable, email: email});
};
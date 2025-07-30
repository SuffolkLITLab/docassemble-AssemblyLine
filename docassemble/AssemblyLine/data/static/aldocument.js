/*
 * given a docassemble event name, and text ID containing email address and whether
 * or not user wants to send editable files, trigger docassemble event to
 * email an ALDocumentBundle
 */
function aldocument_send_action(event_name, wants_editable_id, email_id, template_name="", key="final", preferred_formats=null) {
  var editable = null;
  var final_formats = preferred_formats;
  
  console.log( email_id );
  var editable_choice_node = $('#' + wants_editable_id);
  if ( editable_choice_node && editable_choice_node[0] ) {
    editable = $('#' + wants_editable_id)[0].checked;
    if (editable) {
      final_formats = ["pdf", "docx"];
    } else {
      final_formats = ["pdf"];
    }
  }
  
  var email = $('#' + email_id)[0].value;
  da_action_perform(event_name, {editable: editable, email: email, key:key, template_name: template_name, preferred_formats: final_formats});
};

/*
 * given a docassemble event name, and text ID containing email address and whether
 * or not user wants to send editable files, trigger docassemble event to
 * email an ALDocumentBundle
 */
function aldocument_send_to_action(event_name, editable, email, button_id, template_name="", key="final", preferred_formats="pdf") {
  var button = $('#' + button_id);
  button.html('Sending...');
  button.addClass('disabled');    // to visually disable button
  da_action_call(event_name, {editable: editable, email: email, template_name: template_name, key:key, preferred_formats: preferred_formats}, function (results) {
    if (results.success) {
      console.log("Email sent")
      button.prop('disabled', true);
      button.html('Sent');
    } else {
      console.log("Email failed")
      button.prop('disabled', false);
      button.html('Send');
      button.removeClass('disabled'); // to visually enable
    }
  });
};
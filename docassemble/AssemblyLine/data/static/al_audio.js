$(document).on('daPageLoad', function() {
  var $audio_nodes = $('.daaudio-control');
  var id_count = 1;
  for ( var audio_node of $audio_nodes ) {
    al_js.replace_with_audio_minimal_controls( audio_node, 'page_reader_substitute_' + id_count );
    id_count++;
  }
});

var al_js = {};

// We are not providing a way to rewind or scan through the audio.
// TODO: Show user the audio still needs to load:
// - https://stackoverflow.com/questions/9337300/html5-audio-load-event,
// - https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play
al_js.replace_with_audio_minimal_controls = function( audio_node, id ) {
  /* Create the custom controls for this specific audio element
  * and give the new controls container the requested `id` tag. */
  if (!audio_node) {
    // Some screens, like the signature screen, don't have screen readers.
    return;
  }
  
  // Hide the normal controls and show the new controls
  audio_node.removeAttribute('controls');
  audio_node.style.display = 'none';
  var $audio_container = $($(audio_node).closest('.daaudiovideo-control'));
  $audio_container.addClass( 'al_custom_media_controls' );
  $('<div id="' + id + '" class="btn-group">' +
        audio_contents_html +
  '</div>').appendTo( $audio_container );
  
  // Start of all the right selectors
  var id_s = '#' + id + ' ';
  // 'play' position should be play OR pause OR restart
  $(id_s + '.restart').first().attr('aria-hidden', 'true').hide();
  $(id_s + '.pause').first().attr('aria-hidden', 'true').hide();
  
  var is_loading = true
  $(id_s + '.play').first().on( 'click', function() {  // pause & stop
    audio_node.play().then(function(){ is_loading = false });
    $(id_s + '.pause').first().attr('aria-hidden', 'false').show();
    $(id_s + '.play').first().attr('aria-hidden', 'true').hide();
    $(id_s + '.restart').first().attr('aria-hidden', 'true').hide();
  });
  
  $(id_s + '.restart').first().on( 'click', function() {  // pause & stop
    audio_node.play();
    $(id_s + '.pause').first().attr('aria-hidden', 'false').show();
    $(id_s + '.play').first().attr('aria-hidden', 'true').hide();
    $(id_s + '.restart').first().attr('aria-hidden', 'true').hide();
  });
  
  $(id_s + '.pause').first().on( 'click', function() {  // play & stop
    audio_node.pause()
    $(id_s + '.play').first().attr('aria-hidden', 'false').show();
    $(id_s + '.restart').first().attr('aria-hidden', 'true').hide();
    $(id_s + '.pause').first().attr('aria-hidden', 'true').hide();
  });
  
  var stop_and_reset = function () {
    audio_node.pause();
    audio_node.currentTime = 0;
    $(id_s + '.restart').first().attr('aria-hidden', 'false').show();
    $(id_s + '.play').first().attr('aria-hidden', 'true').hide();
    $(id_s + '.pause').first().attr('aria-hidden', 'true').hide();
  }
  
  $(id_s + '.stop').first().on( 'click', stop_and_reset );
  $(audio_node).on( 'ended', stop_and_reset );
  
};  // Ends al_js.audio_minimal_controls()

// The DOM structure for every AL audio element with custom controls
var audio_contents_html = '\
  <button class="media-action play btn btn-sm btn-outline-secondary">\
    <i class="fas fa-volume-up"></i><span>&nbsp;Listen&nbsp;</span>\
    <i class="fas fa-play"></i>\
  </button>\
  <button class="media-action restart btn btn-sm btn-outline-secondary">\
    <i class="fas fa-volume-up"></i><span>&nbsp;Listen&nbsp;</span>\
    <i class="fas fa-undo"></i>\
  </button>\
  <button class="media-action pause btn btn-sm btn-outline-secondary">\
    <i class="fas fa-volume-up"></i><span>&nbsp;Listen&nbsp;</span>\
    <i class="fas fa-pause"></i>\
  </button>\
  <button class="media-action stop btn btn-sm btn-outline-secondary">\
    <i class="fas fa-stop"></i>\
  </button>\
';

/* A start on volume functionality:
  <button class="media-action volume-down btn btn-sm btn-outline-secondary">\
    <i class="fas fa-volume-down"></i>\
  </button>\
  <button class="media-action volume-up btn btn-sm btn-outline-secondary">\
    <i class="fas fa-volume-up"></i>\
  </button>\
  
  // Seems to bottom out at 0 as far as user interaction is concerned
  $(id_s +'.volume-down').first().on('click', function(){ audio_node.volume -= 0.1 });
  $(id_s + '.volume-up').first().on('click', function(){ audio_node.volume += 0.1 });
*/

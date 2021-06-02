// Do not overwrite already created al_js object. This may be relevant as our js gets built out.
if ( !al_js ) { var al_js = {}; }

$(document).on('daPageLoad', function() {
  try {
    var $audio_nodes = $('.daaudio-control');
    var id_count = 1;
    for ( var audio_node of $audio_nodes ) {
      // We are not using the returned value right now
      al_js.replace_with_audio_minimal_controls( audio_node, 'page_reader_substitute_' + id_count );
      id_count++;
    }
  } catch ( error ) { console.log( 'AL audio intantiation error:', error ) }
});

// We are not providing a way to rewind or scan through the audio.
// TODO: Show user the audio still needs to load:
// - https://stackoverflow.com/questions/9337300/html5-audio-load-event,
// - https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play
al_js.replace_with_audio_minimal_controls = function( audio_node, id ) {
  /* Create the custom controls for this specific audio element
  * and give the new controls container the requested `id` tag.
  * Return functions to control audio playback for this node. */
  var controls = {
    play: function () {}, pause: function () {},
    restart: function () {}, stop_and_reset: function () {},
  };
  
  if (!audio_node) {
    // Some screens, like the signature screen, don't have screen readers.
    return controls;
  }
  
  // Hide the normal controls and show the new controls
  audio_node.removeAttribute('controls');
  audio_node.style.display = 'none';
  var $audio_container = $($(audio_node).closest('.daaudiovideo-control'));
  $audio_container.addClass( 'al_custom_media_controls al_audio_controls' );
  $('<div id="' + id + '" class="btn-group">' +
        audio_contents_html +
  '</div>').appendTo( $audio_container );
  
  // Start of all the right selectors
  var id_s = '#' + id + ' ';
  // There are currently two icons displaying at the same time.
  // The first is one of play OR pause OR restart. The last is always the stop icon.
  $(id_s + '.restart').first().attr('aria-hidden', 'true').hide();
  $(id_s + '.pause').first().attr('aria-hidden', 'true').hide();
  
  var is_loading = true;  // TODO: Add indication that audio is loading and remove var
  controls.play = function () {
    try {
      audio_node.play().then(function(){ is_loading = false; });
      // pause & stop buttons should be visible
      $(id_s + '.pause').first().attr('aria-hidden', 'false').show();
      $(id_s + '.play').first().attr('aria-hidden', 'true').hide();
      $(id_s + '.restart').first().attr('aria-hidden', 'true').hide();
    } catch ( error ) { console.log( 'AL audio play error:', error ) }
  }
  controls.restart = controls.play;
  controls.pause = function() {
    try {
      audio_node.pause()
      // play & stop buttons should be visible
      $(id_s + '.play').first().attr('aria-hidden', 'false').show();
      $(id_s + '.restart').first().attr('aria-hidden', 'true').hide();
      $(id_s + '.pause').first().attr('aria-hidden', 'true').hide();
    } catch ( error ) { console.log( 'AL audio pause error:', error ) }
  }
  controls.stop_and_reset = function () {
    try {
      audio_node.pause();
      audio_node.currentTime = 0;
      $(id_s + '.restart').first().attr('aria-hidden', 'false').show();
      $(id_s + '.play').first().attr('aria-hidden', 'true').hide();
      $(id_s + '.pause').first().attr('aria-hidden', 'true').hide();
    } catch ( error ) { console.log( 'AL audio stop error:', error ) }
  }
  
  $(id_s + '.play').first().on( 'click tap', controls.play );
  $(id_s + '.restart').first().on( 'click tap', controls.restart );
  $(id_s + '.pause').first().on( 'click tap', controls.pause );
  $(id_s + '.stop').first().on( 'click tap', controls.stop_and_reset );
  $(audio_node).on( 'ended', controls.stop_and_reset );
  
  // When any button or link is pressed
  $('button, a').on( 'click tap', function ( event ) {
    try {
      // If the button or link is not in an audio control itself, pause the playback
      var audio_parent = $(event.target).closest( '.al_audio_controls' );
      if ( audio_parent.length === 0 ) { controls.pause(); }
    } catch ( error ) { console.log( 'AL audio button pause error:', error ) }
  });
  
  // Returns ability to control the playback of these nodes externally
  return controls;
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

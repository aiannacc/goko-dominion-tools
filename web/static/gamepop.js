/*
 * Basic appearance of the Annouce Game popup dialog
 */

// Override Goko's "hide select" elements by default" nonsense
$('#gamepop .wtfgoko').css('visibility', 'inherit');
$('#gamepop .wtfgoko').css('top', 'auto');
  
// Make this into a lightbox-style dialog
$('#gamepop').css("position", "absolute");
$('#gamepop').css("top", "50%");
$('#gamepop').css("left", "50%");
$('#gamepop').css("height", "300px");
$('#gamepop').css("margin-top", "-150px");
$('#gamepop').css("width", "40%");
$('#gamepop').css("margin-left", "-20%");
$('#gamepop').css("background", "white");


/*
 * Helper functions
 */

// Update and show/hide the dialog
AM.show_gamepop = function(visible) {
    AM._update_gamepop();
    $('#gamepop').css('visibility', visible ? 'visible' : 'hidden');
}

// Change status and enable/disable elements based on whether we have an
// outstanding game request.
AM._update_gamepop = function() {

    $('#gamehost').html();
    $('#gameguests').empty();

    if (AM.state.game !== null) {
        // Name host
        $('#gamehost').html(AM.state.game.hostname);

        // List guests
        AM.get_oppnames(AM.state.game, AM.state.game.hostname).map(function(p) {
            $('#gameguests').append('<li>' + p + '</li>');
        });
    };
}

$('#abortgame').click(function (evt) {
    AM.send_message('cancel_game', {matchid: AM.state.game.matchid});
    $('#announcepop').hide();
});

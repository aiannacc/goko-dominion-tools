/*
 * Basic appearance of the Offer Match popup dialog
 */

// Override Goko's "hide select" elements by default" nonsense
$('#offerpop .wtfgoko').css('visibility', 'inherit');
$('#offerpop .wtfgoko').css('top', 'auto');
  
// Make this into a lightbox-style dialog
$('#offerpop').css("position", "absolute");
$('#offerpop').css("top", "50%");
$('#offerpop').css("left", "50%");
$('#offerpop').css("height", "300px");
$('#offerpop').css("margin-top", "-150px");
$('#offerpop').css("width", "40%");
$('#offerpop').css("margin-left", "-20%");
$('#offerpop').css("background", "white");


/*
 * Helper functions
 */

// Update and show/hide the dialog
AM.showOfferpop = function(visible) {

    if (AM.state.offer !== null) {

        // List players
        $('#plist').empty();
        AM.state.offer.seeks.map(function(s) {
            var p = s.player.pname + ' [' + s.player.rating.goko_pro_rating + ']'
            $('#plist').append('<li>' + p + '</li>');
            // TODO: use casual rating if it's a casual game
        });

        // List or count card sets
        var sets = AM.getHost(AM.state.offer).setsOwned;
        switch(sets.length) {
            case 15:
                $('#offersets').html('All Cards');
                break;
            case 1:
                $('#offersets').html('Base Only');
                break;
            case 2: case 3: case 4: case 5:
                $('#offersets').html(sets.join(', '));
                break;
            default:
                $('#offersets').html(sets.length + ' sets');
        }

        $('#offerrating').html(AM.state.offer.rating_system);

        $('#offerhost').html(AM.state.offer.hostname);
        $('#offerroom').html(AM.state.offer.roomname);
        $('#offerwaitinfo').html('');
        $('#offeracc').prop('disabled', false);
        $('#offerrej').prop('disabled', false);
    }
    
    $('#offerpop').css('visibility', visible ? 'visible' : 'hidden');
}

$('#offeracc').click(function (evt) {
    AM.state.offer.accepted = true;

    // Disable UI while waiting for server response.
    $('#offeracc').prop('disabled', true);
    $('#offerrej').prop('disabled', true);
    $('#offerwaitinfo').html('Accepted offer. Waiting for server to confirm.');

    // Notify server
    AM.sendMessage('ACCEPT_OFFER', {matchid: AM.state.offer.matchid}, function() {
        $('#offerwaitinfo').html('Accepted offer. Waiting for opponents(s) to accept.');
        $('#offeracc').prop('disabled', true);
        $('#offerrej').prop('disabled', false);
    });
});

$('#offerdec').click(function (evt) {
    AM.showOfferpop(false);

    if (AM.state.offer.accepted !== null && AM.state.offer.accepted) {
        AM.sendMessage('UNACCEPT_OFFER', {matchid: AM.state.offer.matchid}, function() {
            AM.state.offer = null;
        });
    } else {
        AM.sendMessage('DECLINE_OFFER', {matchid: AM.state.offer.matchid}, function() {
            AM.state.offer = null;
        });
    }
});

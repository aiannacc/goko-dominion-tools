/*
 * Basic appearance of the Seek Request popup dialog
 */

// Override Goko's "hide select" elements by default" nonsense
$('#seekpop .wtfgoko').css('visibility', 'inherit');
$('#seekpop .wtfgoko').css('top', 'auto');
  
// Make this into a lightbox-style dialog
$('#seekpop').css("position", "absolute");
$('#seekpop').css("top", "50%");
$('#seekpop').css("left", "50%");
$('#seekpop').css("height", "250px");
$('#seekpop').css("margin-top", "-125px");
$('#seekpop').css("width", "40%");
$('#seekpop').css("margin-left", "-20%");
$('#seekpop').css("background", "white");


/*
 * Helper functions
 */

// Update and show/hide the dialog
AM.showSeekpop = function(visible) {
    AM.updateSeekpop();
    $('#seekpop').css('visibility', visible ? 'visible' : 'hidden');
}

// Change status and enable/disable elements based on whether we have an
// outstanding seek request.
AM.updateSeekpop = function() {
    var seeking = (AM.state.seek !== null);
    var canceling = seeking
        && (typeof AM.state.seek.canceling !== 'undefined')
        && AM.state.seek !== null
        && AM.state.seek; // TODO: surely there is a better way...

    $('#seekpop select').prop('disabled', seeking || canceling); 
    $('#seekpop input').prop('disabled', seeking || canceling);
    $('#seekreq').prop('disabled', seeking || canceling);
    $('#seekcan').prop('disabled', canceling);
    $('#seekhide').prop('disabled', false);
    $('#seekstatus').html(seeking ? 'Looking for a match...' : '');
}


/*
 * Buttons
 */

// Submit request    
$('#seekreq').click(function() {
    console.log('requested seek');

    var np = {class: 'NumPlayers', props: {}};
    np.props.min_players = parseInt($('#minPlayers').val());
    np.props.max_players = parseInt($('#maxPlayers').val());

    var ns = {class: 'NumSets', props: {}};
    ns.props.min_sets = parseInt($('#minSets').val());
    ns.props.max_sets = parseInt($('#maxSets').val());

    var rr = {class: 'RelativeRating', props: {}};
    rr.props.pts_lower = parseInt($('#rdiff').val());
    rr.props.pts_higher = parseInt($('#rdiff').val());
    rr.props.rating_system = $('#ratingSystem').val();

    var rs = {class: 'RatingSystem', props: {}};
    rs.props.rating_system = $('#ratingSystem').val();

    // Send seek request
    AM.state.seek = {player: AM.player,
                     requirements: [np, ns, rr, rs]};
    AM.sendMessage('SUBMIT_SEEK', {seek: AM.state.seek});

    // Hide the dialog
    AM.showSeekpop(false);
});

// Cancel outstanding request, if any, and close dialog
$('#seekcan').click(function() {
    if (AM.state.seek !== null) {
        AM.state.seek.canceled = true;
        AM.sendMessage('CANCEL_SEEK',
            {seekid: AM.state.seek.seekid},
            function() { AM.state.seek = null; });
    }
    AM.showSeekpop(false);
});

$('#seekhide').click(function() {
    AM.showSeekpop(false);
});


/*
 * Input validation
 */

$('#minPlayers').change(function() {
    if (parseInt($('#minPlayers').val()) > parseInt($('#maxPlayers').val())) {
        $('#maxPlayers').val($('#minPlayers').val());
    }
});

$('#maxPlayers').change(function() {
    if (parseInt($('#maxPlayers').val()) < parseInt($('#minPlayers').val())) {
        $('#minPlayers').val($('#maxPlayers').val());
    }
});

$('#minSets').change(function() {
    if (parseInt($('#minSets').val()) > parseInt($('#maxSets').val())) {
        $('#maxSets').val($('#minSets').val());
    }
});

$('#maxSets').change(function() {
    if (parseInt($('#maxSets').val()) < parseInt($('#minSets').val())) {
        $('#minSets').val($('#maxSets').val());
    }
});

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
$('#seekpop').css("height", "300px");
$('#seekpop').css("margin-top", "-150px");
$('#seekpop').css("width", "40%");
$('#seekpop').css("margin-left", "-20%");
$('#seekpop').css("background", "white");


/*
 * Helper functions
 */

// Update and show/hide the dialog
AM.show_seekpop = function(visible) {
    AM._update_seekpop();
    $('#seekpop').css('visibility', visible ? 'visible' : 'hidden');
}

// Change status and enable/disable elements based on whether we have an
// outstanding seek request.
AM._update_seekpop = function() {
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
    np.props.min_players = parseInt($('#min_players').val());
    np.props.max_players = parseInt($('#max_players').val());

    var ns = {class: 'NumSets', props: {}};
    ns.props.min_sets = parseInt($('#min_sets').val());
    ns.props.max_sets = parseInt($('#max_sets').val());

    var rr = {class: 'RelativeRating', props: {}};
    rr.props.pts_lower = parseInt($('#rdiff').val());
    rr.props.pts_higher = parseInt($('#rdiff').val());
    rr.props.rating_system = $('#rating_system').val();

    var rs = {class: 'RatingSystem', props: {}};
    rs.props.rating_system = $('#rating_system').val();

    // Send seek request
    AM.state.seek = {player: AM.player,
                     requirements: [np, ns, rr, rs]};
    AM.send_message('submit_seek', {seek: AM.state.seek});

    // Hide the dialog
    AM.show_seekpop(false);
});

// Cancel outstanding request, if any, and close dialog
$('#seekcan').click(function() {
    if (AM.state.seek !== null) {
        AM.state.seek.canceled = true;
        AM.send_message('cancel_seek',
            {seekid: AM.state.seek.seekid},
            function() { AM.state.seek = null; });
    }
    AM.show_seekpop(false);
});

$('#seekhide').click(function() {
    AM.show_seekpop(false);
});


/*
 * Input validation
 */

$('#min_players').change(function() {
    if (parseInt($('#min_players').val()) > parseInt($('#max_players').val())) {
        $('#max_players').val($('#min_players').val());
    }
});

$('#max_players').change(function() {
    if (parseInt($('#max_players').val()) < parseInt($('#min_players').val())) {
        $('#min_players').val($('#max_players').val());
    }
});

$('#min_sets').change(function() {
    if (parseInt($('#min_sets').val()) > parseInt($('#max_sets').val())) {
        $('#max_sets').val($('#min_sets').val());
    }
});

$('#max_sets').change(function() {
    if (parseInt($('#max_sets').val()) < parseInt($('#min_sets').val())) {
        $('#min_sets').val($('#max_sets').val());
    }
});

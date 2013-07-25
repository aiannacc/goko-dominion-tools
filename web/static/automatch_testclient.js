/////////////////////////////////////////////////
// Browser automatch test client
//
// This is a blocking implementation of the abstract automatch test client
// defined in automatch_client.js, so we load that first.
//
$(document).ready(function() {
  jQuery.getScript('automatch_client.js', function() {
    console.log('Loaded automatch_client.js'); 
    load_automatch_testclient();
    $("#pname").val(Math.random().toString(36).substring(7));
    $("#pro_rating").val(Math.floor(3000+3000*Math.random()));
    $("#casual_rating").val(Math.floor(3000+3000*Math.random()));
    AM.update_ui();
  });
});

// After sending any message, the UI disables itself and waits for the server
// response. There is therefore no danger of getting out of sync with the
// server, but timeouts and lost messages need to be handled sensibly.
//
// Pings server every 10 seconds, times out if no server response is received
// for 10 seconds after sending a blocking message.
// 
var load_automatch_testclient = function() {
  console.log('Loading automatch_testclient.js');

  AM.on_timeout = function() {
    AM.state.info = 'Lost contact with server.';
    AM.update_ui();
    AM.disable_ui();
  }

  AM.handle_message = function(msgtype, message) {
    console.log(AM.player.pname + " received message (" + msgtype + ")");
    console.log(message);

    // Invoke the named function
    AM[msgtype](message);  

    AM.last_message = Date.now();
    AM.update_ui();
  }

  AM.confirm_receipt = function() { }

  AM.confirm_seek = function(msg) {
    AM.state.clear();
    AM.state.seek = msg.seek;
    AM.state.info = 'Server received seek #' + AM.state.seek.seekid;
  }

  AM.offer_match = function(msg) {
    AM.state.clear();
    AM.state.offer = msg.offer;
    AM.state.info = 'Server offered match: ' + AM.match_vs(AM.state.offer);
  }

  AM.confirm_offer_accept = function(msg) {
    AM.state.clear();
    AM.state.offer = msg.offer;
    AM.state.info = 'Server received match accept.';
  }

  AM.rescind_offer = function(msg) {
    AM.state.clear();
    AM.state.info = 'Server rescinded match offer.\nReason: ' + msg.reason;
  }

  AM.announce_game = function(msg) {
    AM.state.clear();
    AM.state.game = msg.game; 
    var game_str = AM.match_vs(AM.state.game) + '\n';
    game_str += '- Host: ' + AM.state.game.hostname + '\n';
    game_str += '- RoomID: ' + AM.state.game.roomid + '\n';
    AM.state.info = 'Server announced game: ' + game_str;
  }

  AM.unannounce_game = function(msg) {
    AM.state.clear();
    AM.state.info = 'Server unannounced game.\nReason: ' + msg.reason;
  }

  AM.disable_ui = function() {
    $("input").attr('disabled', true);
    $("#disconn").attr('disabled', false);
  }

  AM.update_ui = function() {
    AM.ui_blocked = false;
    var s = AM.state;

    $("#connect").attr('disabled', AM.ws);
    $("#ping").attr('disabled', !AM.ws);
    $("#pname").attr('disabled', AM.ws);
    $("#pro_rating").attr('disabled', AM.ws);
    $("#casual_rating").attr('disabled', AM.ws);

    $("#min_players").attr('disabled',
        s.game || s.offer || s.seek || !AM.ws);
    $("#max_players").attr('disabled',
        s.game || s.offer || s.seek || !AM.ws);
    $("#rdiff").attr('disabled',
        s.game || s.offer || s.seek || !AM.ws);
    $("#submit_seek").attr('disabled',
        s.game || s.offer || s.seek || !AM.ws);
    $("#cancel_seek").attr('disabled',
        s.game || s.offer || !s.seek || (s.seek && !s.seek.seekid));

    $('#accept_offer').attr('disabled', s.game || !s.offer || 
        (s.offer && s.accepted_offer));
    $('#decline_offer').attr('disabled', s.game || !s.offer ||
        (s.offer && s.accepted_offer));
    $('#unaccept_offer').attr('disabled', s.game || !s.offer || 
        (s.offer && !s.accepted_offer));

    $('#game_started').attr('disabled', !s.game);
    $('#game_failed').attr('disabled', !s.game);
    $('#cancel_game').attr('disabled', !s.game);

    $('#info').val(AM.state.info);
  };

  (function() {
    $("#connect").click(function(evt) {
      AM.player.pname = $("#pname").val();
      AM.connect();
      AM.disable_ui();
    });

    $("#disconn").click(function(evt) {
      AM.disable_ui();
      location.reload(true);
    });

    $("#ping").click(function(evt) {
      AM.send_message('ping');
    });

    $("#submit_seek").click(function(evt) {
      // Player ratings
      AM.player.rating.goko_pro_rating = parseInt($("#pro_rating").val());
      AM.player.rating.goko_casual_rating = parseInt($("#casual_rating").val());

      // Sets owned
      var card_sets = ['Base', 'Intrigue 1', 'Intrigue 2', 'Seaside 1',
          'Seaside 2', 'Alchemy', 'Cornucopia', 'Prosperity 1', 'Prosperity 2',
          'Guilds', 'Hinterlands 1', 'Hinterlands 2', 'Dark Ages 1',
          'Dark Ages 2', 'Dark Ages 3'];
      console.log(parseInt($('#owned_sets').val()));
      AM.player.sets_owned = card_sets.slice(0,parseInt($('#owned_sets').val()));

      // Requirement: game's number of players
      var np = {class: 'NumPlayers', props: {}};
      np.props.min_players = parseInt($('#min_players').val());
      np.props.max_players = parseInt($('#max_players').val());

      // Requirement: game's number of card sets
      var ns = {class: 'NumSets', props: {}};
      ns.props.min_sets = parseInt($('#min_sets').val());
      ns.props.max_sets = parseInt($('#max_sets').val());

      // Requirement: opponents' relative ratings
      var rr = {class: 'RelativeRating', props: {}};
      rr.props.pts_lower = parseInt($('#rdiff').val());
      rr.props.pts_higher = parseInt($('#rdiff').val());
      rr.props.rating_system = $('#rating_system').val();

      // Requirement: game's rating system
      var rs = {class: 'RatingSystem', props: {}};
      rs.props.rating_system = $('#rating_system').val();

      AM.state.seek = {player: AM.player,
                       requirements: [np, ns, rr, rs]};
      console.log(AM.state.seek);

      // Fill out the seek request info
      AM.send_message('submit_seek', {seek: AM.state.seek});
      AM.disable_ui();
    });

    $("#cancel_seek").click(function(evt) {
      AM.send_message('cancel_seek', {seekid: AM.state.seek.seekid});
      AM.state.clear();
      AM.disable_ui();
    });

    $("#accept_offer").click(function(evt) {
      AM.state.accepted_offer = true;
      AM.send_message('accept_offer', {matchid: AM.state.offer.matchid});
      AM.disable_ui();
    });

    $("#decline_offer").click(function(evt) {
      AM.send_message('decline_offer', {matchid: AM.state.offer.matchid});
      AM.disable_ui();
    });

    $("#unaccept_offer").click(function(evt) {
      AM.send_message('unaccept_offer', {matchid: AM.state.offer.matchid});
      AM.disable_ui();
    });

    $("#game_started").click(function(evt) {
      AM.send_message('game_started', {matchid: AM.state.game.matchid});
      AM.state.game = null;
      AM.disable_ui();
    });
    
    $("#game_failed").click(function(evt) {
      AM.send_message('game_failed', {matchid: AM.state.game.matchid});
      AM.state.game = null;
      AM.disable_ui();
    });

    $("#cancel_game").click(function(evt) {
      AM.send_message('cancel_game', {matchid: AM.state.game.matchid});
      AM.state.game = null;
      AM.disable_ui();
    });
  }());
}


/////////////////////////////////////////////////
// Abstract Automatch Client
//
// Connects to the automatch server via websocket. Can be implemented for
// "production" by a Goko Firefox extension, or for testing by an html UI or an
// autmated JS program. 
//
// Receives JSON messages from the server that are formatted like:
//     message = {msgtype: [string], message: [object]},
// and passes them to AM.handle_message(<msgtype>, <message>), which
// implementations are responsible for defining. The msgtype values which the
// server will send are:
// - 'offer_match'
// - 'rescind_offer'
// - 'announce_game'
// - 'unannounce_game'
// - 'confirm_receipt'
//
// Implementation is responsible for keeping its state consistent with the
// server's. The server is "always right" and will ignore client messages that
// don't make sense to it.
// 
// The helper function AM.send_message(msgtype, msg) is provided for sending
// websocket messages to the server. The server can interpret the following
// message types:
// - <msgtype>='disconnect'; msg is ignored
// - <msgtype>='ping'; msg is ignored
// - <msgtype>='submit_seek'; msg is serialized Seek object
// - <msgtype>='cancel_seek'; msg is seekid
// - <msgtype>='accept_offer'; msg is offer's matchid
// - <msgtype>='decline_offer'; msg is offer's matchid
// - <msgtype>='unaccept_offer'; msg is offer's matchid
// - <msgtype>='game_started'; msg is game's matchid
// - <msgtype>='game_failed'; msg is game's matchid

// Automatch data structure: player info and match state
AM = {};
AM.ws = null;
AM.player = {
  pname: null,
  sets_owned: [],
  rating: {
    goko_casual_rating: null,
    goko_pro_rating: null
  }
}
AM.state = {};
AM.state.clear = function() {
  AM.state.seek = null;
  AM.state.offer = null;
  AM.state.accepted_offer = false;
  AM.state.game = null;
  AM.state.info = null;
};
AM.state.clear();

// Create connection and give pname to server
AM.connect = function() {

  // Open new websocket connection to automatch server
  // TODO: Use production server parameters
  AM.ws = new WebSocket("ws://iron:8080/automatch?pname=" + AM.player.pname);

  AM.ws.onopen = function(evt) {
    // Start pinging the server every 10 seconds
    setInterval(function() {
      AM.send_message('ping');
    }, 5*1000);

    // Start detecting disconnect
    setInterval(function() {
      if (Date.now() - AM.last_message > 10*1000) {
        AM.on_timeout();
      }
    }, 1000);
  };

  // For handling formatted messages from the automatch server
  AM.ws.onmessage = function(evt) {
    var msg = JSON.parse(evt.data);
    AM.handle_message(msg.msgtype, msg.message)
  };
};

// For sending formatted messages to the automatch server
AM.send_message = function (msgtype, msg=null) {
  msg_obj = {msgtype: msgtype, message: msg};
  msg_str = JSON.stringify(msg_obj);
  AM.ws.send(msg_str);
};

AM.match_vs = function(match) {
  var players = [];
  //console.log(match);
  $.each(match.seeks, 
    function(i,s) { players.push(s.player.pname); }
  );
  return players.sort().join(' vs ');
};

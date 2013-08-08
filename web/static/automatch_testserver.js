url = "wss://andrewiannaccone.com:8888/automatch"; 

$(document).ready(function() {
  ws = new WebSocket(url + "?pname=SERVER_VIEW");
  ws.onopen = function(evt) {};
  ws.onclose = function(evt) {};
  ws.onmessage = update_ui;
});

match_to_vs = function(match) {
  return match.seeks.map(function(s) {
    return s.player.pname;
  }).join(' vs ');
};

update_ui = function(evt) {
  var data = JSON.parse(evt.data);
  console.log(data);
  if (data.msgtype == 'SERVER_STATE') {
    data = data.SERVER_DATA
  } else {
    return
  }

  var client_str = ''
  for (var c in data.clients) {
    client_str += data.clients[c] + '\n';
  }
  $("#clients").val(client_str)

  var seek_str = ''
  for (var s in data.seeks) {
    seek_str += data.seeks[s].player.pname + '\n';
  }
  $("#seeks").val(seek_str)

  var offer_str = ''
  for (var i=0; i < data.offers.length; i++) {
    var o = data.offers[i];
    offer_str += match_to_vs(o);
    offer_str += ' [Host: ' + o.hostname + ']\n'
  }
  $("#offers").val(offer_str)

  var game_str = ''
  for (var i in data.games) { 
    var g = data.games[i];
    game_str += match_to_vs(g) + '\n';
    game_str += '- Host: ' + g.hostname + '\n';
    game_str += '- RoomID: ' + g.roomid + '\n';
  }
  $("#games").val(game_str)
};

$(document).ready(function() {
  ws = new WebSocket("ws://iron:8080/automatch?pname=SERVER_VIEW");
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

  var client_str = ''
  for (c in data.clients) {
    client_str += data.clients[c] + '\n';
  }
  $("#clients").val(client_str)

  var seek_str = ''
  for (s in data.seeks) {
    seek_str += data.seeks[s].player.pname + '\n';
  }
  $("#seeks").val(seek_str)

  var offer_str = ''

  for (o in data.offers) {
    offer_str += match_to_vs(data.offers[o])
  }
  $("#offers").val(offer_str)

  var game_str = ''
  for (i in data.games) { 
    g = data.games[i];
    game_str += match_to_vs(g) + '\n';
    game_str += '- Host: ' + g.hostname + '\n';
    game_str += '- RoomID: ' + g.roomid + '\n';
  }
  $("#games").val(game_str)
};

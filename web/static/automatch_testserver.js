var data;

(function () {
    "use strict";
    /*jslint browser:true, forin:true */
    /*globals WebSocket,$,console */

    var url, ws, update_ui, match_to_vs, lcCmp;

    url = "wss://andrewiannaccone.com/automatch";

    $(document).ready(function () {
        ws = new WebSocket(url + "?pname=SERVER_VIEW");
        ws.onopen = function (evt) {};
        ws.onclose = function (evt) {};
        ws.onmessage = update_ui;
    });

    match_to_vs = function (match) {
        return match.seeks.map(function (s) {
            return s.player.pname;
        }).join(' vs ');
    };

    Array.prototype.uniq = function () {
        var that = this;
        return $.grep(this, function (v, k) {
            return that.indexOf(v) === k;
        });
    };

    lcCmp = function (x, y) {
        if (x.toString().toLowerCase() !== y.toString().toLowerCase()) {
            x = x.toString().toLowerCase();
            y = y.toString().toLowerCase();
        }
        return x > y ? 1 : (x < y ? -1 : 0);
    };

    update_ui = function (evt) {
        var client_str, seek_str, game_str, g, h, c, s, offer_str, i, o, history_str;
        data = JSON.parse(evt.data);
        console.log(data);
        if (data.msgtype === 'SERVER_STATE') {
            data = data.SERVER_DATA;

            data.clients = data.clients.sort(lcCmp).uniq();
            data.seeks = data.seeks.sort(lcCmp).uniq();
            data.offers = data.offers.sort(lcCmp).uniq();
            data.games = data.games.sort(lcCmp).uniq();
        } else {
            return;
        }

        client_str = '';
        for (i = 0; i < data.clients.length; i += 1) {
            c = data.clients[i];
            client_str += c + '\n';
        }
        $("#clients").val(client_str);

        seek_str = '';
        for (i = 0; i < data.seeks.length; i += 1) {
            s = data.seeks[i];
            seek_str += s.player.pname + '\n';
        }
        $("#seeks").val(seek_str);

        offer_str = '';
        for (i = 0; i < data.offers.length; i += 1) {
            o = data.offers[i];
            offer_str += match_to_vs(o);
            offer_str += ' [Host: ' + o.hostname + ']\n';
        }
        $("#offers").val(offer_str);

        game_str = '';
        for (i = 0; i < data.games.length; i += 1) {
            g = data.games[i];
            game_str += match_to_vs(g) + '\n';
        }
        $("#games").val(game_str);

        history_str = '';
        for (i = 0; i < data.history.length; i += 1) {
            h = data.history[i];
            history_str += match_to_vs(h) + '\n';
        }
        $("#history").val(history_str);
    };
}());

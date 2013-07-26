// ==UserScript==
// @name        GokoAutomatch
// @namespace   gokomatch
// @description Automatch for goko
// @include     http://play.goko.com/Dominion/gameClient.html
// @include     https://play.goko.com/Dominion/gameClient.html
// @version     2 
// @grant       none
// ==/UserScript==

// TODO: synchronize stuff

// Define the Automatch package namespace and our basic data structure. 
var AM = {ws: null,
          server: null,
          player: null,
          state: {seek: null,
                  offer: null,
                  game: null,
                  playing: null}};

// Make AM available in the global namespace of Goko's script. This is
// "unsafe" in that Goko can potentially read this JS script, disable it, 
// etc. See the Greasemonkey security wiki for details.
unsafeWindow.AM = AM;

console.log('AM version nothing2');

// Choose Automatch server
AM.server = 'gokologs.drunkensailor.org';     // For production
//AM.server = 'iron:8080';                      // For testing

// Import some Goko helper functions
$.getScript('http://' + AM.server + '/static/goko_helpers.js');

// Automatch initialization uses Goko's mtgRoom global.  Append initialization
// to a method that gets run right after mtgRoom gets instantiated. See
// DominionClient.js ~ line 310.
//
AM.rgc = FS.MeetingRoom.prototype.registerGameClass;
FS.MeetingRoom.prototype.registerGameClass = function(gameClass) {
    mtgRoom.GameClass = gameClass;
    //AM.rgc(gameClass);    // Run the Goko method like normal
    AM.initialize();      // Then initialize automatch
};

AM.initialize = function() {
    console.log('Initializing Automatch')

    // Asynchronously start building the popup dialogs
    AM.init_popups();

    // Whenever a player (re-)enters the Goko lobby...
    mtgRoom.bind(FS.MeetingRoomEvents.MEETING_ROOM.GATEWAY_CONNECT, function() {
        AM.fetch_player_info();    // ... start getting Goko player info asynchronously
        AM.connect();              // ... while connecting to the automatch server
        AM.add_automatch_button(); // ... and adding Automatch to the lobby menu
    });
};

/*
 * Functions for fetching Goko player info
 */

AM.fetch_player_info = function() {
    // Store player info here. Other methods expect this location.
    AM.player = {};
    AM.player.rating = {};

    // Get Goko identity
    AM.player.pname = mtgRoom.localPlayer.get('playerName');
    AM.player.pid = mtgRoom.localPlayer.get('playerId');

    // Get ratings and cards owned asynchronously. After each response,
    // check whether we should enable the seek request button yet.
    AM.fetch_rating('pro', AM.check_player_info);
    AM.fetch_rating('casual', AM.check_player_info);
    AM.fetch_sets_owned(AM.check_player_info);
};

AM.fetch_rating = function(rsys, callback) {
    console.log('Getting ' + rsys + ' rating');

    var rsys_ids = {};
    rsys_ids.casual = mtgRoom.helpers.RatingHelper._globalRatingSystemId;
    rsys_ids.pro = mtgRoom.helpers.RatingHelper.ratingSystemPro;

    var rsys_props = {};
    rsys_props.casual = 'goko_casual_rating';
    rsys_props.pro = 'goko_pro_rating';

    // TODO: look up guest ratings correctly
    if (conn.connInfo.kind === "guest") {
        AM.player.rating[rsys_props[rsys]] = 1000;
        callback();
        return;
    }

    mtgRoom.conn.getRating({
        playerId: AM.player.pid,
        ratingSystemId: rsys_ids[rsys]
    }, function(resp) {
        AM.player.rating[rsys_props[rsys]] = resp.data.rating;
        callback();
    });
}

AM.fetch_sets_owned = function(callback) {
    console.log('getting sets owned');

    // Guests only have Base. No need to check.
    if (conn.connInfo.kind === "guest") {
        AM.player.sets_owned = ['Base'];
        callback();
        return;
    }

    var cards_sets = {
        Cellar: 'Base',
        Coppersmith: 'Intrigue 1',
        Baron: 'Intrigue 2',
        Ambassador: 'Seaside 1',
        Explorer: 'Seaside 2',
        Apothecardy: 'Alchemy',
        Hamlet: 'Cornucopia',
        Bishop: 'Prosperity 1',
        Mint: 'Prosperity 2',
        Baker: 'Guilds',
        Duchess: 'Hinterlands 1',
        Oasis: 'Hinterlands 2',
        Altar: 'Dark Ages 1',
        Beggar: 'Dark Ages 2',
        Counterfeit: 'Dark Ages 3'
    };

    // Goko Developer #1: "C'mon... how often are you going to need to look up
    // what cards a player owns? Let's nest it 3 asynchronous callbacks deep."

    // Goko Developer #2: "No, that's bad design. Put it 4 deep."

    conn.getInventoryList({}, function(r) {
        var myInv = r.data.inventoryList.filter( function(x) {
            return x.name==="Personal";
        })[0];
        conn.getInventory({
            inventoryId: myInv.inventoryId,
            tagFilter: "Dominion Card"
        }, function(r) {
            conn.getObjects2({
                objectIds: r.data.objectIds
            }, function(r) {
                var sets_owned = [];
                r.data.objectList.map( function(c) {
                    var set = cards_sets[c.name];
                    if (set && sets_owned.indexOf(set) < 0) {
                        sets_owned.push(set)
                    }
                });
                AM.player.sets_owned = sets_owned;
                callback();
            });
        });
    });
};

// Enable the submit seek button if the player info is complete.
AM.check_player_info = function() {
    if (AM.player.rating.goko_pro_rating
        && AM.player.rating.goko_casual_rating
        && AM.player.sets_owned) {
            console.log('Got all player info');
            $('#seekreq').attr('disabled',false);
    }
};

/*
 * Functions for communicating with the Automatch server
 */

AM.connect = function() {
    if (!AM.ws) { // TODO: also check if disconnected

        // Connect to Automatch server via WebSocket
        AM.ws = new WebSocket('ws://' + AM.server + '/automatch?pname=' + AM.player.pname);

        // Functions to be invoked when the server confirms receipt
        AM.ws.callbacks = {};

        AM.ws.onopen = function(evt) {
            console.log('Connected to Automatch server as ' + AM.player.pname);
            AM.state = {seek: null,
                        offer: null,
                        game: null,
                        playing: null};
            if (typeof AM.show_seekpop !== 'undefined') {
                AM.show_seekpop(false);
            }
            if (typeof AM.show_offerpop !== 'undefined') {
                AM.show_offerpop(false);
            }
            if (typeof AM.show_gamepop !== 'undefined') {
                AM.show_gamepop(false);
            }
        };

        // If connection is lost, wait 3 second and reconnect
        // TODO: does the WS detect timeouts?
        // TODO: notify player of disconnect
        AM.ws.onclose = function() {
            console.log('Lost contact with Automatch server. Reconnecting');
            AM.ws = null;
            setTimeout(AM.connect,3000);
        };

        // Messages from server invoke the function named "AM.<msgtype>"
        AM.ws.onmessage = function(evt) {
            var msg = JSON.parse(evt.data);
            console.log('Received ' + msg.msgtype + ' message from automatch server:');
            console.log(msg.message);
            AM[msg.msgtype](msg.message);
        };
    }
}

AM.send_message = function (msgtype, msg, callback) {
    var msgid = AM.player.pname + Date.now();
    var msg_obj = {msgtype: msgtype,
                   message: msg,
                   msgid: msgid};
    var msg_str = JSON.stringify(msg_obj);

    AM.ws.callbacks[msgid] = callback;
    AM.ws.send(msg_str);

    console.log('Sent ' + msgtype + ' message to server:');
    console.log(msg_obj);
};

/*
 * Functions invoked by messages from the Automatch server
 */

// Invoke the callback registered to this message's id, if any.
AM.confirm_receipt = function(msg) {
    console.log('Receipt of message confirmed: ' + msg.msgid);
    var callback = AM.ws.callbacks[msg.msgid];
    if (typeof callback !== 'undefined' && callback !== null) {
        console.log(callback);
        callback();
    }
};

AM.confirm_seek = function(msg) {
    AM.state.seek = msg.seek;
};

AM.offer_match = function(msg) {
    AM.state.seek = null;
    AM.state.offer = msg.offer;
    AM.show_offerpop(true);
};

AM.rescind_offer = function(msg) {
    AM.state.offer = null;
    // TODO: handle this in a more UI-consistent way
    AM.show_offerpop(false);
    alert('Automatch offer was rescinded:\n' + msg.reason);
};

AM.announce_game = function(msg) {
    AM.state.offer = null;
    AM.state.game = msg.game;

    // Show game announcement (non-blocking)
    AM.show_offerpop(false);
    AM.show_gamepop(true);

    AM.change_room(AM.state.game.roomname, function() {
        if (AM.state.game.hostname === AM.player.pname) {
            
            // If host, go to the game room and create a game.
            var opps = AM.get_oppnames(AM.state.game, AM.player.pname);

            // After all opponents join:
            // TODO: Why am I not getting any join events?
            var after_join = function() {
                var g = AM.get_game_owned_by(AM.player.pname);
                if (typeof g !== 'undefined'
                        && g.get('joined').length === AM.state.game.seeks.length) {
                    console.log('All opponents have joined. Automatch complete.');

                    // Hide the game announcement dialog
                    AM.show_gamepop(false);

                    // Restore default join request behavior
                    AM.set_autoaccept(false);

                    // Stop listening for joins
                    mtgRoom.unbind(JOIN, after_join);
                }
            };
            var JOIN = FS.MeetingRoomEvents.MEETING_ROOM.PLAYER_JOINED_TABLE;
            mtgRoom.bind(JOIN, after_join);

            // Accept guest's join request automatically.
            AM.set_autoaccept(true, opps);

            // Finally ready to create the game
            AM.create_game(opps, AM.state.game.rating_system);

            // TODO: optionally start game automatically

            // When the game starts...
            AM.on_game_start = function() {

                // ... update local variables
                AM.state.playing = AM.state.game;
                AM.state.game = null;

                // ... notify the server
                AM.send_message('game_started', AM.state.playing.matchid);
            }
        } else {

            // If guest, go to the game room and wait for the host's game.
            intvl = setInterval(function() {
                var g = AM.get_game_owned_by(AM.state.game.hostname);
                if (g) {
                    clearInterval(intvl);

                    // Join automatically when it appears.
                    console.log('Joining automatch game. Automatch complete.');
                    AM.join_game(g);
                    AM.show_gamepop(false);

                    // When the game starts...
                    AM.on_game_start = function() {
                        
                        // ... update local variables
                        AM.state.playing = AM.state.game;
                        AM.state.game = null;

                        // ... notify the server
                        AM.send_message('game_started', AM.state.playing.matchid);
                    }
                }
            }, 500);
        }
    });
};

// TODO: deal with possibility that unannounce arrives before announce
AM.unannounce_game = function(msg) {
    AM.state.game = null;
    AM.state.reason = msg.reason;
};

/*
 * UI Construction
 */

AM.init_popups = function(callback) {

    // Wait until Goko creates the "viewport" element.
    if ($('#viewport').length == 0) {
        console.log("Can't build Automatch UI yet... waiting 500 ms");
        setTimeout(AM.init_UI, 500);
        return;
    }

    $.get('http://' + AM.server + '/static/seekpop.html', function(data){
        $(data).appendTo("#viewport");
        $.getScript('http://' + AM.server + '/static/seekpop.js');
    });

    $.get('http://' + AM.server + '/static/offerpop.html', function(data){
        $(data).appendTo("#viewport");
        $.getScript('http://' + AM.server + '/static/offerpop.js');
    });

    $.get('http://' + AM.server + '/static/gamepop.html', function(data){
        $(data).appendTo("#viewport");
        $.getScript('http://' + AM.server + '/static/gamepop.js');
    });
};

AM.add_automatch_button = function() {

    // Wait until Goko creates its lobby button toolbar and Automatch dialogs
    // have all been created and we're connected to the automatch server.
    if (($('.room-section-header-buttons').length == 0)
            || $('#seekpop').length == 0
            || $('#offerpop').length == 0
            || $('#gamepop').length == 0 
            || typeof AM.ws === 'undefined'
            || AM.ws === null
            || AM.ws.readyState != 1) {
        console.log("Can't add Automatch button yet... waiting 500 ms");
        setTimeout(AM.add_automatch_button, 500);
        return;
    }

    // ... and adding the "Automatch" button
    if ($('#automatch_button').length == 0) {
        $('.room-section-header-buttons').append(
            $('<button id="automatch_button"></button>')
                .addClass('fs-mtrm-text-border')
                .addClass('fs-mtrm-dominion-btn')
                .html('Automatch'));

        // Clicking "Automatch" brings up the seek request dialog
        $('#automatch_button').click(function() {
            AM.show_seekpop(true);
        });
    }

    // Also delete the "Play Now" button. Seriously, Goko?
    $('.room-section-btn-find-table').remove();

    if (typeof callback !== 'undefined') {
      callback();
    }
}

console.log('Automatch script loaded.');

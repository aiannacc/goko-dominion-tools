// ==UserScript==
// @name        Goko automatch
// @namespace   gokomatch
// @description Automatch for goko
// @include     http://play.goko.com/Dominion/gameClient.html
// @include     https://play.goko.com/Dominion/gameClient.html
// @version     1
// @grant       none
// ==/UserScript==
var foo = function () {

// Automatch/Autojoin module

// Add Automatch button to the lobby menu
//
var buttonsScript = $('script#fs-mtrm-tpl-classic-room-section')[0];
buttonsScript.textContent = buttonsScript.textContent.replace(
        "<li><button class='fs-mtrm-text-border fs-mtrm-dominion-btn room-section-btn-create-table'>Create Game</button></li>",
        "<li><button class='fs-mtrm-text-border fs-mtrm-dominion-btn room-section-btn-create-table'>Create Game</button></li>" +
        "<li><button onclick='mtgRoom.automatch();' class='fs-mtrm-text-border fs-mtrm-dominion-btn room-section-btn-automatch'>Automatch</button></li>"
);

// Switch to a named lobby room (e.g. "Council Room" or "Outpost II")
// Add this function to the MeetingRoom singleton
//
FS.MeetingRoom.prototype.changeRoomByName = function(roomName) {
    var dest = mtgRoom.roomList.findByRoomName(roomName);
    var destId = dest.attributes.roomId;
    mtgRoom.getHelper('ZoneClassicHelper').changeRoom(destId);
};

// Switch to a specified lobby and join the specified table
// Add this function to the MeetingRoom singleton.
//
FS.MeetingRoom.prototype.joingame = function (roomname,table,seat) {
    mtgRoom.changeRoomByName(roomname);
    setTimeout(function() { sitdown() }, 5000);
    sitdown = function() {
        mtgRoom.helpers.ZoneClassicHelper.sitAtTable(table,seat.get('number'));
    }
}

// Automatch: the holy grail
//
// Submit a request to the automatch server and wait for a response.
// When matched, automatically go to Outpost and host or join.
//
// TODO: this approach to
//
FS.MeetingRoom.prototype.automatch = function () {
    var xmlHttp;

    // Player requesting automatch
    var me           = this.localPlayer;
    var myPlayerName = me.get('playerName');
    var myPlayerId   = me.get('playerId');

    // Request our rating from Goko database.
    // Continue via asynchronous callback after receiving rating
    var myProRating;
    var ratingHelper = this.getHelper('RatingHelper');

    // Go to the automatch room and manually join a game
    // TODO: look for host's table and join automatically
    var join_automatch_game = function(match) {
        var zch, roomList, tableList, automatch_table, joinButton;

        // Join the room
        mtgRoom.changeRoomByName('Outpost');

        // TODO: better notification for players when a match is found
        console.log('You have been automatched with ' + match.host.playerName + '\n' +
              'You are the guest.');

        setTimeout(function () {
            roomList = mtgRoom.getRoomList();
            tableList = roomList.findByRoomId(mtgRoom.currentRoomId).get('tableList');
            automatch_table = tableList.find(function(table) {
                return table.get('owner') && table.get('owner').getId() === match.host.playerId;
            });

            joinButton = automatch_table.view.$el.find('.join')[0];
            joinButton.click();

        }, 2000);

    };

    // create a hosted game
    var create_automatch_game = function(match) {
        var zch, testKingdom, testSettings, testOpts;

        // TODO: Create a random pro game instead of this client-side nonsense.
        testKingdom = ["gardens","cellar","smithy", "village","councilRoom",
                       "bureaucrat","chapel","workshop","festival","market"];
        testSettings = {"name":"Automatch Test Game",
                    "seatsState":[true,true,false,false,false,false],
                    "gameData":{"uid":""},
                    "kingdomCards": testKingdom,
                    "platinumColony":false,
                    "useShelters":false,
                    "ratingType":"unrated"};
        testOpts = {settings: JSON.stringify(testSettings),
                    isLock: false,
                    isRequestJoin: true,
                    isRequestSit: false,
                    tableIndex: null};

        // Create a table and seat us at it
        zch = mtgRoom.getHelper('ZoneClassicHelper');
        zch.createTable(testOpts);
    };

    // Go to the automatch room and host a game
    var host_automatch_game = function(match) {
        // Join the room
        mtgRoom.changeRoomByName('Outpost');

        // TODO: better notification for players when a match is found
        console.log('You have been automatched with ' + match.guest.playerName + '\n' +
              'You are the host');

        // give Goko's events a bit of time before creating the game
        setTimeout(function () {

            // temporarily set the "request to join" popup to auto-accept the
	    // matched player and reject all others
            mtgRoom.views.ClassicRoomsPermit.old_showByRequest =
            mtgRoom.views.ClassicRoomsPermit.showByRequest;
            mtgRoom.views.ClassicRoomsPermit.showByRequest = function (req) {
                mtgRoom.views.ClassicRoomsPermit.old_showByRequest(req);
                var requestingPlayer = mtgRoom.playerList.findByAddress(req.data.playerAddress);
                if (requestingPlayer.getId() == match.guest.playerId) {
                    mtgRoom.views.ClassicRoomsPermit.onClickAsk();
                } else {
                    mtgRoom.views.ClassicRoomsPermit.onClickCancel();
                }
            };

            create_automatch_game(match);

            // restore the "request to join" popup after the matched
            // player has joined
            setTimeout(function () {
                mtgRoom.views.ClassicRoomsPermit.showByRequest =
                mtgRoom.views.ClassicRoomsPermit.old_showByRequest;
            }, 5000);

        }, 1000);
    };

    // Callback for continuing after receiving response from Automatch server
    var handle_automatch_response = function() {

        if (xmlHttp.readyState==4 && xmlHttp.status!=200){
            // Received ready response from server. Wait for match to be made.
            console.log('Connection with Automatch server established.');
            console.log('Awaiting match.');
        } else if (xmlHttp.readyState==4 && xmlHttp.status==200){
            var match, matchJSON;

            // Received automatch response
            matchJSON = xmlHttp.response;
            console.log(matchJSON);
            match = JSON.parse(matchJSON);

            // Log automatch data to JS console.
            console.log(match);

            // TODO: Allow a player to accept or decline the proposed match.

            // Host or join the proposed game
            if (myPlayerId === match.host.playerId) {
                host_automatch_game(match);
            } else if (myPlayerId === match.guest.playerId) {
                join_automatch_game(match);
            } else {
                console.log('Error: invalid match playerid data');
            }
        }
    };

    // Callback for continuing after receiving rating
    var handle_rating_response = function(resp) {
        var host, port, rel, args, url, key;

        console.log('Received rating response. Continuing.');

        // Read rating
        if (!resp || !resp.data || !resp.data.ratingPro) {
            console.log('Warning: Response has no rating data.');
        } else {
            console.log("resp = " + JSON.stringify(resp));
            myProRating = resp.data.ratingPro;
        }

        // Build Automatch server url
        host = "http://gokologs.drunkensailor.org";
        port = "8080";
        rel  = "automatch";
        args = {
            'playerName': myPlayerName,
            'playerId': myPlayerId,
            'proRating': myProRating,
            'sets': ''
        };
        url = host + ':' + port + '/' + rel + '?';
        for (key in args) {
            url += key + '=' + args[key] + '&';
        }

        // Request match from Automatch server.
        // Continue via asynchronous callback when a match is found.
        xmlHttp = new XMLHttpRequest();
        xmlHttp.onreadystatechange = handle_automatch_response;
        xmlHttp.open("GET", url, true);
        xmlHttp.send();
        console.log('Sent Automatch request. Awaiting response.');
    };

    ratingHelper.getRating(
        {
            playerId: myPlayerId,
            $elPro: $(document.createElement('div')),
            $elQuit: $(document.createElement('div'))
        },
        handle_rating_response
    );
    console.log('Sent rating request. Awaiting response.');

};

// Autojon: a poor man's automatcth
//
// Searches lobbies for open two-player pro games.
// Offer the best match to the user and automatically join if accepted.
// Add this function to the MeetingRoom singleton
//
// NOTE: This doesn't quite work as written. Goko's framework doesn't actually
//       return table info for any lobby except the one you're already in
//
FS.MeetingRoom.prototype.autojoin = function () {

    // Asynchronously get my rating and continue in callback
    my_pid = mtgRoom.localPlayer.get('playerId');
    mtgRoom.getHelper('RatingHelper').getRating({
        playerId: my_pid,
        $elPro: $(document.createElement('div')),
        $elQuit: $(document.createElement('div'))
    }, function (resp) {

        // Get our rating
        if (!resp.data || !resp.data.ratingPro) {
            console.log('Error: could not find your pro rating');
            my_rating = undefined;
        } else {
            my_rating = resp.data.ratingPro;
            console.log('Your rating is ' + my_rating);
        }

        // Search in all rooms on the server
        rooms = mtgRoom.roomList.models;
        console.log(rooms.length)
        for (var i=0; i<rooms.length; i++) {

            // Room name and ID
            room = mtgRoom.roomList.models[i];
            room_name    = room.get('name');
            room_id      = room.get('roomId');

            // Only search in rooms with at least 5 players
            if (room.get('currentPlayers')<5) continue;

            console.log(room_name);

            // Search all tables in the room
            tables = room.get('tableList').models;

            for (var j=0; j<tables.length; j++) {

                // Table ID
                table = tables[j];
                table_number = table.get('number');

                // Table must have exactly one player (the host)
                if (table.get('joined').models.length != 1) continue;

                // Skip games that have already started
                if (table.get('state') != 'Idle') continue;

                // Read table settings
                settings = JSON.parse(table.get('settings'));

                // Skip non-pro games
                //if (settings.ratingType != 'pro') continue;

                // Skip request-to-join tables
                // TODO: does "requestSit" mean something similar?
                if (table.get('requestJoin')) continue;

                // Make sure our rating is high enough for the host
                min_rating_regex = '/\b(\d+)(\d{3}|k)\+/';
                var m = settings.name.toLowerCase().match(min_rating_regex);
                if (m) {
                    min_rating = parseInt(m[1],10) * 1000 +
                        (m[2] == 'k' ? 0 : parseInt(m[2],10));
                    if (my_rating < min_rating) continue;
                }

                // Asynchronously get the hosts's rating and callback
                // TODO: Cancel unnecessary queries after finding a match?
                host = table.get('owner').get('player');
                host_name = host.get('playerName');
                mtgRoom.getHelper('RatingHelper').getRating({
                    playerId: host.get('playerId'),
                    $elPro: $(document.createElement('div')),
                    $elQuit: $(document.createElement('div'))
                }, function (resp) {

                    console.log('poop3.');

                    // Get host rating
                    if (!resp.data || !resp.data.ratingPro) {
                        host_rating = -1
                    } else {
                        host_rating = resp.data.ratingPro;
                    }
                    console.log('Host rating is ' + host_rating);


                    // Make sure host's rating is high enough for us
                    // TODO: Configure in options?
                    //if (host_rating > my_rating - 2000) {

                        // Declare victory
                        console.log('Matched with ' +
                            host_name + '(' + host_rating + ')' +
                            'on table #' + table_number +
                            'in ' + room_name);

                        return;

                        // TODO: go join the room
                        // TODO: stop the looping and other async requests
                    //}
                });
            }
        }
    });
}


// Unused code to find a half-empty room
//var halfEmpty = function(room,index,roomlist) {
//    numPlayers = room.attributes.currentPlayers;
//    return numPlayers < room.attributes.maxPlayers/2;
//}
//var halfEmptyRooms = mtgRoom.roomList.models.filter(halfEmpty);
//var roomId = halfEmptyRooms[0].attributes.roomId;
}; document.addEventListener ('DOMContentLoaded', foo);

// ==UserScript==
// @name        GokoAutomatch
// @namespace   gokomatch
// @description Automatch for goko
// @include     http://play.goko.com/Dominion/gameClient.html
// @include     https://play.goko.com/Dominion/gameClient.html
// @version     1
// @grant       none
// ==/UserScript==

// TODO: Read requirement info from Automatch request popup.

// Automatch data structure
AM = { ws: null,
       player: { pname: null,
                 sets_owned: [],
                 rating: { goko_casual_rating: null,
                           goko_pro_rating: null } },
       state: { seek: null,
                offer: null,
                game: null
       }
};

AM.clear_state = function() {
    AM.state.seek = null;
    AM.state.offer = null;
    AM.state.game = null;
};

AM.automatch_button = function() {
    if (AM.ws === null) {
        AM.connect();
    }
    AM.retrieve_player_info(AM.show_seek_popup);
};

// Create websocket connection to automatch server
// TODO Start this asynchronous function as soon as mtgRoom is defined, 
AM.connect = function() {

    // Get Goko username
    AM.player.pname = mtgRoom.localPlayer.get('playerName');
    AM.player.phash = mtgRoom.localPlayer.playerId;

    // TODO: Connect to production server instead of test server
    // TODO: Deal with connection failures and timeouts
    AM.ws = new WebSocket("ws://gokologs.drunkensailor.org:8080/automatch?pname=" + AM.player.pname);

    // Invoked when the WebSocket connection is established
    AM.ws.onopen = function(evt) {
        console.log('Connected to automatch server');

        // Asynchronously request sets (slow) so we don't have to wait later
        AM.player.retrieve_sets_owned();

        // Start pinging the server every 10 seconds
        setInterval(function() {
            AM.send_message('ping');
            AM.last_message = Date.now();
        }, 10*1000);

        // Detect timeout if no response for 30 seconds
        setInterval(function() {
            if (Date.now() - AM.last_message > 30*1000) {
                alert('Lost contact with automatch server.');
                // TODO: Now what?
            }
        }, 1000);
    };

    // For handling formatted messages from the automatch server
    AM.ws.onmessage = function(evt) {
        var msg = JSON.parse(evt.data);
        if (msg.msgtype !== 'confirm_receipt') {
            console.log('Received message (' + msg.msgtype + ')');
            console.log(msg.message);
        }

        // Update timeout deadline
        AM.last_message = Date.now();

        // Invoke named function
        AM[msg.msgtype](msg.message);
    };

    // For sending formatted messages to the automatch server
    AM.send_message = function (msgtype, msg=null) {
        msg_obj = {msgtype: msgtype, message: msg};
        msg_str = JSON.stringify(msg_obj);
        AM.ws.send(msg_str);
    };
};

///////////////////////////////
// Handle messages from server 

// TODO: identify the message that is being confirmed
AM.confirm_receipt = function(msg) { };

AM.confirm_seek = function(msg) {
    AM.state.seek = msg.seek;
    AM.state.seek.confirmed = true;
    $('seekpop').hide();
};

AM.offer_match = function(msg) {
    AM.state.seek = null;
    AM.state.offer = msg.offer;

    AM.show_offer_popup();
};

AM.rescind_offer = function(msg) {
    AM.state.offer = null;
    AM.state.reason = msg.reason;
    $('#offerpop').hide();
};

AM.announce_game = function(msg) {
    // Update state
    AM.state.offer = null;
    AM.state.game = msg.game;

    // Determine whether we're hosting
    var is_host = AM.state.game.hostname === AM.player.pname;

    // Show game announcement (non-blocking)
    $('#offerpop').hide();
    AM.show_game_announcement(is_host);

    // Host or join game when Goko fires the room change event.
    var room_changed = FS.MeetingRoomEvents.MEETING_ROOM.CORE_CHANGE_ROOMS;
    if (is_host) {
        mtgRoom.bind(room_changed, AM.create_automatch_game);
    } else {
        mtgRoom.bind(room_changed, AM.join_automatch_game);
    }

    // Ask Goko to take us to Outpost and then fire the room change event.
    // TODO: Have automatch suggest a room instead.
    mtgRoom.helpers.ZoneClassicHelper.changeRoom(AM.getRoomId('Outpost'));
};

AM.getRoomId = function(room_name) {
    return mtgRoom.roomList.models.filter(function(m) { 
        return m.get('name') === room_name; 
    })[0].get('roomId');
}

// TODO: deal with possibility that unannounce arrives before announce
AM.unannounce_game = function(msg) {
    AM.state.game = null;
    AM.state.reason = msg.reason;
};

////////////////////////////////

AM.show_game_announcement = function(host) {
    console.log('Entering show_game_announcement');
    var h, hg;

    if ($("#announcepop").length == 0) {
        console.log('Creating game announcement popup');
        $("#viewport").append(AM.create_lightbox('announcepop'));

        h = '<h3 style="text-align:center">Creating Automatch Game</h3><br>';
        h += 'Automatch will seat you automatically.';
        h += '<div id="hostguest">HOST OR GUEST</div><br>';
        h += '<input type="button" class="automatch" id="abortgame" value="Abort" />';
        $('#announcepop').html(h);

        if (host) {
            hg = 'You are the host. Please wait for your opponent to join.';
        } else {
            hg = 'You are the guest. Automatch will seat you automatically\
                  when your opponent creates the game.';
        }
        $('#hostguest').html(hg);

        $('#abortgame').click(function (evt) {
            AM.send_message('cancel_game', {matchid: AM.state.game.matchid});
            $('#announcepop').hide();
        });
    }

    // Show the built and updated popup
    console.log('Showing announce popup');
    $("#announcepop").show();
};

//// Seems to work fine. --AI, July 23, 2013
//AM.test_snap_create = function() {
//    var secretChamberId = mtgRoom.roomList.models.filter(function(m) { 
//        return m.get('name') === 'Secret Chamber' })[0].get('roomId');
//    var councilRoomId = mtgRoom.roomList.models.filter(function(m) { 
//        return m.get('name') === 'Council Room' })[0].get('roomId');
//
//    var testKingdom = ["gardens", "cellar", "smithy", "village", "councilRoom",
//                      "bureaucrat", "chapel", "workshop", "festival", "market"];
//    var testSettings = {name: 'Test',
//                        seatsState: [true,true,false,false,false,false],
//                        gameData: {uid: ""},
//                        kingdomCards: testKingdom,
//                        platinumColony: false,
//                        useShelters: false,
//                        ratingType: "pro"};
//    var testOpts = {settings: JSON.stringify(testSettings),
//                    isLock: false,
//                    isRequestJoin: true,
//                    isRequestSit: false,
//                    tableIndex: null};
//
//    var create_table = function() {
//        console.log('entering create_table');
//        mtgRoom.helpers.ZoneClassicHelper.createTable(testOpts);
//        console.log('exiting create_table');
//    }
//
//    var room_changed = FS.MeetingRoomEvents.MEETING_ROOM.CORE_CHANGE_ROOMS;
//    mtgRoom.bind(room_changed, create_table);
//
//    mtgRoom.helpers.ZoneClassicHelper.changeRoom(councilRoomId);
//}

AM.create_automatch_game = function() {
    var testKingdom, testSettings, testOpts, i;

    var ss = [false, false, false, false, false, false];
    for (i = 0; i < AM.state.game.seeks.length; i++) {
        ss[i] = true;
    }

    // NOTE: No need to explicitly generate a random kingdom. Goko will ignore
    //       this parameter when it actually starts a Pro game.
    // TODO: Do I need to enter any of these settings at all?
    // TODO: Is there a helper method for creating a table?
    testKingdom = ["gardens", "cellar", "smithy", "village", "councilRoom",
                   "bureaucrat", "chapel", "workshop", "festival", "market"];
    testSettings = {name: AM.state.game.matchid,
                    seatsState: ss, 
                    gameData: {uid: ""},
                    kingdomCards: testKingdom,
                    platinumColony: false,
                    useShelters: false,
                    ratingType: "pro"};
    testOpts = {settings: JSON.stringify(testSettings),
                isLock: false,
                isRequestJoin: true,
                isRequestSit: false,
                tableIndex: null};

    // Temporarily set the "request to join" popup to auto-accept the
    // matched player and reject all others
    // TODO: Why isn't this working?
    //var crp = mtgRoom.views.ClassicRoomsPermit;
    //crp.old_showByRequest = crp.showByRequest;
    //crp.showByRequest = function (req) {

    //    // Show the join dialog. TODO: is this necessary?
    //    crp.old_showByRequest(req);

    //    // Names of our automatch opponents
    //    var opps = AM.state.game.seeks.map(function(s) { return s.player.pname; });

    //    // Name of player asking to join
    //    var joiner = mtgRoom.playerList
    //                        .findByAddress(req.data.playerAddress)
    //                        .get('name');

    //    if (opps.indexOf(joiner) >= 0) {
    //        crp.onClickAsk();    // Accept opponent

    //        // Restore the original method. TODO: wait for all N-1 opps
    //        crp.showByRequest = crp.old_showByRequest;
    //        delete crp.old_showByRequest;
    //    } else {
    //        crp.onClickCancel(); // Reject others
    //    }
    //};

    mtgRoom.helpers.ZoneClassicHelper.createTable(testOpts);
    // TODO: unbind from CORE_CHANGE_ROOMS
    $('#announcepop').hide();
};

AM.join_automatch_game = function() {
    var intvl = setInterval(function() {
        // Look for the host's game, if it has been created.
        var tables = mtgRoom.helpers.ZoneClassicHelper.currentTableList.models;
        var owned_tables = tables.filter( function(m) { 
            return m.get('owner') !== null;
        });
        var am_table = owned_tables.filter(function(m) { 
            return m.get('owner')
                    .get('player')
                    .get('playerName') === AM.state.game.hostname;
        })[0];


        if (am_table === undefined) {
            console.log('Automatch table not found. Waiting 500 ms.');
        } else {
            clearInterval(intvl); 
            $('#announcepop').hide();
            console.log('Found automatch table. Joining.');

            // Get the table's index
            var opts = {table: am_table.get('number')};

            // Find first empty seat
            opts.seat = am_table.get('seats').filter(function(s) {
                return s.getOccAddr() === null;
            })[0].get('number');

            // Join, sit, and tell Goko that we're ready
            conn.joinAndSit(opts, function () {
                opts.ready = true;
                conn.setReady(opts); 
                console.log('Automatch complete. Ready to start game.');
            }); 

            //conn.joinTable(opts, function(r) { 
            //    conn.sitSeat(opts, function(resp) {
        }
    },5000);
}

AM.player.retrieve_sets_owned = function() {
    if (conn.connInfo.kind === "guest") {
        AM.player.got_sets_owned = true;
        return ['Base'];
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
        Counterfeit: 'Dark Ages 3',
        Envoy: 'Envoy',
        Governor: 'Governor',
        Stash: 'Stash'
    }
    cards_sets['Walled Village'] = 'Walled Village';
    cards_sets['Black Market'] = 'Black Market';

    var sets_owned = [];

    conn.getInventoryList({}, function(r) {
        invId = r.data.inventoryList.filter( function(x) {
            return x.name==="Personal";
        })[0].inventoryId;
        conn.getInventory(
            {inventoryId: invId, tagFilter: "Dominion Card"},
            function(r) {
                conn.getObjects2( {objectIds: r.data.objectIds}, function(r) {
                    r.data.objectList.map( function(c) {
                        sets_owned.push(cards_sets[c.name]);
                    });
                    sets_owned = jQuery.unique(sets_owned);
                    sets_owned.map( function(s) {
                        if (s!==undefined) {
                            AM.player.sets_owned.push(s);
                        }
                    })

                    AM.player.got_sets_owned = true;
                }               
            );
        });
    });
}

AM.player.retrieve_rating = function() {
    mtgRoom.getHelper('RatingHelper').getRating({
        playerId: mtgRoom.localPlayer.get('playerId'),
        $elPro: $(document.createElement('div')),
        $elQuit: $(document.createElement('div'))
    }, function (resp) {
        AM.player.rating.goko_pro_rating = resp.data.ratingPro;
        AM.player.rating.goko_casual_rating = resp.data.rank;
        AM.player.got_rating = true;
    });
};

AM.retrieve_player_info = function(callback) {
    console.log('Requesting player info');

    // Start asynchronous requests, if necessary
    if (AM.player.sets_owned.length == 0) {
        AM.player.got_sets_owned = false;
        AM.player.retrieve_sets_owned();
    }
    AM.player.got_rating = false;
    AM.player.retrieve_rating();

    // Loop until asynchronous requests are finished.
    // TODO: Do this in a non-blocking way?
    // TODO: Give up eventually
    var intvl = setInterval(function() {
        if (AM.player.got_rating && AM.player.got_sets_owned) {
            console.log('Retrieved player info');
            console.log('Got rating: ' + AM.player.got_rating);
            console.log('Got sets owned: ' + AM.player.got_sets_owned);
            clearTimeout(intvl);
            callback();
        } else {
            console.log('Waiting on player...');
            console.log('Got rating: ' + AM.player.got_rating);
            console.log('Got sets owned: ' + AM.player.got_sets_owned);
        }
    }, 100);
};

AM.create_lightbox = function(lightbox_id) {
    var lb = $('<div id="' + lightbox_id + '">LIGHTBOX</div>');
    //lb.css("text-align", "center");
    lb.css("position", "absolute");
    lb.css("top", "50%");
    lb.css("left", "50%");
    lb.css("height", "300px");
    lb.css("margin-top", "-150px");
    lb.css("width", "40%");
    lb.css("margin-left", "-20%");
    lb.css("background", "white");
    return(lb)
}

// Show automatch seek popup
AM.show_seek_popup = function() {
    console.log('Entering show_seek_popup');

    // Build seek popup if necessary
    if ($("#seekpop").length == 0) {
        console.log('Creating seek popup');
        $("#viewport").append(AM.create_lightbox('seekpop'));

        h = '<h3 style="text-align:center">Request Automatch</h3>\
             <table>\
               <tr>\
                 <td> Players: </td>\
                 <td><select style="width:100%"> \
                       <option value="2">2</option>\
                       <option value="3">3</option>\
                       <option value="4">4</option>\
                       <option value="5">5</option>\
                       <option value="6">6</option>\
                   </select>\
                 </td>\
               </tr>\
               <tr>\
                 <td> Rating +/- </td>\
                 <td> <input type="numeric" id="rrange" size="4" value="1500"/> </td>\
               </tr>\
               <tr>\
                 <td colspan="2" >\
                   <div style="text-align:right">\
                     <input type="checkbox" id="allcards" checked >All Cards?</input>\
                   </div>\
                 </td>\
               </tr>\
               <tr>\
                 <td colspan="2" >\
                   <input type="button" class="automatch" id="seekreq" value="Request" style="width:48%"/>\
                   <input type="button" class="automatch" id="seekcan" value="Cancel" style="width:48%"/>\
                 </td>\
               </tr>\
             </table>';
        $("#seekpop").html(h);

        $('#seekreq').click(function (evt) {
            AM.state.seek = {
                player: AM.player,
                requirements: []         //TODO: populate from seekpop form
            }
            AM.send_message('submit_seek', {seek: AM.state.seek});
            $('#seekpop').hide();
        });

        $('#seekcan').click(function (evt) {
            $('#seekpop').hide();
        });
    }

    console.log('Showing seek popup');
    $("#seekpop").show();
};

// Show automatch offer popup
AM.show_offer_popup = function() {
    console.log('Entering show_offer_popup');

    if ($("#offerpop").length == 0) {
        console.log('Creating offer popup');
        $("#viewport").append(AM.create_lightbox('offerpop'));

        h = '<h3 style="text-align:center">Match Found</h3>\
             <div id="offerinfo">OFFER INFO</div>\
             <div id="offerwaitinfo">OFFER WAIT INFO</div>\
             <input type="button" class="automatch" id="offeracc" value="Accept" />\
             <input type="button" class="automatch" id="offeracccan" value="Cancel" />\
             <input type="button" class="automatch" id="offerdec" value="Decline" />\
            ';
        $('#offerpop').html(h);

        $('#offeracc').click(function (evt) {
            AM.send_message('accept_offer', {matchid: AM.state.offer.matchid});
            AM.state.offer.accepted = true;
        });

        $('#offeracccan').click(function (evt) {
            AM.send_message('reject_offer', {matchid: AM.state.offer.matchid});
            $('#offerpop').hide();
        });

        $('#offerdec').click(function (evt) {
            AM.send_message('reject_offer', {matchid: AM.state.offer.matchid});
            $('#offerpop').hide();
        });
    }

    // Insert offer details
    var vsinfo = AM.state.offer.seeks.map(function(s) {
        return s.player.pname + ' (' + s.player.rating.goko_pro_rating + ')';
    }).join(' vs ');
    $("#offerinfo").html(vsinfo)

    // Show the built and updated popup
    console.log('Showing offer popup');
    $("#offerpop").show();
};

// Transfer the Greasemonkey global namespace variable AM to Goko's global namespace
unsafeWindow.AM = AM

document.addEventListener('DOMContentLoaded', function () {
    console.log('Loading automatch interface');
    console.log('Loading automatch interface');
    console.log('Loading automatch interface');
    console.log('Loading automatch interface');

    // Add Automatch button to the lobby menu.
    var buttonsScript = $('script#fs-mtrm-tpl-classic-room-section')[0];
    buttonsScript.textContent = buttonsScript.textContent.replace(
        "<li><button class='fs-mtrm-text-border fs-mtrm-dominion-btn room-section-btn-create-table'>Create Game</button></li>",
        "<li><button class='fs-mtrm-text-border fs-mtrm-dominion-btn room-section-btn-create-table'>Create Game</button></li>" +
        "<li><button onclick='AM.automatch_button();' class='fs-mtrm-text-border fs-mtrm-dominion-btn'>Automatch</button></li>"
    );
});

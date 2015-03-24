(function () {
    "use strict";

    // Underscore template for displaying an individual game
    var gameTemplate;

    $.vals = function(selector) {
        return _.map($(selector), function (el) {
            return el.value;
        });
    };

    function num_players(nums) {
        if (nums) {
            $('#num-players-format input').prop('checked', false);
            nums.forEach(function (m) {
                $('#num-players-format [value="' +  m + '"]').prop('checked', true);
            });
            $('#num-players-format input').button('refresh');
        } else {
            return $.vals('#num-players-format :checked');
        }
    }

    function rating_modes(modes) {
        if (modes) {
            $('#rating-mode-format input').prop('checked', false);
            modes.forEach(function (m) {
                $('#rating-mode-format [value="' +  m + '"]').prop('checked', true);
            });
            $('#rating-mode-format input').button('refresh');
        } else {
            return $.vals('#rating-mode-format :checked');
        }
    }

    function init_ui() {
        var autocomplete_defaults = {
            addontab: true,
            firstselected: true,
            filter_selected: true,
            filter_begin: true,
            delay: 0,
            cache: true,
            width: 778,
            complete_text: ""
        };
        
        $('[type=checkbox]').change(function() {
            if(!$(this).is(':checked')) {
                $(this).blur();
            }
        });

       $('#players').fcbkcomplete(_.extend({
           json_url: "/logsearch_json?req-type=player-names&count=10",
           maxitems: 6,
           height: 10,
       }, autocomplete_defaults));

       $('#kingdom, #nonkingdom').fcbkcomplete(_.extend({
           json_url: "/logsearch_json?req-type=card-names",
           fetch_only_once: true,
           maxitems: 10,
           height: 3
       }, autocomplete_defaults));

       $('#rating-mode-format').buttonset();
       $('#num-players-format').buttonset();
       $('#search-button').button();

        $("#more-options-div").accordion({
            collapsible: true,
            active: null,
            animate: false
        });
        $("#more-options-div").css("width", $("#search-table").css("width"));

        $("#start-date").datepicker({
            onClose: function( selectedDate ) {
                $( "#end-date" ).datepicker( "option", "min-date", selectedDate );
            }
        });

        $("#end-date").datepicker({
            onClose: function( selectedDate ) {
                $( "#from" ).datepicker( "option", "max-date", selectedDate );
            }
        });

        $(".datepicker").each(function () {
            $(this).datepicker("option", "changeMonth", true);
            $(this).datepicker("option", "showOn", "button");
            $(this).datepicker("option", "buttonImage", "/static/img/calendar.gif");
            $(this).datepicker("option", "buttonImageOnly", true);
        });

        $.ajax('/static/logsearch_gametemplate.html')
            .done(function (resp) {
                gameTemplate = _.template(resp);
            });
    }

    function apply_stored_search_params() {
        var params = localStorage.getItem('default-search-params');
        if (params === null) {
            params = {
                rating_modes: ['pro', 'casual', 'unrated'],
                num_players: ['2', '3', '4', '5', '6']
            };
        }
        rating_modes(params.rating_modes);
        num_players(params.num_players);
    }

    function get_search_params() {
        var params = $('#more-options-form').serializeArray();
        params.push({'name': 'player_ids', 'value': $.vals('#players option')});
        params.push({'name': 'kingdom_cards', 'value': $.vals('#kingdom option')});
        params.push({'name': 'num_players', 'value': num_players()});
        params.push({'name': 'rating_modes', 'value': rating_modes()});
        return params;
    }

    function store_search_params() {
        var params = get_search_params();
        localStorage.setItem('default-search-params', params);
    }

    $(document).ready(function () {
        console.log('TODO: verify database is up to date.');
        console.log('TODO: also search on defunct usernames.');
        console.log('TODO: implement advanced (old) search options.');
        console.log('TODO: add 2-player stats.');
        console.log('TODO: faster search when 2+ players are named.');
        console.log('TODO: ignore accents?');

        init_ui();
        apply_stored_search_params();

        $("#save-params").click(function () {
            console.log('TODO: Implement saving parameters');
        });

        $("#clear").click(function (evt) {
            alert('TODO: clear search fields');
        });

        $("#cancel").click(function (evt) {
            $(this).attr('disabled', true);
            $.getJSON("/logsearch_json?query=cancel-logsearch");
        });

        function cardImageURL(cardName) {
            var okName = cardName.replace(/\w\S*/g, function (s) {
                return s[0].toUpperCase() + s.slice(1);
            });
            okName = okName.replace(/[ '\-]/g, '');
            okName = okName[0].toLowerCase() + okName.slice(1);
            return 'static/img/half-card/' + okName + '.gif';
        }

        function addGame(el) {
            return function (game) {
                game.cardURLs = [game.kingdom.length];
                    for (i = 0; i < game.kingdom.length; i += 1) {
                    game.cardURLs[i] = cardImageURL(game.kingdom[i]);
                }
                var gameHTML = gameTemplate({
                    'g': game,
                    'card_width': 120
                });
                $(el).append(gameHTML);
            };
        }

        function showGames(gameArr, el) {
            console.log(game_arr);
            $(el).empty();
            gameArr.foreach(addGame($(el)));
        }

        $("#search-button").click(function () {

            //$(this).val('Cancel');
            
            // kingdom_cards: $.vals('#kingdom option'),
            // num_players: $.vals('#num-players-format :checked'),
            // rating_modes: $.vals('#rating-mode-format :checked')

            var params = get_search_params();
            console.log(params);

            $.getJSON("/logsearch_json?req-type=submit-logsearch", params)
                .done(function (resp) {
                    console.log('Retrieved game search results.');
                    showGames(resp);
                })

                .always(function (resp) {
                    console.log('Search request response:');
                    console.log(resp);
                });
        });
    });
}());

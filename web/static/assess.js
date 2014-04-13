/*jslint browser:true, nomen:true, devel:true, vars:true */
/*globals angular, Promise, $, _, GDT */

(function () {
    "use strict";
    
    var proRatings = {};
    window.namesToIds = {};
    window.idsToNames = {};
    var names = [];
    var ids = {};
    var showAssessment = function (player_id1, player_id2) {
        var url = '/query/gokoproratingquery?query_type=assess'
                + '&player_id_A=' + player_id1
                + '&player_id_B=' + player_id2;
        GDT.doGet(url).then(function (resp) {
            var r = JSON.parse(resp);
            var p = window.sss.predictions = {};
            p['P1 Wins'] = r.a_win;
            p.Draw = r.a_draw;
            p['P1 Loses'] = r.a_loss;
            window.sss.$digest();
        });
    };

    var showProbabilities = function (player_id1, player_id2, pname1, pname2) {
        console.log(player_id1, player_id2);
        var url = '/query/gokoproratingquery?query_type=probabilities'
                + '&player_id_A=' + player_id1
                + '&player_id_B=' + player_id2
                + '&player_name_A=' + pname1
                + '&player_name_B=' + pname2;
        GDT.doGet(url).then(function (resp) {
            var r = JSON.parse(resp).probs;
            var p = window.sss.probs = {};
            console.log(r);
            window.resp = r;
            p.isotropish = {
                p1win: r.isotropish.p1win,
                draw: r.isotropish.draw,
                p1loss: r.isotropish.p1loss
            };
            p.goko = {
                p1win: r.goko.p1win,
                draw: r.goko.draw,
                p1loss: r.goko.p1loss
            };
            window.sss.$digest();
        });
    };

    var nameChosen = function (event, ui) {
        var pid = window.namesToIds[ui.item.value];
        ids[event.target.id] = pid;

        var sn = {
            p1name: 'p1',
            p2name: 'p2'
        }[event.target.id];

        var url = '/query/gokoproratingquery?query_type=player_rating'
                + '&player_id=' + pid;
        GDT.doGet(url).then(function (resp) {
            var r = JSON.parse(resp);
            var p = window.sss[sn];
            p.mu = Math.round(r.mu);
            p.sigma = Math.round(r.sigma);
            p.displayed = r.displayed;
            window.sss.$digest();

            p.show = true;

        }).then(undefined, function (e) {
            throw e;
        });

        if ($('#p1name').val() && $('#p2name').val()) {
            var x = {};
            x.p1 = window.namesToIds[$('#p1name').val()];
            x.p2 = window.namesToIds[$('#p2name').val()];
            x[sn] = pid;
            var pname1 = window.idsToNames[x.p1];
            var pname2 = window.idsToNames[x.p2];
            showAssessment(x.p1, x.p2);
            showProbabilities(x.p1, x.p2, pname1, pname2);
        }
    };

    $(document).ready(function () {
        $('#p1name').autocomplete({
            source: [],
            minLength: 2,
            autoFocus: true,
            select: nameChosen
        });
        $('#p2name').autocomplete({
            source: [],
            minLength: 2,
            autoFocus: true,
            select: nameChosen
        });

        var url = '/query/gokoproratingquery?query_type=rating_list';
        GDT.doGet(url).then(function (resp) {
            JSON.parse(resp).ratings.map(function (r) {
                var id = r[0];
                var pname = r[1];
                window.namesToIds[pname] = id;
                window.idsToNames[id] = pname;
                names.push(pname);
            });
            $('#p1name').autocomplete('option', 'source', names);
            $('#p2name').autocomplete('option', 'source', names);
        }).then(undefined, function (e) {
            throw e;
        });
    });

    var ratingApp = angular.module('ratingApp', []);
    ratingApp.controller('RatingCtrl', function ($scope) {
        $scope.p1 = {};
        $scope.p2 = {};
        $scope.show_p1_rating = false;
        $scope.show_p2_rating = false;
        $scope.predictions = null;
        window.sss = $scope;
    });
    
}());

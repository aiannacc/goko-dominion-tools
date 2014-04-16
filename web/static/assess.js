/*jslint browser:true, nomen:true, devel:true, vars:true */
/*globals angular, Promise, $, _, GDT, namesToIds */

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

    var showRecord = function (pname1, pname2) {
        var url = '/query/gokoproratingquery?query_type=record'
                + '&player_name_A=' + pname1
                + '&player_name_B=' + pname2;
        GDT.doGet(url).then(function (resp) {
            var r = JSON.parse(resp);
            var total = r.wins + r.draws + r.losses;
            r.winpct = 100 * r.wins / total;
            r.drawpct = 100 * r.draws / total;
            r.losspct = 100 * r.losses / total;
            window.sss.record = r;
            window.sss.$digest();
        });
    };

    var onBothChosen = function (pname1, pname2) {
        console.log(pname1, pname2);
        console.log(namesToIds[pname1], namesToIds[pname2]);
        showAssessment(namesToIds[pname1], namesToIds[pname2]);
        showProbabilities(namesToIds[pname1], namesToIds[pname2], pname1, pname2);
        showRecord(pname1, pname2);
        localStorage.setItem('pname1', pname1);
        localStorage.setItem('pname2', pname2);
    };

    window.refresh = function () {
        onBothChosen($('#p1name').val(), $('#p2name').val());
    };

    var showRating = function (key, pname) {
        var pid = window.namesToIds[pname];
        var url = '/query/gokoproratingquery?query_type=player_rating'
                + '&player_id=' + pid;
        GDT.doGet(url).then(function (resp) {
            var r = JSON.parse(resp);
            var p = window.sss[key];
            p.mu = Math.round(r.mu);
            p.sigma = Math.round(r.sigma);
            p.displayed = r.displayed;
            window.sss.$digest();

            p.show = true;

        }).then(undefined, function (e) {
            throw e;
        });
    };

    var nameChosen = function (event, ui) {
        var pid = window.namesToIds[ui.item.value];
        ids[event.target.id] = pid;

        var sn = {
            p1name: 'p1',
            p2name: 'p2'
        }[event.target.id];

        showRating(sn, ui.item.value);

        if ($('#p1name').val() && $('#p2name').val()) {
            var x = {};
            x.p1 = window.namesToIds[$('#p1name').val()];
            x.p2 = window.namesToIds[$('#p2name').val()];
            x[sn] = pid;
            var pname1 = window.idsToNames[x.p1];
            var pname2 = window.idsToNames[x.p2];
            onBothChosen(pname1, pname2);
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

            var oldpname1 = localStorage.getItem('pname1');
            var oldpname2 = localStorage.getItem('pname2');
            if (typeof oldpname1 !== 'undefined' && oldpname1 !== null
                    && typeof oldpname2 !== 'undefined' && oldpname2 !== null) {
                console.log(oldpname1, oldpname2);
                $('#p1name').val(oldpname1);
                $('#p2name').val(oldpname2);
                showRating('p1', oldpname1);
                showRating('p2', oldpname2);
                onBothChosen(oldpname1, oldpname2);
            }
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

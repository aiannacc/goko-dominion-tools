/*jslint browser:true, nomen:true, devel:true, vars:true */
/*globals angular, Promise, $, _ */

(function () {
    "use strict";

    var reload = function (full, sortkey) {
        console.log(full, sortkey);
    };

    var appendRows = function (rows) {

    };

    var leaderboardApp = angular.module('leaderboardApp', []);
    leaderboardApp.controller('leaderboardController', function ($scope) {
        $scope.rows = [];
        $scope.ago = 'WHENEVER';
        $scope.setRows = function (newRows) {
            $scope.rows = newRows;
            $scope.$digest();
        };
        $scope.appendRows = function (newRows) {
            var i = $scope.rows.length;
            newRows.map(function (r) {
                i += 1;
                $scope.rows.push(r);
                //if (i % 1000 === 0 || (i < 500 && i % 100 === 0)) {
                //    $scope.$digest();
                //}
            });
            $scope.$digest();
        };
        window.lbs = $scope;
    });

    var full = true,
        sortkey = 'level',
        offset = 100,
        count = 20;

    var loadRows = function (full, sortkey, offset, count) {
        return new Promise(function (resolve, reject) {
            var req = new XMLHttpRequest();
            window.req = req;
            var args = '?'
                + 'full=' + full
                + '&sortkey=' + sortkey
                + '&offset=' + offset
                + '&count=' + count;
            req.open('GET', '/query/leaderboard' + args);
            req.onload = function () {
                if (req.status === 200) {
                    resolve(req.response);
                } else {
                    reject(req.statusText);
                }
            };
            req.onerror = reject;
            req.send();
        }).then(function (resp) {
            var rows = JSON.parse(resp).ratings;
            console.info('Appending rows', rows);
            appendRows(rows);
        }).then(undefined, function (e) {
            throw e;
        });
    };
    loadRows(false, 'level', 0, 50);
    loadRows(false, 'level', 0, 100);
    loadRows(false, 'level', 0, 1000);
    loadRows(false, 'level', 0, 10000);
}());

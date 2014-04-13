/*jslint browser:true, nomen:true, devel:true, vars:true */
/*globals angular, Promise, $, _, window */

(function () {
    'use strict';

    window.GDT = (window.GDT || {});
    window.GDT.doGet = function (addr) {
        return new Promise(function (resolve, reject) {
            var req = new XMLHttpRequest();
            window.req = req;
            req.open('GET', addr);
            req.onload = function () {
                if (req.status === 200) {
                    resolve(req.response);
                } else {
                    reject(req.statusText);
                }
            };
            req.onerror = reject;
            req.send();
        });
    };
}());

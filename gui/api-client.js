/*
 * Oracle Knots Control Center — API client bootstrap.
 *
 * The dashboard's HTTP API requires a per-run token (see gui.py). This runs
 * before any other script and wraps window.fetch so every same-origin request
 * carries that token, which keeps the 68-odd existing fetch calls unchanged.
 * Cross-origin requests are passed through untouched so the token never leaves
 * this machine.
 */
(function () {
    'use strict';

    if (window.__oracleFetchWrapped) return;

    var meta = document.querySelector('meta[name="oracle-api-token"]');
    var token = meta ? (meta.getAttribute('content') || '') : '';
    if (!token || token === '__ORACLE_API_TOKEN__') {
        // Served without a token: the page was opened outside the Control
        // Center launcher. Leave fetch alone so the failure is the plain 403
        // from the server rather than a confusing client-side error.
        console.warn('Oracle Knots: no API token in this page; API calls will be refused.');
        return;
    }

    window.ORACLE_API_TOKEN = token;

    var nativeFetch = window.fetch.bind(window);

    function isSameOrigin(url) {
        if (typeof url !== 'string') return true;         // Request object, resolved below
        if (url.indexOf('//') === 0) return false;        // protocol-relative
        if (/^[a-z][a-z0-9+.-]*:/i.test(url)) {           // absolute URL
            return url.indexOf(window.location.origin + '/') === 0 ||
                   url === window.location.origin;
        }
        return true;                                       // relative path
    }

    window.fetch = function (input, init) {
        var url = (typeof input === 'string') ? input : (input && input.url) || '';
        if (!isSameOrigin(url)) return nativeFetch(input, init);

        var opts = {};
        if (init) {
            for (var key in init) {
                if (Object.prototype.hasOwnProperty.call(init, key)) opts[key] = init[key];
            }
        }
        var headers = new Headers(
            (init && init.headers) ||
            (typeof input === 'object' && input && input.headers) ||
            {}
        );
        headers.set('X-Oracle-Token', token);
        opts.headers = headers;
        return nativeFetch(input, opts);
    };

    window.__oracleFetchWrapped = true;
})();

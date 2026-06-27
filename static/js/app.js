/*
 * Brokerly · App JS
 *
 * Bundle minimal: apenas toggles de menu (mobile + collapse).
 * O tema Duralux espera as classes `html.minimenu` e `body.mob-navigation-active`.
 * Bootstrap JS (dropdowns, modais, tabs) vem do vendor/duralux/js/vendors.min.js.
 */
(function () {
    'use strict';

    var html = document.documentElement;
    var body = document.body;

    function toggleMiniMenu() {
        html.classList.toggle('minimenu');
    }

    function openMobileMenu() {
        body.classList.add('mob-navigation-active');
    }

    function closeMobileMenu() {
        body.classList.remove('mob-navigation-active');
    }

    document.addEventListener('DOMContentLoaded', function () {
        var miniMini = document.getElementById('menu-mini-button');
        var miniFull = document.getElementById('menu-full-button');
        if (miniMini) {
            miniMini.addEventListener('click', toggleMiniMenu);
        }
        if (miniFull) {
            miniFull.addEventListener('click', toggleMiniMenu);
        }

        var mobile = document.getElementById('mobile-collapse');
        if (mobile) {
            mobile.addEventListener('click', openMobileMenu);
        }

        document.addEventListener('click', function (event) {
            if (!body.classList.contains('mob-navigation-active')) {
                return;
            }
            var sidebar = document.querySelector('.nxl-navigation');
            var trigger = document.getElementById('mobile-collapse');
            if (!sidebar) {
                return;
            }
            if (sidebar.contains(event.target) || (trigger && trigger.contains(event.target))) {
                return;
            }
            closeMobileMenu();
        });
    });
})();

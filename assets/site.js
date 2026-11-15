// Loaded in the head, so that the page is never painted in the wrong theme first,
// and a first visit that belongs on the Italian home page goes there before anything is shown.
(function () {
    var THEME_KEY = 'pixelcake-site-theme';
    var LANGUAGE_KEY = 'pixelcake-site-language';
    var root = document.documentElement;
    var italian = (root.getAttribute('lang') || '').indexOf('it') === 0;

    function read(key) {
        try {
            return localStorage.getItem(key);
        } catch (error) {
            return null;
        }
    }

    function write(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (error) {
            // The choice lasts for this page only
        }
    }

    // --- The language. The site is in English at the root and in Italian in it/.
    // Only the English home page, the address people are given, moves a visitor:
    // when no language was chosen with the switch, a browser that puts Italian
    // before English goes to the Italian home page. A choice made with the switch
    // is kept in this browser and wins. Nobody is moved while going from one page
    // of the site to another, and the other pages never move anyone.

    function prefersItalian() {
        var list = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ''];
        for (var i = 0; i < list.length; i++) {
            var code = String(list[i]).split(';')[0].trim().toLowerCase();
            if (code === 'it' || code.indexOf('it-') === 0) return true;
            if (code === 'en' || code.indexOf('en-') === 0) return false;
        }
        return false;
    }

    function fromThisSite() {
        try {
            return !!document.referrer && new URL(document.referrer).host === location.host && location.host !== '';
        } catch (error) {
            return false;
        }
    }

    var italianHome = root.getAttribute('data-italian-home');
    if (italianHome) {
        var chosen = read(LANGUAGE_KEY);
        if (chosen === 'it' || (chosen !== 'en' && !fromThisSite() && prefersItalian())) {
            // (a page opened from the disk has no index of a folder)
            var page = italianHome + (location.protocol === 'file:' ? 'index.html' : '');
            location.replace(page + location.hash);
            return;
        }
    }

    // --- Light or dark. The page follows the computer until the visitor
    // chooses; the choice is kept in this browser.

    var WORDS = italian
        ? { light: 'Chiaro', dark: 'Scuro', toLight: 'Passa al tema chiaro', toDark: 'Passa al tema scuro' }
        : { light: 'Light', dark: 'Dark', toLight: 'Switch to the light theme', toDark: 'Switch to the dark theme' };

    function savedTheme() {
        var value = read(THEME_KEY);
        return value === 'light' || value === 'dark' ? value : null;
    }

    function current() {
        return (
            root.getAttribute('data-theme') ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
        );
    }

    var choice = savedTheme();
    if (choice) root.setAttribute('data-theme', choice);
    root.classList.add('js');

    function themeButton() {
        var button = document.querySelector('.theme-toggle');
        if (!button) return;

        // The button names the theme it leads to
        function label() {
            var dark = current() === 'dark';
            button.textContent = dark ? WORDS.light : WORDS.dark;
            button.setAttribute('aria-label', dark ? WORDS.toLight : WORDS.toDark);
        }

        button.addEventListener('click', function () {
            var next = current() === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            write(THEME_KEY, next);
            label();
        });

        label();
    }

    // --- The switch between the two languages (in the masthead and in the
    // footer): a link to the same page in the other language. The language
    // chosen with it is kept, next to the theme.

    function languageSwitch() {
        var links = document.querySelectorAll('.lang a[hreflang]');
        Array.prototype.forEach.call(links, function (link) {
            link.addEventListener('click', function () {
                write(LANGUAGE_KEY, link.getAttribute('hreflang'));
            });
        });
    }

    // --- The drawings. Each tells a short story in a loop: it starts from the
    // beginning when the drawing comes into view and waits while it is out of
    // sight. For who asked for less motion it stands still, on the frame that
    // says the most (data-still, in seconds).

    function drawings() {
        var all = Array.prototype.slice.call(document.querySelectorAll('svg.iso'));
        all = all.filter(function (svg) {
            return typeof svg.pauseAnimations === 'function';
        });
        if (!all.length) return;

        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            all.forEach(function (svg) {
                svg.pauseAnimations();
                svg.setCurrentTime(parseFloat(svg.getAttribute('data-still')) || 0);
            });
            return;
        }
        if (!('IntersectionObserver' in window)) return;

        var watch = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    var svg = entry.target;
                    if (entry.isIntersecting) {
                        svg.setCurrentTime(0);
                        svg.unpauseAnimations();
                    } else {
                        svg.pauseAnimations();
                    }
                });
            },
            { threshold: 0.3 }
        );
        all.forEach(function (svg) {
            svg.pauseAnimations();
            watch.observe(svg);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        themeButton();
        languageSwitch();
        drawings();
    });
})();

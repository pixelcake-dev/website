// Loaded in the head, so that the page is never painted in the wrong theme first.
(function () {
    var KEY = 'pixelcake-site-theme';
    var root = document.documentElement;

    // --- Light or dark. The page follows the computer until the visitor
    // chooses; the choice is kept in this browser.

    function saved() {
        try {
            var value = localStorage.getItem(KEY);
            return value === 'light' || value === 'dark' ? value : null;
        } catch (error) {
            return null;
        }
    }

    function current() {
        return (
            root.getAttribute('data-theme') ||
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
        );
    }

    var choice = saved();
    if (choice) root.setAttribute('data-theme', choice);
    root.classList.add('js');

    function themeButton() {
        var button = document.querySelector('.theme-toggle');
        if (!button) return;

        // The button names the theme it leads to
        function label() {
            var next = current() === 'dark' ? 'Light' : 'Dark';
            button.textContent = next;
            button.setAttribute('aria-label', 'Switch to the ' + next.toLowerCase() + ' theme');
        }

        button.addEventListener('click', function () {
            var next = current() === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            try {
                localStorage.setItem(KEY, next);
            } catch (error) {
                // The choice lasts for this page only
            }
            label();
        });

        label();
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
        drawings();
    });
})();

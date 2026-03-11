/* Drag-to-scroll for touchscreen kiosk mode.
   Uses capture phase to intercept mouse events before Grafana's
   React components can consume them. */
(function() {
    var poll = setInterval(function() {
        var views = document.querySelectorAll(".scrollbar-view");
        var scrollEl = null;
        for (var i = 0; i < views.length; i++) {
            if (views[i].scrollHeight > views[i].clientHeight + 100) {
                scrollEl = views[i];
                break;
            }
        }
        if (!scrollEl) return;
        clearInterval(poll);

        var startY = 0, startScroll = 0, dragging = false;

        document.addEventListener("mousedown", function(e) {
            dragging = true;
            startY = e.clientY;
            startScroll = scrollEl.scrollTop;
            e.stopPropagation();
            e.preventDefault();
        }, true);

        document.addEventListener("mousemove", function(e) {
            if (!dragging) return;
            scrollEl.scrollTop = startScroll + (startY - e.clientY);
            e.stopPropagation();
            e.preventDefault();
        }, true);

        document.addEventListener("mouseup", function() {
            dragging = false;
        }, true);
    }, 500);
})();

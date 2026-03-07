(function() {
    var sv = document.querySelectorAll(".scrollbar-view");
    var scrollEl = null;
    for (var i = 0; i < sv.length; i++) {
        if (sv[i].scrollHeight > 1000) { scrollEl = sv[i]; break; }
    }
    if (!scrollEl) return "no scroll element";

    var startY, startScroll, dragging = false;
    scrollEl.addEventListener("mousedown", function(e) {
        dragging = true;
        startY = e.clientY;
        startScroll = scrollEl.scrollTop;
    });
    document.addEventListener("mousemove", function(e) {
        if (!dragging) return;
        scrollEl.scrollTop = startScroll + (startY - e.clientY);
        e.preventDefault();
    });
    document.addEventListener("mouseup", function() {
        dragging = false;
    });
    return "OK scrollH=" + scrollEl.scrollHeight;
})()

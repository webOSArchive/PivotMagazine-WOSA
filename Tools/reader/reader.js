// Pivot Magazine web reader. Hosts the App Catalog's own Magazine engine in a
// page: picks portrait or landscape to suit the window, scales the fixed-size
// TouchPad pages to fit, and adds the page controls a touch device didn't
// need. ES5 only -- this has to run in the webOS 2.x/3.x browsers too.
//
//   read.html?issue=2011&lang=en&page=4
(function () {
    // The area the App Catalog gave the magazine on a TouchPad: the screen
    // minus the catalog's own header bar. The page artwork is cut to exactly
    // these sizes; the layouts declare the full screen and rely on clipping.
    var PORTRAIT = [768, 947], LANDSCAPE = [1024, 691];
    var MUSEUM = 'https://appcatalog.webosarchive.org/';

    function param(name, fallback) {
        var m = new RegExp('[?&]' + name + '=([^&#]*)').exec(window.location.search);
        return m ? decodeURIComponent(m[1].replace(/\+/g, ' ')) : fallback;
    }
    // Issue and language name folders, so keep them to folder-name characters.
    function folderName(s, fallback) {
        return /^[A-Za-z0-9_-]+$/.test(s || '') ? s : fallback;
    }

    var issue = folderName(param('issue', ''), '');
    var lang = folderName(param('lang', 'en'), 'en');
    var startPage = parseInt(param('page', '0'), 10) || 0;
    var issueBase = window.location.pathname.replace(/[^\/]*$/, '') +
                    'issues/' + issue + '/' + lang;

    var magazine = null;
    var numPages = 0;
    var forced = null;                         // null = follow the window
    var landscape = false;

    // Read by stubs-post.js.
    window.PivotReader = {
        isLandscape: function () { return landscape; },
        openApp: function (appId) {
            if (appId) window.open(MUSEUM + 'showMuseumDetails.php?appid=' + encodeURIComponent(appId));
        },
        fail: function () {
            document.body.className += ' failed';
        }
    };

    if (!issue) {
        window.location.replace('./');
        return;
    }

    // Must be set before Magazine.create() runs inside renderInto().
    AppCatalog.Config.draftEditionDir = issueBase;
    // document.write is still legal here: we run while the head is parsing.
    document.write('<link rel="stylesheet" href="' + issueBase + '/common/css/magazine.css">');
    document.write('<link rel="stylesheet" href="' + issueBase + '/common/css/page.css">');

    function $(id) { return document.getElementById(id); }

    function currentPage() { return magazine ? magazine.currentPageNum : startPage; }

    function updatePageInfo() {
        var p = currentPage();
        $('page-info').innerHTML = numPages ? (p + 1) + ' / ' + numPages : '';
        $('btn-prev').disabled = p <= 0;
        $('btn-next').disabled = !numPages || p >= numPages - 1;
        // Keep the address bar pointing at this page, so it can be shared.
        if (window.history && history.replaceState) {
            try {
                history.replaceState(null, '', '?issue=' + issue + '&lang=' + lang + '&page=' + p);
            } catch (e) {}
        }
    }

    // The engine lays pages out in fixed pixels and sizes its carousel from
    // the DOM, so the viewport keeps the device dimensions and is scaled
    // with a transform.
    function fit(size, availW, availH) {
        return Math.min(availW / size[0], availH / size[1]);
    }
    function layout() {
        var stage = $('stage');
        var availW = stage.clientWidth, availH = stage.clientHeight;
        var wantLandscape = forced !== null ? forced :
            fit(LANDSCAPE, availW, availH) > fit(PORTRAIT, availW, availH);

        var size = wantLandscape ? LANDSCAPE : PORTRAIT;
        var w = size[0], h = size[1];
        var scale = fit(size, availW, availH);

        var vp = $('viewport'), frame = $('frame');
        vp.style.width = w + 'px';
        vp.style.height = h + 'px';
        var t = 'scale(' + scale + ')';
        vp.style.webkitTransform = t;
        vp.style.transform = t;
        frame.style.width = Math.floor(w * scale) + 'px';
        frame.style.height = Math.floor(h * scale) + 'px';
        frame.style.marginTop = Math.max(0, Math.floor((availH - h * scale) / 2)) + 'px';

        var changed = wantLandscape !== landscape;
        landscape = wantLandscape;
        if (magazine) {
            // VFlexBox children don't stretch to fill their parent, so size the
            // magazine root and its carousel explicitly; otherwise the carousel
            // measures itself short and pages render undersized.
            var nodes = [magazine.hasNode(), magazine.$.magazineContainer.hasNode()];
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i]) {
                    nodes[i].style.width = w + 'px';
                    nodes[i].style.height = h + 'px';
                }
            }
            if (changed) magazine.update();
        }
    }

    function go(page) {
        if (!magazine || page < 0 || page >= numPages || page === currentPage()) return;
        var car = magazine.$.magazineContainer;
        // Neighbouring pages get the carousel's own slide; anything further
        // away is a jump, which is how the engine handles TOC links too.
        if (page === currentPage() + 1) car.next();
        else if (page === currentPage() - 1) car.previous();
        else magazine.setInternetTargetPage(page);
    }

    function wireMagazine() {
        var M = magazine;
        // Every way the page can change -- swipe, buttons, TOC links -- ends up
        // in one of these three.
        var after = function (fn) {
            return function () {
                var r = fn.apply(this, arguments);
                setTimeout(updatePageInfo, 0);
                return r;
            };
        };
        M.handleNextPage = after(M.handleNextPage);
        M.handlePrevPage = after(M.handlePrevPage);
        M.setInternetTargetPage = after(M.setInternetTargetPage);

        var loaded = M.drafEditionFilesetLoaded;
        M.drafEditionFilesetLoaded = function () {
            loaded.apply(this, arguments);
            numPages = this.currentEdition.numPages;
            updatePageInfo();
            // Not synchronously: each new page queues an async Pane view switch,
            // and jumping now destroys page 0 before that switch runs, which
            // throws inside Enyo.
            var self = this;
            if (startPage > 0 && startPage < numPages) {
                setTimeout(function () { self.setInternetTargetPage(startPage); }, 100);
            }
        };

        // Targets outside the magazine meant other App Catalog screens. The
        // App Museum is the nearest thing on the web.
        M.doMagazineGoToTarget = function (target, params) {
            if (target === 'appdetails' && params && params.publicApplicationId) {
                PivotReader.openApp(params.publicApplicationId);
            } else if (target === 'searchlist') {
                window.open(MUSEUM);
            }
        };
    }

    function loadTitle() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'issues.json', true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4 || xhr.status !== 200) return;
            try {
                var issues = JSON.parse(xhr.responseText).issues || [];
                for (var i = 0; i < issues.length; i++) {
                    if (issues[i].id === issue) {
                        $('issue-title').innerHTML = '';
                        $('issue-title').appendChild(document.createTextNode(issues[i].title));
                        document.title = issues[i].title + ' – Pivot Magazine';
                    }
                }
            } catch (e) {}
        };
        xhr.send(null);
    }

    window.addEventListener('DOMContentLoaded', function () {
        $('btn-prev').onclick = function () { go(currentPage() - 1); };
        $('btn-next').onclick = function () { go(currentPage() + 1); };
        $('btn-rotate').onclick = function () { forced = !landscape; layout(); };
        document.addEventListener('keydown', function (e) {
            var k = e.keyCode;
            if (k === 37 || k === 33) { go(currentPage() - 1); e.preventDefault(); }
            else if (k === 39 || k === 34 || k === 32) { go(currentPage() + 1); e.preventDefault(); }
            else if (k === 36) { go(0); e.preventDefault(); }
            else if (k === 35) { go(numPages - 1); e.preventDefault(); }
        }, false);
        window.addEventListener('resize', layout, false);

        layout();
        magazine = new enyo.FindApps.Magazine.Magazine({});
        wireMagazine();
        magazine.renderInto($('viewport'));
        layout();
        updatePageInfo();
        loadTitle();
    }, false);
})();

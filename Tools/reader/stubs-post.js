// Stubs loaded AFTER the app's build.js. Patches kinds and globals so the
// Magazine renders standalone in a web page without the catalog or luna
// services. Adapted from Tools/preview/stubs-post.js; ES5 only.

// Without localStorage (private browsing, blocked site data) the stock
// version returns null and Magazine.create() throws on .toUpperCase().
findApps.UserSession.getActivationCountry = function() { return 'US'; };

// Give ViewLibrary a container stub so MagazinePageCarousel.sizeControls
// doesn't throw when checking isTopView.
findApps.ViewLibrary._container = {
    isTopView: function() { return true; },
    setView: function() {},
    popViewsFromHistory: function() {},
    goBack: function() {}
};

// editionsMgrHelper.getEdition() fires a luna PalmService call to schedule
// a background edition download. Not applicable on the web.
enyo.FindApps.Magazine.EditionsMgrHelper.prototype.getEdition = function() {};

// Stub enyo.application singletons that catalog buttons reference.
enyo.application = enyo.application || {};
enyo.application.savedList = {
    attach: function() {},
    detach: function() {},
    isSaved: function() { return false; },
    saveApp: function() {},
    removeApp: function() {},
    getList: function() { return []; },
    contains: function() { return false; }
};
enyo.application.appdownloadManager = {
    attach: function() {},
    detach: function() {},
    myAppsListIsReady: function() { return false; },
    belongToMyApp: function() { return null; },
    getAppDownload: function() { return null; }
};
enyo.application.sessionManager = {
    triggerInitSession: function() { return { status: 'complete' }; }
};
enyo.application.connectionManager = {
    isConnected: function() { return true; },
    monitor: function() {}
};

// A browser can't install anything, so the featured-app download button
// becomes a link to that app's page in the webOS App Museum.
enyo.kind({
    name: 'findApps.downloadsavebutton',
    kind: enyo.Control,
    published: { appItem: {} },
    className: 'reader-app-button',
    create: function() {
        this.inherited(arguments);
        this.appItemChanged();
    },
    appItemChanged: function() {
        var id = this.appItem && this.appItem.appId;
        this.setShowing(!!id);
        this.setContent('View in App Museum');
    },
    clickHandler: function() {
        PivotReader.openApp(this.appItem && this.appItem.appId);
        return true;
    },
    setButton: function() {},
    disableMe: function() {},
    updateFromServer: function() {}
});

// AppInfoService fetches live ratings and prices from the HP-era catalog
// server, which no longer exists. Return nothing; the cards render without.
enyo.FindApps.Magazine.AppInfoService.prototype.getAppList = function() {
    this._returnResponse([]);
};

// MagazinePage.generateLayout() passes window.innerWidth/innerHeight, which
// says nothing about the orientation the reader has chosen for the scaled
// stage. Ask the reader instead.
enyo.FindApps.Magazine.MagazinePage.prototype.orientationChanged = function() {
    if (this.hasCustomLandscapeLayout) {
        this.landscapeMode = PivotReader.isLandscape();
    }
    this._selectOrientView();
};

// The stock loader goes through enyo.WebService, whose XHR chain depends on
// the webOS runtime. A plain XHR (not fetch, for old webOS browsers) works
// everywhere.
enyo.FindApps.Magazine.Magazine.prototype.loadDraftEdition = function() {
    var self = this;
    var xhr = new XMLHttpRequest();
    xhr.open('GET', AppCatalog.Config.draftEditionDir + '/manifest.json', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return;
        var data = null;
        if (xhr.status === 200 || (xhr.status === 0 && xhr.responseText)) {
            try { data = JSON.parse(xhr.responseText); } catch (e) {}
        }
        if (data) {
            self.drafEditionFilesetLoaded(null, data);
        } else {
            self.drafEditionFilesetNotLoaded(null, null);
            PivotReader.fail();
        }
    };
    xhr.send(null);
};

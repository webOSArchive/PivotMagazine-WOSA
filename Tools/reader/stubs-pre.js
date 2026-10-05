// Stubs loaded BEFORE enyo-build.js, UserSession.js, and the app's build.js.
// Adapted from Tools/preview/stubs-pre.js for the public web reader: paths
// are relative to wherever the reader is published, and nothing here may use
// syntax newer than ES5 -- webOS 2.x/3.x browsers read this site too.

// enyo-build.js is the compiled Enyo framework. It extends an existing `enyo`
// object rather than creating it -- that bootstrapping is normally done by
// enyo.js. We replicate the minimum here so enyo-build.js can parse cleanly.
window.enyo = window.enyo || {};
enyo.args = {};
// enyoPath is read at parse time by the dependency-loader section of
// enyo-build.js. Absolute, derived from this page's own URL, so the reader
// works at /pivot/magazine/ in production and at / on a local build.
enyo.enyoPath = window.location.pathname.replace(/[^\/]*$/, '') + 'lib/enyo';

// Deliberately no window.PalmSystem stub (Tools/preview has one). Its mere
// presence switches Enyo into device mode: taps are routed through
// PalmSystem.simulateMouseClick, which a browser doesn't have, so every link
// on a page silently stops working. The App Catalog code never reads it.

// build.js calls $L("...") at parse time for UI strings.
window.$L = function(s) { return s; };

// palmGetResource is a webOS native for loading package resources.
window.palmGetResource = function() { return null; };

// PalmServiceBridge is the native luna IPC bridge. Stub it so PalmService
// and DbService can be instantiated without crashing (calls are silently dropped).
window.PalmServiceBridge = function() {
    this.onservicecallback = null;
    this.call = function() {};
    this.cancel = function() {};
};

// UserSession.getActivationCountry() reads this key directly. Guarded:
// localStorage throws in some private-browsing modes.
try {
    localStorage.setItem('com.palm.app.findapps.country', 'US');
} catch (e) {}

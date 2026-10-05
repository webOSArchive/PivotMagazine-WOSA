#!/bin/sh
#
# Pull, build, publish the Pivot Magazine web reader to
# www.webosarchive.org/pivot/magazine/. Safe to run from cron as often as you
# like: it does nothing unless one of its sources has moved.
#
#   /home/wosa/pivot-admin/magazine-src     this repo, outside the docroot
#   /home/wosa/pivot-admin/appcatalog-src   webos-appcatalog-touchpad (the engine)
#   /home/wosa/pivot-admin/enyo-src         enyojs/enyo-1.0 (the framework)
#   /home/wosa/pivot-admin/lunacy-src       Lunacy, only LunaRuntimes/enyo-1.0:
#                                           its Enyo patches for modern browsers
#   /home/wosa/wosa-web/pivot-magazine      what nginx serves -- build output only
#
# Deliberately NOT inside /home/wosa/wosa-web/pivot: the blog's deploy.sh
# rsyncs into that directory with --delete and would erase the magazine.
#
# Pass --force to rebuild and republish regardless.
#
# Mirrors pivotce.com's deploy.sh; the comments there explain the fetch
# refspec and the self-update re-exec in more detail.
#
set -eu

SELF=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")

BASE=/home/wosa/pivot-admin
SRC=$BASE/magazine-src
APP=$BASE/appcatalog-src
ENYO=$BASE/enyo-src
LUNACY=$BASE/lunacy-src
PATCHES=LunaRuntimes/enyo-1.0
BUILD=$BASE/magazine-build
DOCROOT=/home/wosa/wosa-web/pivot-magazine

# Records the source versions actually published. Untracked, beside the clone.
STAMP=$SRC/.last-deployed

# Shallow mirror of one branch: clone if missing, otherwise force it to match
# origin. The leading "+" is required on a --depth 1 clone, where every new
# tip looks like a non-fast-forward. Not --quiet, so a rejection still shows.
#
# With a fourth argument, only that path is checked out (and only its blobs
# fetched): Lunacy is a large, busy repo and all this needs is its patches.
sync_repo() {   # dir url branch [sparse-path]
    if [ ! -d "$1/.git" ]; then
        if [ -n "${4:-}" ]; then
            git clone --no-progress --depth 1 --branch "$3" --filter=blob:none --sparse "$2" "$1"
            git -C "$1" sparse-checkout set "$4"
        else
            git clone --no-progress --depth 1 --branch "$3" "$2" "$1"
        fi
    else
        git -C "$1" fetch --no-progress --depth 1 origin "+$3:refs/remotes/origin/$3"
        git -C "$1" reset --hard --quiet "origin/$3"
    fi
}

# This repo carries this script, and /bin/sh reads scripts incrementally, so
# restart if the reset changed us underneath ourselves.
before=$(cksum < "$SELF")
sync_repo "$SRC" https://github.com/webOSArchive/PivotMagazine-WOSA main
if [ "$before" != "$(cksum < "$SELF")" ]; then
    echo "magazine deploy: deploy-web.sh was updated, restarting with the new version"
    exec "$SELF" --force
fi
sync_repo "$APP" https://github.com/webOSArchive/webos-appcatalog-touchpad main
sync_repo "$ENYO" https://github.com/enyojs/enyo-1.0 master
sync_repo "$LUNACY" https://github.com/webOSArchive/Lunacy main "$PATCHES"

# Lunacy is versioned by the tree of the patches folder, not by its HEAD:
# Lunacy commits constantly, and almost never to these patches.
target="$(git -C "$SRC" rev-parse HEAD) $(git -C "$APP" rev-parse HEAD) $(git -C "$ENYO" rev-parse HEAD) $(git -C "$LUNACY" rev-parse "HEAD:$PATCHES")"
if [ "${1:-}" != "--force" ] \
   && [ -f "$STAMP" ] && [ "$(cat "$STAMP")" = "$target" ] \
   && [ -f "$DOCROOT/index.html" ]; then
    exit 0                      # already published; the normal case on most runs
fi

# build-web.py validates every published issue, and fails if a Lunacy patch no
# longer applies, rather than produce a partial site -- so a bad commit in any
# of the four leaves the live reader untouched.
python3 "$SRC/Tools/build-web.py" \
    --app "$APP" --enyo "$ENYO" --enyo-patches "$LUNACY/$PATCHES/patches" \
    --out "$BUILD" >/dev/null

mkdir -p "$DOCROOT"
rsync -a --delete --exclude .pivot-web-build "$BUILD/" "$DOCROOT/"
printf '%s\n' "$target" > "$STAMP"
count=$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["issues"]))' "$DOCROOT/issues.json")
echo "magazine deploy: published $count issue(s) to $DOCROOT"

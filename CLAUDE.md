# CLAUDE.md — PivotMagazine-WOSA

## What this repo is

Authoring source for "Pivot Magazine," the featured-content edition shown in the [webOS Archive App Catalog](https://github.com/webOSArchive/webos-appcatalog-touchpad) (`com.palm.app.enyo-findapps`, repo `webos-appcatalog-touchpad`, sibling directory to this one).

**This is not a submodule or build-time dependency of the app anymore.** The app ships a tiny placeholder edition baked directly into its own repo (`webos-appcatalog-touchpad/main/source/magazine/defaultEdition/{lang}/`) and, at runtime, hydrates the real edition over HTTPS from `https://appcatalog.webosarchive.org/pivot/{lang}/` into on-device storage (`/media/internal/.pivot`). See `main/source/pivot-hydration.js` in the app repo for the client-side half of this. This repo is purely where a real edition's content is authored and staged before publishing to that URL — see "Publishing an issue" below for the actual end-to-end flow.

`Issues/Current/` is the edition currently published live. `Issues/2011/` is the original HP-era content, kept untouched for historical reference — never edit it.

---

## Issue folder structure

Every issue folder (e.g. `Issues/Current/`) has the same layout:

```
{issue}/
├── manifest.json               ← root/legacy manifest (no lang code, 1-page, unused by the app)
├── common/                     ← lang-agnostic shared assets
│   ├── css/                    ← magazine.css, page.css
│   └── images/                 ← light-bg.png etc.
└── {lang}/                     ← one folder per locale: en, de, es, fr, it
    ├── manifest.json           ← THE manifest the app actually uses
    ├── gen-manifest.sh         ← legacy Linux-only manifest generator (superseded, see below)
    ├── common/
    │   ├── apps/               ← one subfolder per featured app
    │   │   └── {appname}/
    │   │       └── info.json
    │   ├── layouts/            ← shared Enyo component templates (.lo.js)
    │   │   ├── app.lo.js           ← renders a single app card
    │   │   ├── portraitHeader.lo.js
    │   │   ├── landscapeHeader.lo.js
    │   │   └── header.json         ← bindings for the header templates
    │   ├── css/                ← magazine.css, page.css
    │   └── images/             ← shared UI images (arrows, gradients)
    └── page{N}/                ← one folder per page, 0-indexed, must be a CONTIGUOUS
                                   range (0..numPages-1) -- the app's carousel navigates
                                   by pageNum+1/-1, and a gap breaks forward navigation
                                   past it (see "Trimming or reorganizing pages" below)
        ├── bindings.json       ← template variable values for this page
        ├── portrait.lo.js      ← Enyo component tree, portrait layout
        ├── landscape.lo.js     ← Enyo component tree, landscape layout
        └── images/
            ├── portrait-bg.jpg
            └── landscape-bg.jpg
```

`Issues/Current/en` is presently a shortened 10-page edition (page0–page9): a cover, masthead, two TOC pages, four content pages, one featured-app grid, and one closing/teaser page. It was trimmed down from the original HP-era 32-page structure to keep the on-device hydration download small — see git history (`shorten current magazine`) if you need the reasoning. `de`/`es`/`fr`/`it` currently ship only a single `page0`. None of this is a structural limit — a future issue can be any page count; `numPages` and the manifest are derived automatically from whatever `page*` folders actually exist (see "Regenerating the manifest").

---

## File formats

### `bindings.json`

Plain JSON. Defines template variable values for a page. All `{$varName}` tokens in the `.lo.js` files for that page are substituted with the corresponding value before the layout is evaluated.

```json
{
    "portraitBgImage": "page4/images/portrait-bg.jpg",
    "landscapeBgImage": "page4/images/landscape-bg.jpg",
    "appTemplate": "common/layouts/app.lo.js",
    "app1BindingsPortrait": "common/apps/kindle/info.json",
    ...
}
```

All paths in `bindings.json` are **relative to the language folder** (e.g. `en/`), and **relative to the page's own current folder name** for that page's own background images (`page4/images/...` inside `page4/bindings.json`) — if you rename or renumber a page folder, its own `bindings.json` self-references need updating to match, not just the folder move itself.

### `.lo.js` layout files

A JavaScript array literal containing an Enyo 0.x component tree. **Not valid JSON** — keys may be unquoted, and the file is `eval()`'d by the magazine engine after template substitution.

```javascript
[
    {kind: "VFlexBox", className: "portrait",
     style: "background-image: url({$portraitBgImage}); height:1024px; width:768px;",
     components: [
        {kind: "enyo.FindApps.Magazine.BindableLayout",
         templatePath: "{$portraitHeaderTemplate}",
         bindingPath: "{$headerTemplateBindings}"},
        {kind: "enyo.FindApps.Magazine.BindableLayout",
         className: "index-app1",
         templatePath: "{$appTemplate}",
         bindingPath: "{$app1BindingsPortrait}"},
        ...
    ]}
]
```

`{$varName}` tokens are replaced by values from `bindings.json` before eval. Paths in `templatePath` and `bindingPath` are also relative to the language folder.

### `common/apps/{appname}/info.json`

Identifies an app to feature. `_app_id` is the webOS app ID. The remaining fields are placeholders — the magazine engine fetches live values (rating, price, review count) from the App Catalog service at render time.

```json
{
    "_app_id": "com.palm.app.kindle",
    "rating": "{$_app_rating}",
    "reviewCount": "{$_app_reviewCount}",
    "price": "{$_app_price}"
}
```

To feature a new app: create a new subfolder under `common/apps/` with an `info.json` using the app's webOS package ID.

### `manifest.json`

Tells the magazine engine which files exist in this edition. The engine reads this first, then fetches individual files on demand.

```json
{
    "publishDate": "06/01/2011 12:00:00",
    "numPages": 10,
    "packageSize": 4045872,
    "results": [
        {
            "logicalPath": "page4/images/landscape-bg.jpg",
            "checksum": "d5b7de79af584941a8ef0595c5b0c443",
            "section": "page4",
            "type": "image",
            "edition": 1,
            "physicalPath": "source/magazine/defaultEdition/en/page4/images/landscape-bg.jpg",
            "size": 179380
        },
        ...
    ]
}
```

**Critical fields:**
- `logicalPath` — path relative to the language folder (e.g. `en/`)
- `physicalPath` — for a *bundled* placeholder edition, path relative to the app package root, always starting `source/magazine/defaultEdition/{lang}/`. For a *hydrated* edition (this repo's normal output via `gen-device-manifest.py`), this instead gets rewritten to the on-device cache path `/media/internal/.pivot/{lang}/...` — see "Publishing an issue" below. Either way, getting this wrong silently breaks page loading.
- `checksum` — MD5 hex digest of the file
- `type` — one of `image`, `layout`, `binding`, `css`
- `section` — the page or `common` prefix (first path component of `logicalPath`)
- `numPages` — total page count; must match the actual number of page folders
- `packageSize` — sum of all file sizes in bytes

**The manifest must be regenerated any time files are added, removed, or changed** — see below.

---

## Regenerating the manifest

Each language folder's old `gen-manifest.sh` was HP's original Linux-only toolchain (`md5sum`/`stat -c%s`) — don't use it. Use `Tools/gen-manifest.py` instead (works on macOS and Linux, auto-counts `page*` folders for `numPages`, preserves the existing `publishDate`):

```bash
# From the PivotMagazine-WOSA repo root:
python3 Tools/gen-manifest.py --issue Issues/Current --lang en
```

Run this any time you add, remove, rename, or edit a file under a language folder — including a pure rename/renumber with no content change, since `logicalPath`/`physicalPath`/`section` are all derived from the current folder name.

---

## Page types

Pages aren't interchangeable — they use different layout templates and binding keys depending on role:

| Role | Key bindings |
|------|-------------|
| Splash / cover | Just background images |
| Masthead / about | Header template, email, version |
| Table of contents | `targetHinge`, `targetSphereN`, `targetHub`, `targetOrientN`, `targetFeatureN`, `targetShutter`, `targetIndex`, `targetTeaser` — each navigates to another page **by folder name** (e.g. `"page4"`) when tapped |
| Featured app grid | `appNBindingsPortrait/Landscape` pointing to `common/apps/*/info.json`; navigation link fragments |
| Content/editorial | Background images + header template |

The `target` / `runtimeParams` mechanism on clickable elements navigates to another page or launches a search list. `target: "searchlist"` with a `queryFragment` opens the app list filtered by that query.

### Trimming or reorganizing pages

If you remove or renumber pages (as was done to shorten `Issues/Current`), two things beyond the manifest need attention or you'll ship dead links or silently-wrong navigation:

1. **Every TOC binding target must point to a page that still exists in the trimmed range.** A target string like `"page19"` that no longer has a matching `page19/` folder doesn't error — `Magazine.getView()` just returns `null` for an out-of-range index, so the tap silently does nothing. Worse, if the target number happens to coincidentally match a *different, renumbered* page (e.g. an old target of `"page8"` surviving after page8's content changed), it'll navigate somewhere plausible-looking but wrong, which is easy to miss in testing.
2. **For a target with no remaining valid destination**, don't leave it pointing at a dead page number — clear the binding value to `""` and add `" hidden"` to that element's `className` in both `portrait.lo.js` and `landscape.lo.js` (there's already a `toc-sphere8 hidden` precedent in the original HP layout for exactly this). This is a *content* fix, not a code fix — no app changes needed.
3. Page folders must stay a **contiguous 0-indexed range**. The carousel navigates by `currentPageNum ± 1`; a gap (e.g. page0–page7 then page30–page31 with nothing in between) breaks forward navigation at the gap even if every individual page's own content is fine. Renumber, don't just delete-and-leave-gaps.

---

## Publishing an issue

This is the full path from edited content in this repo to it actually being live on real devices — there are two more steps beyond just running the generator, and skipping either one is a real trap (both have bitten this exact repo before):

```bash
# 1. From this repo's root: regenerate the source manifest for anything you changed.
python3 Tools/gen-manifest.py --issue Issues/Current --lang en

# 2. Derive + stage the publish artifacts into the catalog-service checkout.
#    --version MUST be higher than whatever's currently live (checked in
#    catalog-service/pivot/{lang}/version.json) -- the app compares
#    magazineVersion strictly and treats "not higher" as "nothing to do,"
#    with no override. Forgetting to bump it means devices silently never
#    pick up the republish, no matter how many times you push.
python3 Tools/gen-device-manifest.py --lang en --version 3 \
    --out /path/to/catalog-service/pivot

# 3. gen-device-manifest.py only COPIES/OVERWRITES files it knows about --
#    it never deletes. If you removed or renamed any page folders since the
#    last publish (see "Trimming or reorganizing pages"), their old files
#    are still sitting in catalog-service/pivot/{lang}/ under their old
#    names and WILL get published alongside the new content unless you
#    remove them yourself first. Diff the two page* folder listings before
#    committing:
diff <(ls Issues/Current/en | grep '^page') \
     <(ls /path/to/catalog-service/pivot/en | grep '^page')
#    Anything only on the right (catalog-service) side is stale -- rm -rf it
#    from the catalog-service checkout before committing.

# 4. Commit + push catalog-service, same as any other change to that repo.
#    Nothing is actually live until this is pushed AND the server has run
#    its own `git pull` -- pushing to GitHub alone does not deploy it.
```

Repeat per language for any locale you changed — each has its own independent `version.json`, so publishing `en` doesn't touch `de`/`es`/`fr`/`it`'s versions and vice versa.

**Adding a new locale** (not just editing an existing one) needs one more piece outside this repo: `webos-appcatalog-touchpad/main/source/pivot-hydration.js`'s `SUPPORTED_LANGS` array only lists `de/en/es/fr/it` — a device set to any other locale silently falls back to `en` regardless of what's published here. You'd also need a placeholder `page0` for that locale under `main/source/magazine/defaultEdition/{lang}/` in the app repo (bundled edition, shown before hydration completes) — that's app-repo work, not something this repo alone can ship.

## Creating a new issue from scratch

```bash
python3 Tools/new-issue.py 2026-Summer        # scaffolds Issues/2026-Summer/ from Issues/Current
# ... edit content in Issues/2026-Summer/en/ ...
python3 Tools/gen-manifest.py --issue Issues/2026-Summer --lang en
python3 Tools/preview/serve.py                # preview locally, see Tools/README.md
```

When ready to ship, either point `gen-device-manifest.py --issue Issues/2026-Summer` directly at the new folder for publishing, or replace `Issues/Current`'s contents with the finished issue first (keeping `Issues/Current` as the one canonical "what's live" folder) — either works, `gen-device-manifest.py`'s `--issue` flag defaults to `Issues/Current` but accepts any issue folder.

---

## Relationship to the app repo

- App repo: `webos-appcatalog-touchpad` (sibling directory to this repo — both live under the same parent, e.g. `~/Projects/AppCatalogIntegration/`).
- The magazine **engine** (Enyo kinds: `Magazine`, `MagazinePage`, `BindableLayout`, etc.) lives in `webos-appcatalog-touchpad/main/source/magazine/app/` (source-restored, not just compiled) and is compiled into that repo's `main/build.js`. Do not look for it here.
- The **hydration glue** — checking for a new version, downloading a published edition into `/media/internal/.pivot`, and swapping the placeholder for the hydrated cache once it's ready — is `webos-appcatalog-touchpad/main/source/pivot-hydration.js`. That file is what actually fetches everything this repo publishes.
- The magazine **content** (pages, images, bindings) lives here in `Issues/`.
- `webos-appcatalog-touchpad/main/source/magazine/defaultEdition/{lang}/` is **not** empty — it holds a tiny bundled placeholder edition (single page, "fetching your first issue" message + spinner + progress bar) shown until hydration finishes. It is a real, separately-maintained mini-edition in the app repo, not generated from this repo's content.

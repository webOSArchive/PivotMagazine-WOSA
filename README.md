# PivotMagazine-WOSA

The "Pivot Magazine" featured-content edition for the [webOS Archive App Catalog](https://github.com/webOSArchive/webos-appcatalog). This repo holds the magazine **content** (page layouts, app data, background images, manifests) independently of the app itself.

## How it fits together

The webOS App Catalog (`com.palm.app.enyo-findapps`, repo `webos-appcatalog-touchpad`) ships a tiny placeholder edition baked directly into its own repo — this content is **no longer a submodule or build-time dependency of the app repo**. Instead, the app hydrates the real edition at runtime from `https://appcatalog.webosarchive.org/pivot/{lang}/`, caching it on-device at `/media/internal/.pivot`. This repo is purely the **authoring source** for what gets published to that URL.

```
PivotMagazine-WOSA/
└── Issues/
    ├── Current/        ← published to appcatalog.webosarchive.org/pivot/{lang}/
    │   ├── en/         ← English edition (10 pages, shortened from the original 32 -- see CLAUDE.md)
    │   ├── de/         ← German (page 0 only)
    │   ├── es/fr/it/   ← Other locales (page 0 only)
    │   └── common/     ← lang-agnostic CSS and images
    └── 2011/           ← archived original HP issue (reference / history -- never edit)
```

## Publishing an issue

From this repo's root, for each language:

```bash
python3 Tools/gen-manifest.py --issue Issues/Current --lang en   # regenerate {lang}/manifest.json first
python3 Tools/gen-device-manifest.py --lang en --version 2 \
    --out /path/to/catalog-service/pivot         # derive + stage the publish artifacts
```

`gen-device-manifest.py` copies the raw asset tree into a version-namespaced `pivot/{lang}/v{N}/` URL (never a flat, reused-across-versions path — confirmed on-device that reusing the URL let Cloudflare's static-file cache serve a stale earlier version even after the origin had new content) and writes `version.json`, `manifest.device.json` (the app's download plan), and `manifest.local.json` (what the app writes to disk as its cached `manifest.json`) at the stable top-level `pivot/{lang}/` path, ready to deploy the same way as that repo's other static files. **Bump `--version` every time you republish** — the app compares it against what's cached on-device to decide whether to re-hydrate, and treats "not higher" as nothing to do. Then commit + push `catalog-service` — nothing is live until the server's own `git pull` picks it up. Full step-by-step is in `CLAUDE.md`.

## Creating a new issue

1. Duplicate `Issues/Current` to a new named folder (e.g. `Issues/2025`).
2. Edit page content — see `CLAUDE.md` for format details.
3. Add any new app entries to `{lang}/common/apps/`.
4. Regenerate `{lang}/manifest.json` using the tooling in `Tools/`.
5. When ready to ship: copy or symlink the new issue folder to `Issues/Current`, then publish per the steps above with a bumped `--version`.

## Tools

`Tools/` contains helpers for working with issue content. See `Tools/README.md` (or `CLAUDE.md`) for usage.

# Tools

Cross-platform helpers for working with Pivot Magazine issues. See the repo's `CLAUDE.md` for full format documentation.

---

## `preview/` — Live browser preview

Renders the magazine in a desktop browser using the real Enyo 0.x engine from the app's `build.js`. Requires the `webos-appcatalog-touchpad` app repo to be checked out as a sibling directory to this one (`serve.py` walks up three levels from its own location to find the shared parent, so the parent directory's own name doesn't matter).

**Start the preview:**

```bash
# From the shared parent directory of both repos:
python3 PivotMagazine-WOSA/Tools/preview/serve.py
```

Opens `http://localhost:8080/PivotMagazine-WOSA/Tools/preview/` automatically.

**URL parameters:**

| Param | Default | Description |
|-------|---------|-------------|
| `issue` | `Current` | Issue folder name under `Issues/` |
| `lang` | `en` | Language subfolder |
| `page` | `0` | Starting page number |

Example: `http://localhost:8080/PivotMagazine-WOSA/Tools/preview/?issue=Current&lang=en&page=5`

To preview a new issue, create it first with `new-issue.py` (see below), then use `?issue=YourIssueName`.

**Toolbar controls:** Prev/Next page · Portrait/Landscape toggle · Issue + Lang inputs with Reload button.

**How it works:** The server serves the `webos-appcatalog/` root so both repos are reachable. The preview sets `AppCatalog.Config.draftEditionDir` to the issue URL, which tells the magazine engine to load `manifest.json` and derive all asset URLs from that base — no path remapping needed. WebOS-specific services (Luna, DB, activity manager) are stubbed out. The featured-app download buttons are replaced with passive placeholders since HP-era app IDs no longer exist.

**First-time setup:** `vendor/enyo-build.js` and `vendor/enyo-build.css` are copied from the Palm SDK and are gitignored. If they go missing, re-run:

```bash
cp /opt/PalmSDK/Current/share/framework/enyo/1.0/framework/build/enyo-build.{js,css} \
   Tools/preview/vendor/
```

Other Palm SDK assets (Onyx theme images, g11n data) are served automatically by `serve.py` directly from `/opt/PalmSDK/Current/` — no copying needed.

---

## `gen-manifest.py` — Manifest regenerator

Regenerates `{lang}/manifest.json` after any files are added, removed, or changed. Replaces the Linux-only `gen-manifest.sh` found in each locale folder. Works on macOS and Linux.

```bash
# From the PivotMagazine-WOSA repo root:
python3 Tools/gen-manifest.py

# Specify issue and language:
python3 Tools/gen-manifest.py --issue Issues/Current --lang en

# Override page count (default: auto-count page* folders):
python3 Tools/gen-manifest.py --issue Issues/2026-Summer --lang en --num-pages 28
```

Computes MD5 checksums, file sizes, and `physicalPath` values (`source/magazine/defaultEdition/{lang}/…`) for every file in the language folder, then writes `manifest.json` in-place. Preserves the existing `publishDate` if the manifest already exists.

**Run this every time you add, remove, or replace a file in a language folder.**

---

## `gen-device-manifest.py` — Publish to catalog-service

Derives the on-device hydration artifacts for one language from its already-regenerated `manifest.json` (run `gen-manifest.py` first), and stages the raw asset copy alongside them into a `catalog-service` checkout.

```bash
# From the PivotMagazine-WOSA repo root:
python3 Tools/gen-device-manifest.py --lang en --version 3 \
    --out /path/to/catalog-service/pivot
```

Writes into `{out}/{lang}/`:
- a copy of every asset file, under a version-namespaced `v{N}/` subdirectory (mirrors `{issue}/{lang}/` minus tooling files) — never a flat, reused-across-versions path. Confirmed on-device 2026-08-21: with a flat path, Cloudflare's static-file cache (4h `max-age` on `.js`/image extensions — `.json` stays uncached) kept serving an earlier version's cached response for some files even after the origin had new content, so a device could redownload into the correct on-device directory and still land some stale bytes. Versioning the URL makes that impossible, and as a side effect nothing is ever overwritten in place, so there's no stale-file cleanup step needed anymore even after removing or renaming pages.
- `version.json` — `{"magazineVersion": N}`, at the stable top-level path (not versioned — this is what the client checks without already knowing the current version)
- `manifest.device.json` — the hydrator's download plan (`sourceUrl`/`targetFilename` per asset)
- `manifest.local.json` — the same shape as the app's own manifest, but with every `physicalPath` rewritten to the on-device cache path; this is what gets downloaded last and written to disk as the device's `manifest.json`

**One thing this tool does NOT do for you: it doesn't enforce `--version` being higher than what's already published.** The app compares `magazineVersion` strictly and treats "not higher" as "nothing to do" — forgetting to bump it means every device that already has the old edition cached will never see the republish, with no error anywhere to indicate why.

After running this, commit + push the `catalog-service` checkout — nothing is live until that repo's own deploy step (`git pull` on the server) runs too. See the top-level `CLAUDE.md`'s "Publishing an issue" section for the full sequence with exact commands.

---

## `new-issue.py` — Issue scaffolder

Creates a new issue folder by copying `Issues/Current` as a starting point.

```bash
# From the PivotMagazine-WOSA repo root:
python3 Tools/new-issue.py 2026-Summer
```

Copies `Issues/Current/` → `Issues/2026-Summer/`, updates `publishDate` to today in all `manifest.json` files, and prints next-step instructions.

After editing content, regenerate the manifest:

```bash
python3 Tools/gen-manifest.py --issue Issues/2026-Summer --lang en
```

Then preview:

```bash
python3 Tools/preview/serve.py
# open: http://localhost:8080/PivotMagazine-WOSA/Tools/preview/?issue=2026-Summer&lang=en
```

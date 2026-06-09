# Tools

Cross-platform helpers for working with Pivot Magazine issues. See the repo's `CLAUDE.md` for full format documentation.

## Planned tools

### `gen-manifest.py`

Regenerates `manifest.json` for a language edition. Replaces the Linux-only `gen-manifest.sh` found in each locale folder.

```
Usage: python3 gen-manifest.py <issue-dir> <lang> --numPages <N>
Example: python3 gen-manifest.py ../Issues/Current en --numPages 32
```

Should:
- Walk `<issue-dir>/<lang>/`, find all `.js`, `.json`, `.jpg`, `.png`, `.gif`, `.css` files
- Skip `manifest.json` itself
- Compute MD5 checksum, file size, type, section, logicalPath, physicalPath for each
- Set `physicalPath` to `source/magazine/defaultEdition/<lang>/<logicalPath>`
- Write `<issue-dir>/<lang>/manifest.json` in-place

### `new-issue.sh` (or `.py`)

Scaffolds a new issue by copying `Issues/Current` to `Issues/<name>`, ready for editing.

### `add-app.py`

Creates a `common/apps/<appname>/info.json` entry for a new featured app given its webOS app ID.

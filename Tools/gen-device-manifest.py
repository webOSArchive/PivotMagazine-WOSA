#!/usr/bin/env python3
"""
Generate the on-device hydration artifacts for a magazine issue language folder,
and stage the raw asset tree alongside them for static publishing.

Reads the existing {issue}/{lang}/manifest.json (see gen-manifest.py) and derives,
under {out}/{lang}/:
  - a copy of every asset file (mirrors {issue}/{lang}/ minus tooling files)
  - version.json           {"magazineVersion": N}
  - manifest.device.json   the hydrator's download plan (sourceUrl/targetFilename per asset)
  - manifest.local.json    the same shape as the app's own manifest.json, but with every
                            physicalPath rewritten to the on-device cache path; this is what
                            gets downloaded last and written to disk as "manifest.json"

Nothing here is new authoring -- every field is mechanically derived from the existing
manifest.json plus a version number and a base URL.

Usage (from the PivotMagazine-WOSA repo root):
    python3 Tools/gen-device-manifest.py --lang en --version 1 \
        --base-url https://appcatalog.webosarchive.org/pivot \
        --out /path/to/catalog-service/pivot
"""
import argparse
import json
import pathlib
import shutil
import sys

REPO_ROOT = pathlib.Path(__file__).parent.parent.resolve()
DEVICE_CACHE_ROOT = '/media/internal/.pivot'


def flatten(logical_path: str) -> str:
    return logical_path.replace('/', '__')


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--issue', default='Issues/Current',
                   help='Path to the issue folder relative to repo root (default: Issues/Current)')
    p.add_argument('--lang', required=True, help='Language code subfolder (e.g. en)')
    p.add_argument('--version', type=int, required=True,
                   help='magazineVersion to stamp into version.json / manifest.device.json / manifest.local.json')
    p.add_argument('--base-url', default='https://appcatalog.webosarchive.org/pivot',
                   help='Public base URL the raw asset tree is published under (default: %(default)s)')
    p.add_argument('--out', required=True,
                   help='Output directory to stage the publish tree into (e.g. a checkout of catalog-service, '
                        'pointed at its pivot/ subdirectory)')
    args = p.parse_args()

    lang_dir = REPO_ROOT / args.issue / args.lang
    manifest_path = lang_dir / 'manifest.json'
    if not manifest_path.is_file():
        print(f'Error: {manifest_path} not found -- run gen-manifest.py first', file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())

    out_lang_dir = pathlib.Path(args.out) / args.lang
    out_lang_dir.mkdir(parents=True, exist_ok=True)

    device_assets = []
    local_results = []

    for entry in manifest['results']:
        logical = entry['logicalPath']
        target_filename = flatten(logical)

        src_file = lang_dir / logical
        dst_file = out_lang_dir / logical
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)

        source_url = f"{args.base_url}/{args.lang}/{logical}"

        device_assets.append({
            'sourceUrl': source_url,
            'targetFilename': target_filename,
            'logicalPath': logical,
            'type': entry['type'],
            'section': entry['section'],
            'size': entry['size'],
        })

        local_results.append({
            'logicalPath': logical,
            'checksum': entry['checksum'],
            'section': entry['section'],
            'type': entry['type'],
            'edition': entry['edition'],
            'physicalPath': f"{DEVICE_CACHE_ROOT}/{args.lang}/{target_filename}",
            'size': entry['size'],
        })

    version_json = {'magazineVersion': args.version}
    (out_lang_dir / 'version.json').write_text(json.dumps(version_json, indent=4) + '\n', encoding='utf-8')

    manifest_device = {
        'lang': args.lang,
        'magazineVersion': args.version,
        'assets': device_assets,
        'self': {
            'sourceUrl': f"{args.base_url}/{args.lang}/manifest.local.json",
            'targetFilename': 'manifest.json',
        },
    }
    (out_lang_dir / 'manifest.device.json').write_text(
        json.dumps(manifest_device, indent=4) + '\n', encoding='utf-8')

    manifest_local = {
        'publishDate': manifest['publishDate'],
        'magazineVersion': args.version,
        'numPages': manifest['numPages'],
        'packageSize': manifest['packageSize'],
        'results': local_results,
    }
    (out_lang_dir / 'manifest.local.json').write_text(
        json.dumps(manifest_local, indent=4) + '\n', encoding='utf-8')

    print(f'Staged {len(device_assets)} assets + version.json/manifest.device.json/manifest.local.json '
          f'into {out_lang_dir.relative_to(pathlib.Path.cwd()) if out_lang_dir.is_relative_to(pathlib.Path.cwd()) else out_lang_dir}')


if __name__ == '__main__':
    main()

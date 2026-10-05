#!/usr/bin/env python3
"""
Scaffold a new magazine issue by copying Issues/Current.

Usage (from the PivotMagazine-WOSA repo root):
    python3 Tools/new-issue.py <name>

Creates Issues/<name>/ as a copy of Issues/Current/ and sets publishDate
in all manifest.json files to today's date, and writes the issue.json that
the web reader (build-web.py) lists issues by. After editing content, run
gen-manifest.py to regenerate accurate checksums and file sizes.
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).parent.parent.resolve()
CURRENT = REPO_ROOT / 'Issues' / 'Current'


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('name', help='Name for the new issue folder (e.g. 2026-Summer)')
    args = p.parse_args()

    dest = REPO_ROOT / 'Issues' / args.name

    if dest.exists():
        print(f'Error: {dest} already exists', file=sys.stderr)
        sys.exit(1)

    if not CURRENT.exists():
        print(f'Error: {CURRENT} not found', file=sys.stderr)
        sys.exit(1)

    print(f'Copying {CURRENT.relative_to(REPO_ROOT)} → Issues/{args.name} ...')
    shutil.copytree(CURRENT, dest)

    today = datetime.now().strftime('%m/%d/%Y 12:00:00')
    updated = 0
    for manifest in dest.rglob('manifest.json'):
        try:
            data = json.loads(manifest.read_text())
            data['publishDate'] = today
            manifest.write_text(json.dumps(data, indent=4) + '\n', encoding='utf-8')
            updated += 1
        except (json.JSONDecodeError, KeyError):
            pass

    print(f'Updated publishDate to {today} in {updated} manifest.json file(s).')

    # Web reader metadata (Tools/build-web.py). "draft" keeps the issue off
    # the web, so pushing work in progress publishes nothing; delete the line
    # when the issue is ready.
    issue_meta = {
        'title': f'Pivot: {args.name}',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'description': '',
        'languages': ['en'],
        'draft': True,
    }
    (dest / 'issue.json').write_text(json.dumps(issue_meta, indent=4) + '\n', encoding='utf-8')
    print(f'Wrote Issues/{args.name}/issue.json as a draft (not on the web until "draft" is removed).')
    print()
    print(f'Next steps:')
    print(f'  1. Edit content in Issues/{args.name}/en/  (pages, images, bindings)')
    print(f'  2. Regenerate manifest:')
    print(f'     python3 Tools/gen-manifest.py --issue Issues/{args.name} --lang en')
    print(f'  3. Preview:')
    print(f'     python3 Tools/preview/serve.py')
    print(f'     Open: http://localhost:8080/PivotMagazine-WOSA/Tools/preview/?issue={args.name}&lang=en')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Build the Pivot Magazine web reader: a static site that renders issues in a
browser with the App Catalog's own Magazine engine.

Usage (from the PivotMagazine-WOSA repo root):
    python3 Tools/build-web.py --app ../webos-appcatalog-touchpad \\
        --enyo ../enyo-1.0 --enyo-patches ../Lunacy/LunaRuntimes/enyo-1.0/patches \\
        --out build/web

--enyo is a checkout of enyojs/enyo-1.0 (master), and --enyo-patches the
patch series Lunacy maintains against it for modern browsers -- chiefly the
FlexLayout fixes, which every magazine page depends on. The patches are
applied in order to a copy, as Lunacy's own fetch-assets.sh does, and one
that no longer applies fails the build rather than being skipped.

An issue is published to the web only if its folder has an issue.json:

    {
        "title": "Pivot 02: The Something Issue",
        "date": "2026-11-01",
        "description": "One or two sentences for the issue list.",
        "languages": ["en"]
    }

`languages` defaults to ["en"]. `"draft": true` (which new-issue.py writes)
keeps an issue off the web until it is removed. Issues/Current never needs an
issue.json: it is a moving pointer, and a web link to it would change under
its readers.

Output:
    index.html        list of issues, newest first (plain HTML, no script)
    read.html         the reader: read.html?issue=<folder>&lang=<lang>&page=<n>
    issues.json       the same list, for the reader and anything else
    latest.html       redirects to the newest issue
    cover.jpg         the newest issue's cover
    reader/           reader scripts and styles (Tools/reader)
    lib/enyo/         Enyo 1.0 framework build, with Lunacy's patches
    lib/findapps/     the App Catalog's build.js + UserSession.js
    issues/<id>/      cover.jpg and one folder per published language
"""
import argparse
import html
import json
import pathlib
import re
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date

REPO_ROOT = pathlib.Path(__file__).parent.parent.resolve()
ISSUES = REPO_ROOT / 'Issues'
READER = REPO_ROOT / 'Tools' / 'reader'
MARKER = '.pivot-web-build'
FOLDER = re.compile(r'^[A-Za-z0-9_-]+$')
# HP's Linux-only tooling sits in every language folder; none of it is content.
SKIP = shutil.ignore_patterns('gen-*.sh', '.DS_Store')


def fail(msg):
    print(f'build-web: {msg}', file=sys.stderr)
    sys.exit(1)


def load_issue(folder):
    meta_file = folder / 'issue.json'
    try:
        meta = json.loads(meta_file.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        fail(f'{meta_file}: {e}')
    if meta.get('draft'):
        return {'id': folder.name, 'draft': True}     # unfinished; not validated
    if not FOLDER.match(folder.name):
        fail(f'{folder.name}: issue folder names must be letters, digits, - or _')
    for key in ('title', 'date'):
        if not meta.get(key):
            fail(f'{meta_file}: "{key}" is required')
    try:
        date.fromisoformat(meta['date'])
    except ValueError:
        fail(f'{meta_file}: "date" must be YYYY-MM-DD, got {meta["date"]!r}')

    langs = meta.get('languages') or ['en']
    pages = {}
    for lang in langs:
        manifest = folder / lang / 'manifest.json'
        if not FOLDER.match(lang) or not manifest.is_file():
            fail(f'{meta_file}: language {lang!r} has no {manifest.relative_to(REPO_ROOT)}')
        pages[lang] = json.loads(manifest.read_text(encoding='utf-8'))['numPages']

    cover = folder / langs[0] / 'page0' / 'images' / 'portrait-bg.jpg'
    if not cover.is_file():
        fail(f'{folder.name}: no cover at {cover.relative_to(REPO_ROOT)}')

    return {
        'id': folder.name,
        'title': meta['title'],
        'date': meta['date'],
        'description': meta.get('description', ''),
        'languages': langs,
        'pages': pages[langs[0]],
        'cover': f'issues/{folder.name}/cover.jpg',
        'url': f'read.html?issue={folder.name}&lang={langs[0]}',
        'draft': False,
        '_cover_src': cover,
    }


def prepare_out(out):
    """Start from an empty directory, but never empty one we didn't build."""
    if out.exists():
        if any(out.iterdir()) and not (out / MARKER).exists():
            fail(f'{out} is not empty and is not a previous build; refusing to clear it')
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text('Built by PivotMagazine-WOSA/Tools/build-web.py\n')


def long_date(iso):
    d = date.fromisoformat(iso)
    return f'{d.strftime("%B")} {d.day}, {d.year}'


def render_index(issues):
    cards = []
    for i in issues:
        e = {k: html.escape(str(v)) for k, v in i.items() if not k.startswith('_')}
        desc = f'<p class="desc">{e["description"]}</p>' if i['description'] else ''
        cards.append(f'''
    <li class="issue">
      <a href="{e["url"]}"><img src="{e["cover"]}" alt="Cover of {e["title"]}" width="384" height="474"></a>
      <h2><a href="{e["url"]}">{e["title"]}</a></h2>
      <p class="meta">{html.escape(long_date(i["date"]))} &middot; {e["pages"]} pages</p>
      {desc}
    </li>''')
    return INDEX_TEMPLATE.replace('{{issues}}', ''.join(cards))


INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pivot Magazine</title>
<meta name="description" content="Pivot, the magazine built into the webOS App Catalog on the HP TouchPad, and its new issues from webOS Archive.">
<style>
  html, body { margin: 0; background: #141414; color: #ddd;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }
  a { color: #9cc4ff; }
  header, main, footer { max-width: 960px; margin: 0 auto; padding: 0 16px; }
  header { padding-top: 32px; }
  h1 { margin: 0 0 8px; font-size: 40px; letter-spacing: -0.5px; color: #fff; }
  header p { margin: 0 0 8px; max-width: 640px; line-height: 1.5; color: #aaa; }
  ul { list-style: none; margin: 24px 0; padding: 0; }
  .issue { display: inline-block; vertical-align: top; width: 280px; margin: 0 24px 32px 0; }
  .issue img { display: block; width: 100%; height: auto; border: 0;
    -webkit-box-shadow: 0 4px 24px rgba(0,0,0,.7); box-shadow: 0 4px 24px rgba(0,0,0,.7); }
  .issue h2 { margin: 14px 0 4px; font-size: 19px; }
  .issue h2 a { color: #fff; text-decoration: none; }
  .issue h2 a:hover { text-decoration: underline; }
  .meta { margin: 0; font-size: 13px; color: #888; }
  .desc { margin: 8px 0 0; font-size: 14px; line-height: 1.45; color: #bbb; }
  footer { padding-bottom: 32px; font-size: 13px; color: #777; }
  @media (max-width: 640px) {
    h1 { font-size: 30px; }
    .issue { display: block; width: auto; max-width: 400px; margin-right: 0; }
  }
</style>
</head>
<body>
<header>
  <h1>Pivot Magazine</h1>
  <p>Pivot was the magazine inside the App Catalog on the HP TouchPad. HP published one
  issue before webOS hardware was discontinued; webOS Archive is publishing new ones.
  Tap or click the right or left side of a page to turn it (or swipe, or use the arrow
  keys), and switch between portrait and landscape with the Rotate button.</p>
  <p><a href="../">&larr; Back to pivotCE</a></p>
</header>
<main>
  <ul>{{issues}}
  </ul>
</main>
<footer>
  Pages are drawn by the App Catalog's own magazine engine. On a TouchPad running the
  <a href="https://appcatalog.webosarchive.org/">webOS Archive App Catalog</a>, the
  current issue is also in the app.
</footer>
</body>
</html>
'''

LATEST_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pivot Magazine</title>
<meta http-equiv="refresh" content="0; url={url}">
<link rel="canonical" href="{url}">
</head>
<body><p><a href="{url}">Read the latest issue of Pivot Magazine</a></p></body>
</html>
'''


def patched_enyo_build(enyo, patches, dest):
    """Copy enyo/framework, apply each patch in order, keep only build/.

    The patches touch framework/source/ as well as the built file, so they
    are applied to the whole framework and the source then dropped: the
    reader loads only enyo-build.js."""
    series = sorted(patches.glob('*.patch'))
    if not series:
        fail(f'no *.patch files in {patches}')
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(enyo / 'framework', pathlib.Path(tmp) / 'framework')
        # Stop git from finding a repository above the temp dir: inside one,
        # `git apply` takes paths relative to that repo's root instead.
        env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(pathlib.Path(tmp).parent))
        for patch in series:
            r = subprocess.run(['git', 'apply', str(patch)], cwd=tmp, env=env,
                               capture_output=True, text=True)
            if r.returncode != 0:
                fail(f'{patch.name} does not apply to {enyo}:\n{r.stderr.strip()}')
        shutil.copytree(pathlib.Path(tmp) / 'framework' / 'build', dest, ignore=SKIP)
    return [p.name for p in series]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--app', required=True, type=pathlib.Path,
                   help='checkout of webOSArchive/webos-appcatalog-touchpad')
    p.add_argument('--enyo', required=True, type=pathlib.Path,
                   help='checkout of enyojs/enyo-1.0')
    p.add_argument('--enyo-patches', required=True, type=pathlib.Path,
                   help="Lunacy's Enyo patch series (Lunacy/LunaRuntimes/enyo-1.0/patches)")
    p.add_argument('--out', required=True, type=pathlib.Path, help='output directory')
    args = p.parse_args()

    app_build = args.app / 'main' / 'build.js'
    user_session = args.app / 'UserSession.js'
    for f in (app_build, user_session, args.enyo / 'framework' / 'build' / 'enyo-build.js'):
        if not f.is_file():
            fail(f'missing {f}')

    issues = [load_issue(d) for d in sorted(ISSUES.iterdir())
              if d.is_dir() and (d / 'issue.json').exists()]
    drafts = [i['id'] for i in issues if i['draft']]
    issues = [i for i in issues if not i['draft']]
    if not issues:
        fail('no Issues/*/issue.json found; nothing to publish')
    issues.sort(key=lambda i: (i['date'], i['id']), reverse=True)

    out = args.out.resolve()
    prepare_out(out)

    applied = patched_enyo_build(args.enyo, args.enyo_patches, out / 'lib' / 'enyo')
    (out / 'lib' / 'findapps').mkdir(parents=True)
    shutil.copy2(app_build, out / 'lib' / 'findapps' / 'build.js')
    shutil.copy2(user_session, out / 'lib' / 'findapps' / 'UserSession.js')

    shutil.copytree(READER, out / 'reader', ignore=shutil.ignore_patterns('read.html', '.DS_Store'))
    shutil.copy2(READER / 'read.html', out / 'read.html')

    for i in issues:
        dest = out / 'issues' / i['id']
        for lang in i['languages']:
            shutil.copytree(ISSUES / i['id'] / lang, dest / lang, ignore=SKIP)
        shutil.copy2(i['_cover_src'], dest / 'cover.jpg')

    public = [{k: v for k, v in i.items() if not k.startswith('_') and k != 'draft'} for i in issues]
    (out / 'issues.json').write_text(json.dumps({'issues': public}, indent=2) + '\n', encoding='utf-8')
    (out / 'index.html').write_text(render_index(issues), encoding='utf-8')
    (out / 'latest.html').write_text(LATEST_TEMPLATE.format(url=html.escape(issues[0]['url'])),
                                     encoding='utf-8')
    shutil.copy2(issues[0]['_cover_src'], out / 'cover.jpg')

    print(f'build-web: {len(issues)} issue(s) -> {out}')
    print(f'  enyo: applied {", ".join(applied)}')
    for d in drafts:
        print(f'  {d:<16} skipped: draft')
    for i in issues:
        print(f'  {i["id"]:<16} {i["date"]}  {i["pages"]:>3} pages  {",".join(i["languages"])}  {i["title"]}')


if __name__ == '__main__':
    main()

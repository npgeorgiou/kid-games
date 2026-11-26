"""Krita preset (.kpp) reader: a .kpp is a PNG whose 'preset' text chunk holds the brush settings as XML.

  python3 kpp.py <preset.kpp>... --out <dir>
writes <dir>/<name>.txt (one setting per line: name = value, sensor curves on one line)
and copies every brush tip / pattern the preset names from the bundle folder (--bundle) into <dir>/../tips, ../patterns.
"""
import argparse, base64, os, re, shutil, html
from PIL import Image

def settings(path):
    xml = Image.open(path).info['preset']
    engine = re.search(r'paintopid="([^"]+)"', xml).group(1)
    rows = []
    for name, val in re.findall(r'<param[^>]*name="([^"]+)"[^>]*>(.*?)</param>', xml, re.S):
        val = re.sub(r'^<!\[CDATA\[(.*)\]\]>$', r'\1', val.strip(), flags=re.S)
        val = re.sub(r'\s+', ' ', html.unescape(val)).strip()
        rows.append((name, val))
    return engine, rows

def save_embedded_pattern(rows, folder):
    """Krita embeds the texture pattern in the preset as base64 of the base64 PNG: write the PNG under its own name."""
    d = dict(rows)
    data, name = d.get('Texture/Pattern/Pattern'), d.get('Texture/Pattern/Name')
    if not data or not name: return None
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, name), 'wb') as f: f.write(base64.b64decode(base64.b64decode(data)))
    return name

def named_files(rows):
    files = set()
    for _, v in rows:
        files.update(re.findall(r'filename="([^"]+)"', v))
    for n, v in rows:
        if n.endswith('PatternFileName') and v: files.add(v)
    return files

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('kpp', nargs='+'); ap.add_argument('--out', required=True); ap.add_argument('--bundle', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    missing = set()
    for p in a.kpp:
        engine, rows = settings(p)
        name = os.path.basename(p)[:-4]
        embedded = save_embedded_pattern(rows, os.path.join(a.out, '..', 'patterns'))
        with open(os.path.join(a.out, name + '.txt'), 'w') as f:
            f.write('engine = %s\n' % engine)
            f.writelines('%s = %s\n' % (n, '<embedded: patterns/%s>' % embedded if n == 'Texture/Pattern/Pattern' else v) for n, v in rows)
        for fn in named_files(rows):
            base = os.path.basename(fn)
            if embedded and base in (embedded, embedded + '.pat'): continue
            for sub in ('brushes', 'patterns'):
                src = os.path.join(a.bundle, sub, base)
                if os.path.exists(src):
                    dst = os.path.join(a.out, '..', 'tips' if sub == 'brushes' else 'patterns')
                    os.makedirs(dst, exist_ok=True); shutil.copy(src, dst); break
            else: missing.add(base)
    print('presets', len(a.kpp), 'missing files', sorted(missing))

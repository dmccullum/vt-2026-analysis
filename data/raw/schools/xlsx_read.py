"""Minimal stdlib-only XLSX reader (no formulas evaluated; uses cached values). Never executes file content."""
import zipfile, re
import xml.etree.ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def _col(ref):
    s = re.match(r'[A-Z]+', ref).group(0)
    n = 0
    for ch in s:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path):
    """Return {sheetname: [[cell,...],...]}"""
    z = zipfile.ZipFile(path)
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rmap = {r.get('Id'): r.get('Target') for r in rels}
    out = {}
    for sh in wb.find('m:sheets', NS):
        rid = sh.get('{%s}id' % NS['r'])
        tgt = rmap[rid].lstrip('/')
        if not tgt.startswith('xl/'):
            tgt = 'xl/' + tgt
        root = ET.fromstring(z.read(tgt))
        rows = []
        for row in root.iter('{%s}row' % NS['m']):
            vals = {}
            for c in row.findall('m:c', NS):
                t = c.get('t')
                v = c.find('m:v', NS)
                if t == 's' and v is not None:
                    val = ss[int(v.text)]
                elif t == 'inlineStr':
                    val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
                elif v is not None:
                    val = v.text
                else:
                    val = None
                vals[_col(c.get('r'))] = val
            if vals:
                m = max(vals) + 1
                rows.append([vals.get(i) for i in range(m)])
            else:
                rows.append([])
        out[sh.get('name')] = rows
    return out

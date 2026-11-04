"""Assign each school in AOE F.17 (lat/long) to a Census county subdivision (town) via TIGERweb point query.
Usage: python3 -I geocode_schools.py   (run from the schools folder)"""
import sys, json, csv, time, urllib.request, urllib.parse
sys.path.insert(0, '.')
from xlsx_read import read_xlsx
rows = read_xlsx('aoe_redistricting_data/F.17.-Public-School-Locations-and-Grades---School-Level.xlsx')['Sheet1']
hdr = rows[0]
out = []
URL = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/1/query?'
for r in rows[1:]:
    d = dict(zip(hdr, r))
    if not d.get('ORG_ID'): continue
    lon, lat = d.get('Longitude'), d.get('Latitude')
    geoid = name = ''
    if lon and lat:
        q = urllib.parse.urlencode({'geometry': f'{lon},{lat}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326,
                                    'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'GEOID,NAME,BASENAME', 'returnGeometry': 'false', 'f': 'json'})
        for t in range(3):
            try:
                j = json.load(urllib.request.urlopen(URL + q, timeout=60)); break
            except Exception as e:
                j = {}; time.sleep(2)
        f = j.get('features', [])
        if f:
            a = f[0]['attributes']; geoid, name = a['GEOID'], a['NAME']
    d['cousub_geoid'] = geoid; d['cousub_name'] = name
    out.append(d)
keys = list(out[0].keys())
with open('school_town_geocode.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)
print(len(out), sum(1 for o in out if not o['cousub_geoid']), 'unmatched')

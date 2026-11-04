"""Build school-level and town-level school-risk files. Run from schools folder: python3 -I build_school_risk.py
Inputs (all in this folder): school_town_geocode.csv, nces_dl/vt_membership_2425.csv, nces_dl/vt_directory_2425.csv,
aoe_redistricting_data/*.xlsx, ../sos2026/turnOut.json. Hand-coded news-based closure facts are in CLOSURES below (see SOURCES.md)."""
import sys, csv, json, re, collections
sys.path.insert(0, '.')
from xlsx_read import read_xlsx

sos = [x['tn'] for x in json.load(open('../sos2026/turnOut.json'))['d']]
sosset = set(sos)

def norm_town(name):
    n = name.upper().replace('ST.', 'SAINT').replace('  ', ' ').strip()
    n = n.replace('FAIRLEE', 'FAIRLEE')
    if n in sosset: return n
    for suf in (' TOWN', ' CITY', ' VILLAGE'):
        if n.endswith(suf) and n[:-len(suf)] in sosset: return n[:-len(suf)]
    return None

# ---- schools
geo = list(csv.DictReader(open('school_town_geocode.csv')))
mem = {r['ST_SCHID'].split('-')[-1]: int(r['STUDENT_COUNT']) for r in csv.DictReader(open('nces_dl/vt_membership_2425.csv')) if r['TOTAL_INDICATOR'] == 'Education Unit Total'}
dire = {r['ST_SCHID'].split('-')[-1]: r for r in csv.DictReader(open('nces_dl/vt_directory_2425.csv'))}
f10 = read_xlsx('aoe_redistricting_data/F.10.-10-Year-Enrollment---School-Level.xlsx')['K-12']
f10d = {r[0]: r for r in f10[1:] if r and r[0]}
def num(x):
    try: return int(float(x))
    except: return ''

# Closure facts (news / AOE F.47). status: closed_by_SY25-26 (F.47) | approved_close | merged_into_other | 
CLOSURES = {
 'PS209': ('closed_SY25-26', 'AOE F.47 lists North Hero Elementary closed SY25-26'),
 'PS244': ('closed_SY25-26', 'AOE F.47 lists Ripton Elementary closed SY25-26'),
 'PS126': ('pk_only_SY25-26', 'AOE F.47: Lakeview Union now only serving PK'),
 'PS292': ('pk_only_SY25-26', 'AOE F.47: Summit Street now only serving PK'),
 'PS149': ('closure_approved_2026', 'AOE F.47: Jamaica Village K-12 ceased SY24-25 (PK only); voters Apr 8 2026 authorized closure 102-36'),
 'PS177': ('closure_approved_2026', 'Marlboro voters approved closing Marlboro Elementary Mar 3 2026, 311-65'),
 'PS240': ('closure_approved_2026', 'Readsboro voters approved closing school Mar 3 2026, 222-36'),
 'PS293': ('closure_approved_2026', 'Taconic & Green board voted 11-2 on Nov 4 2025 to close Sunderland School effective July 1 2026'),
 'PS079': ('closure_approved_2026', 'Taconic & Green board voted 11-2 on Nov 4 2025 to close Currier Memorial (Danby) effective July 1 2026'),
 'PS268': ('merged_2026', 'ACSD board voted 8-1 Nov 2025 to move Shoreham K-5 into Bridport Central from fall 2026; Shoreham becomes PreK hub'),
}
# closed before SY24-25 window but since 2020 (AOE F.47; not in F.17, town taken from school name): (name, town, year)
CLOSED_2020_PLUS_NOT_IN_F17 = [('Roxbury Village School', 'ROXBURY', 'SY24-25'), ('Windham Elementary', 'WINDHAM', 'SY24-25'), ('Castleton Village School', 'CASTLETON', 'SY22-23')]
# board voted to close but voters rejected (Feb 10 2026) / proposed
PROPOSED_NOT_ENACTED = {
 'CALAIS': 'Washington Central board voted 8-5 (Dec 2025) to close Calais Elementary; voters kept it open 398-249 on Feb 10 2026',
 'WORCESTER': 'Washington Central board voted 8-5 (Dec 2025) to close Doty Memorial; voters kept it open 212-114 on Feb 10 2026',
 'STARKSBORO': 'Robinson Elementary named as possible closure candidate by Mt Abraham USD; town advisory vote on withdrawing from district (Mar 2026); outcome not verified',
 'DANVILLE': 'Danville voters were to decide Dec 6 2025 whether to close high school grades and move to school choice; outcome not verified',
}

TOWN_OVERRIDE = {'PS027': 'FAIRFAX'}
schools = []
for g in geo:
    sid = g['ORG_ID']
    town = norm_town(g['cousub_name'])
    method = 'TIGERweb point-in-polygon on AOE F.17 lat/long'
    if sid in TOWN_OVERRIDE: town = TOWN_OVERRIDE[sid]; method = 'manual override (F.17 coordinates fall in wrong town; school title/postal city = Fairfax)'
    d = dire.get(sid, {})
    grades = [x.replace('#', '') for x in g['Grades'].split(';')]
    k12 = [x for x in grades if x not in ('PK', 'EE', 'AE')]
    cl = CLOSURES.get(sid, ('', ''))
    e = mem.get(sid, '')
    schools.append(dict(school_id=sid, school_name=g['Title'], town=town or '', tiger_name=g['cousub_name'], county=g['County'],
        grades=g['Grades'].replace('#', ''), gslo=d.get('GSLO', ''), gshi=d.get('GSHI', ''), has_k_plus_grades=int(bool(k12)),
        enroll_2024_25_nces=e, f10_k12_2023=num(f10d.get(sid, [None]*13)[11] if sid in f10d else ''), f10_k12_2024=num(f10d.get(sid, [None]*13)[12] if sid in f10d else ''),
        operating_org=g['Operating Organization'], supervisory_union=g['Parent Organization'], lat=g['Latitude'], lon=g['Longitude'],
        town_assignment_method=method, closure_status=cl[0], closure_source_note=cl[1]))
with open('school_level_vt_2425.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(schools[0].keys())); w.writeheader(); w.writerows(schools)
bad = [s for s in schools if not s['town']]
print('schools', len(schools), 'unmapped towns', [(s['school_name'], s['tiger_name']) for s in bad])

# ---- town resident ADM (F.9)
w9 = read_xlsx('aoe_redistricting_data/F.9.-F.40.-Single-year-ADM-by-grade-for-towns-and-districts-FY20-FY24-and-change-over-period.xlsx')
adm = {}; tally = {}
for sh, key in (('FY20 by town', 'fy20'), ('FY24 by town', 'fy24')):
    for r in w9[sh][12:]:
        if not r or not r[0] or not re.match(r'T\d{3}$', str(r[0])): continue
        nm = re.sub(r' ID$', '', r[1].strip())
        MAN = {'Mt. Tabor': 'MOUNT TABOR', 'Mt. Holly': 'MOUNT HOLLY', 'So.Hero': 'SOUTH HERO', 'Orleans': 'BARTON', 'North Bennington': 'BENNINGTON',
               'Wells River': 'NEWBURY', 'Essex Junction': 'ESSEX JUNCTION CITY', 'Vergennes': 'VERGENNES', 'Winooski': 'WINOOSKI'}
        t = MAN.get(nm) or norm_town(nm)
        if nm in ('Glastenbury', "Buel's Gore", 'Averill', "Avery's Gore", 'Ferdinand', 'Lewis', "Warner's Grant", "Warren's Gore", 'Somerset'): continue
        tot = r[23] if len(r) > 23 else None
        # total is last numeric col: find header 'Total' position = 24
        try: tot = float(r[24])
        except: tot = None
        if t is None: print('F9 unmatched', sh, r[0], r[1]); continue
        adm.setdefault(t, {}).setdefault(key, 0.0); tally[key] = tally.get(key, 0) + (tot or 0)
        if tot is not None: adm[t][key] += tot

print('F9 sum check (excl. gores)', tally, 'statewide FY20 86428.87 FY24 82422.96')
# ---- aggregate
by = collections.defaultdict(list)
for s in schools:
    if s['town']: by[s['town']].append(s)
closed_extra = collections.defaultdict(list)
for n, t, y in CLOSED_2020_PLUS_NOT_IN_F17: closed_extra[t].append((n, y))

out = []
for t in sorted(sos):
    ss = [s for s in by.get(t, []) if s['has_k_plus_grades'] and isinstance(s['enroll_2024_25_nces'], int) and s['enroll_2024_25_nces'] > 0]
    ens = [s['enroll_2024_25_nces'] for s in ss]
    allst = by.get(t, [])
    enacted = [s for s in allst if s['closure_status']]
    closing = [s for s in ss if s['closure_status'] in ('closed_SY25-26', 'pk_only_SY25-26', 'closure_approved_2026', 'merged_2026')]
    remaining = [s for s in ss if not s['closure_status'] or s['closure_status'] == '']
    notes = []
    if t in PROPOSED_NOT_ENACTED: notes.append(PROPOSED_NOT_ENACTED[t])
    for s in closing: notes.append(f"{s['school_name']}: {s['closure_source_note']}")
    for n, y in closed_extra.get(t, []): notes.append(f'{n} closed {y} (AOE F.47; town inferred from school name)')
    if t in ('SAINT ALBANS CITY',): pass
    since2020 = len(closing) + len(closed_extra.get(t, []))
    row = dict(town=t,
        has_school=int(len(ss) > 0),
        n_schools_in_town=len(ss),
        total_enrollment_in_town=sum(ens) if ss else '',
        smallest_school_enrollment=min(ens) if ss else '',
        n_schools_below_100=sum(1 for e in ens if e < 100) if ss else '',
        n_schools_below_50=sum(1 for e in ens if e < 50) if ss else '',
        n_schools_closing_or_merging_2526_2627=len(closing),
        closure_or_merger_flag=int(len(closing) > 0),
        closure_proposed_not_enacted_flag=int(t in PROPOSED_NOT_ENACTED),
        n_closed_since_2020_incl_above=since2020,
        n_schools_remaining_after_closures=len(remaining) if ss else (0),
        resident_adm_fy24=round(adm.get(t, {}).get('fy24', 0), 2) if t in adm else '',
        resident_adm_fy20=round(adm.get(t, {}).get('fy20', 0), 2) if t in adm else '',
        proposed_district='', tax_change='',
        school_names='; '.join(f"{s['school_name']} ({s['enroll_2024_25_nces']})" for s in ss),
        notes=' | '.join(notes))
    if row['resident_adm_fy24'] != '' and row['resident_adm_fy20'] not in ('', 0):
        row['resident_adm_pct_change_fy20_24'] = round(100 * (row['resident_adm_fy24'] / row['resident_adm_fy20'] - 1), 1)
    else: row['resident_adm_pct_change_fy20_24'] = ''
    if t in ('ESSEX TOWN', 'ESSEX JUNCTION CITY'):
        row['resident_adm_pct_change_fy20_24'] = ''
        row['resident_adm_fy20'] = ''
        notes.append('Essex Junction split from Essex Town for FY24; FY20 resident ADM not comparable (combined Essex Town + Essex Junction FY20 3524.33 vs FY24 3287.32)')
        row['notes'] = ' | '.join(notes)
    out.append(row)
cols = ['town','n_schools_in_town','total_enrollment_in_town','smallest_school_enrollment','has_school','n_schools_below_100','n_schools_below_50',
        'closure_or_merger_flag','n_schools_closing_or_merging_2526_2627','closure_proposed_not_enacted_flag','n_closed_since_2020_incl_above','n_schools_remaining_after_closures',
        'resident_adm_fy24','resident_adm_fy20','resident_adm_pct_change_fy20_24','proposed_district','tax_change','school_names','notes']
with open('school_risk_by_town.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(out)
print(len(out), 'towns;', 'has_school', sum(r['has_school'] for r in out), 'closure flag', sum(r['closure_or_merger_flag'] for r in out),
      'below100', sum(1 for r in out if r['n_schools_below_100'] not in ('', 0)), 'adm', sum(1 for r in out if r['resident_adm_fy24'] != ''))

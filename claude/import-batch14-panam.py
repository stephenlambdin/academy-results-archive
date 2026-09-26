#!/usr/bin/env python3
"""2025 Presidents Cup Pan Am: bracket structure and printed names from the official
PATU draw sheet; winners and round scores from taekwondo.tv, joined on match number.
Method is left blank (taekwondo.tv carries none). Stephen's call, 2026-09-27."""
import pymupdf, re, json, pickle, subprocess, unicodedata, csv
from build import *

ENT = re.compile(r'^\((\d+|x)\)\s+(.+?)\s+(\.?[A-Z]{2,3})$')

def spans(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                t = s['text'].strip()
                if t: out.append(dict(x0=s['bbox'][0], y0=s['bbox'][1], x1=s['bbox'][2], y1=s['bbox'][3], t=t, size=s['size']))
    return out

def parse_draw(page):
    sp = spans(page); W = page.rect.width; cx = W / 2
    head = {}
    for s in sp:
        m = re.search(r'(Men|Women)\s+([+-]\d+kg)\s+Contestants:\s*(\d+)', s['t'])
        if m: head.update(gender=m.group(1), weight=m.group(2), count=int(m.group(3)))
        m = re.search(r'(MON|TUE|WED|THU|FRI|SAT|SUN) \d{2} [A-Z]{3} \d{4}', s['t'])
        if m and s['y0'] < 40: head['date'] = m.group(0)
    ents = []
    for s in sp:
        m = ENT.match(s['t'])
        if m and 70 < s['y0'] < 540:
            ents.append(dict(kind='E', name=m.group(2), noc=m.group(3).lstrip('.') or 'WT',
                             y=(s['y0'] + s['y1']) / 2, side='L' if s['x0'] < cx else 'R', w=s['x1'] - s['x0']))
    nums = [s for s in sp if re.fullmatch(r'\d{3,4}', s['t']) and 70 < s['y0'] < 540]
    center = [n for n in nums if abs((n['x0'] + n['x1']) / 2 - cx) < 15]
    assert len(center) == 1, (head, [n['t'] for n in center])
    side_nums = [n for n in nums if n not in center]
    matches = []
    def build(side):
        live = sorted([e for e in ents if e['side'] == side], key=lambda e: e['y'])
        mine = [n for n in side_nums if (n['x0'] < cx) == (side == 'L')]
        cols = sorted(set(round(n['x0']) for n in mine), reverse=(side == 'R'))
        for c in cols:
            for n in sorted([n for n in mine if round(n['x0']) == c], key=lambda n: n['y0']):
                ny = (n['y0'] + n['y1']) / 2
                t = max([e for e in live if e['y'] < ny], key=lambda e: e['y'])
                b = min([e for e in live if e['y'] > ny], key=lambda e: e['y'])
                node = dict(kind='M', no=n['t'], y=ny, feeders=(t, b))
                live.remove(t); live.remove(b); live.append(node); live.sort(key=lambda e: e['y'])
                matches.append(node)
        return live
    L = build('L'); R = build('R')
    assert len(L) == 1 and len(R) == 1
    fin = dict(kind='M', no=center[0]['t'], feeders=(L[0], R[0]))
    matches.append(fin)
    def depth(m, d=0):
        m['depth'] = d
        for f in m['feeders']:
            if f['kind'] == 'M': depth(f, d + 1)
    depth(fin)
    entrants = [(e['name'], e['noc']) for e in sorted([e for e in ents if e['side'] == 'L'], key=lambda e: e['y'])] + \
               [(e['name'], e['noc']) for e in sorted([e for e in ents if e['side'] == 'R'], key=lambda e: e['y'])]
    return dict(head, entrants=entrants, matches=matches, widths={(e['name'], e['noc']): e['w'] for e in ents})

def toks(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().upper()
    return [t for t in re.split(r'[^A-Z]+', s) if len(t) > 1]

def overlap(tvp, ent):
    """0 = not this person. Entrants flagged .WT in the draw (Costa Rica) come back as CRC."""
    c = tvp['country'].lstrip('.')
    if c != ent[1] and ent[1] != 'WT': return 0
    et = toks(ent[0]); tt = toks(tvp['name'])
    if not et: return 0
    if not (et[0] in tt or (len(et[0]) >= 5 and any(t.startswith(et[0][:5]) for t in tt))): return 0
    return 1 + sum(1 for t in et[1:] if any(u.startswith(t) or t.startswith(u) for u in tt))

RN = {0: 'F', 1: 'SF', 2: 'QF', 3: 'R16', 4: 'R32', 5: 'R64'}

def fill(draw, tvb, notes, tag):
    tvm = {m['matchNumber']: m for m in tvb['matches']}
    parent = {}
    for m in draw['matches']:
        for f in m['feeders']:
            if f['kind'] == 'M': parent[id(f)] = m
    golds = []
    issues = []; rows = []
    def ident(x): return (x['name'], x['noc']) if x['kind'] == 'E' else x.get('winner')
    for m in draw['matches']:
        t, b = m['feeders']; ti, bi = ident(t), ident(b)
        tv = tvm.get(m['no'])
        if tv is None or ti is None or bi is None:
            issues.append(f"match {m['no']}: missing ({'no tv match' if tv is None else 'feeder unresolved'})"); m['winner'] = None; continue
        ps = [p for p in tv['participants'] if p.get('name')]
        if len(ps) != 2 or tv['state'] != 'DONE':
            issues.append(f"match {m['no']}: tv has {len(ps)} participants, state {tv['state']}"); m['winner'] = None; continue
        pmap = {}
        for p in ps:
            sc = {e: overlap(p, e) for e in (ti, bi)}
            best = max(sc.values())
            hits = [e for e in (ti, bi) if sc[e] == best and best > 0]
            if len(hits) != 1:
                issues.append(f"match {m['no']}: tv '{p['name']}' {p['country']} maps to {hits} (feeders {ti} / {bi})"); break
            pmap[hits[0]] = p
        if len(pmap) != 2: m['winner'] = None; continue
        w = [e for e, p in pmap.items() if p['isWinner']]
        flag_w = w[0] if len(w) == 1 else None
        # progression: the participant who appears in the parent match on taekwondo.tv
        par = parent.get(id(m)); prog_w = None
        if par is not None and par['no'] in tvm:
            nxt = [q for q in tvm[par['no']]['participants'] if q.get('name')]
            adv = [e for e, p in pmap.items() if any(q['name'] == p['name'] for q in nxt)]
            if len(adv) == 1: prog_w = adv[0]
        if par is None:
            gold = [x for x in golds if x[0] == 1]
            prog_w = flag_w
        if prog_w is None and flag_w is None:
            issues.append(f"match {m['no']}: no winner"); m['winner'] = None; continue
        w = prog_w or flag_w
        suspect = flag_w is not None and prog_w is not None and flag_w != prog_w
        if suspect:
            notes.append(f"{tag} match {m['no']}: taekwondo.tv flags {flag_w[0]} as winner but {prog_w[0]} is the one who "
                         f"appears in match {par['no']}; winner taken from progression, score left blank")
        l = bi if w == ti else ti
        m['winner'], m['loser'] = w, l
        ws, ls = pmap[w]['resultText'], pmap[l]['resultText']
        score = ''
        if suspect: ws = ls = ''
        if re.fullmatch(r'\d+', ws or '') and re.fullmatch(r'\d+', ls or ''):
            if not (ws == '0' and ls == '0'): score = f'{ws}:{ls}'
        rows.append(dict(round=RN[m['depth']], no=m['no'], winner=w[0], wnoc=w[1], loser=l[0], lnoc=l[1], method='', score=score))
    return rows, issues

if __name__ == '__main__':
    doc = pymupdf.open('src/pan_draw.pdf')
    # medallists (official PATU / WT results system P14)
    txt = subprocess.run(['pdftotext', '-layout', 'src/pan_med.pdf', '-'], capture_output=True, text=True).stdout
    meds = {}; cur = []; pending = []
    for l in txt.split('\n'):
        m = re.search(r'\b(GOLD|SILVER|BRONZE)\s+(.+?)\s{2,}(\.?[A-Z]{2,3})\s*$', l)
        if m: pending.append(({'GOLD': 1, 'SILVER': 2, 'BRONZE': 3}[m.group(1)], m.group(2).strip(), m.group(3).lstrip('.') or 'WT'))
        d = re.match(r'^\s*([MW]) ([+-]\d+kg)\s', l)
        if d: pending.append(('DIV', d.group(1), d.group(2)))
    # division label sits between SILVER and first BRONZE; regroup in blocks of 4 medals
    divorder = [p for p in pending if p[0] == 'DIV']; medl = [p for p in pending if p[0] != 'DIV']
    for i, dv in enumerate(divorder):
        meds[('Men' if dv[1] == 'M' else 'Women') + ' ' + dv[2]] = medl[i * 4:(i + 1) * 4]
    arch = {}
    for r in csv.DictReader(open('archive_results.csv', encoding='utf-8')):
        arch.setdefault((r['Athlete'], r['NOC']), set()).add(r['EventID'])
    import run_muju_expand as X
    X.arch = arch; X.arch_names = set(arch)
    notes = []; divs = []
    for pno in range(len(doc)):
        dr = parse_draw(doc[pno])
        tag = f"{dr['gender']} {dr['weight']}"
        wc = ('M' if dr['gender'] == 'Men' else 'F') + dr['weight']
        tvb = json.load(open(f'tv/{wc}.json'))['bracket']
        rows, iss = fill(dr, tvb, notes, tag)
        md = meds.get(tag, [])
        ren = {e: X.expand(e, 100 if len(e[0]) >= 16 else 0, md, notes, tag) for e in dr['entrants']}
        ents = [(ren[e], e[1]) for e in dr['entrants']]
        for r in rows:
            r['winner'] = ren[(r['winner'], r['wnoc'])]; r['loser'] = ren[(r['loser'], r['lnoc'])]
        d = dict(division='Senior ' + tag, count=dr['count'], entrants=ents, matches=rows, date=iso(dr['date']), parse_issues=iss)
        d['placements'] = placements(ents, md, notes, tag)
        d['medallists'] = md
        d['issues'] = d['parse_issues'] + verify(d, False)
        divs.append(d)
    ev = dict(id='presidents-cup-america-2025', name='2025 Presidents Cup Pan Am', location='Lima, Peru',
              level='Presidents Cup', divisions=divs, start=min(d['date'] for d in divs))
    print(ev['id'], ev['start'], len(divs), sum(d['count'] for d in divs), sum(len(d['matches']) for d in divs))
    for d in divs: print('  ', d['division'], d['count'], len(d['matches']), d['issues'][:6])
    for n in notes:
        if 'expanded' not in n: print('   note:', n)
    print(sum('expanded' in n for n in notes), 'expansions')
    pickle.dump((ev, notes), open('panam.pkl', 'wb'))

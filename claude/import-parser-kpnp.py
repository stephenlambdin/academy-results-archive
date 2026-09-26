#!/usr/bin/env python3
"""Parser for the KPNP draw sheets used at the Muju Taekwondowon 2025 WT Grand Prix
Challenge (DXperience producer, 842x616 landscape). Layout:
  entrants  '(seed) (NOC) SURNAME Given'  (NOC-first, names truncated at ~100pt)
  match box number; winner label ~7pt ABOVE it, method ~7pt BELOW it, both on the
  outer side of the box (right of it on the left half, left of it on the right half)
  final in the centre, a Bronze Medal Match below it, classification block at the bottom.
Scores print top-feeder-first (left finalist first in the final)."""
import pymupdf, re

ENT = re.compile(r'^\((\d+|[Xx])\)\s+\((\.?[A-Z]{2,3})\)\s+(.+?)\s*$')
METH = re.compile(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN|GDP)\b\s*(\d+)?\s*-?\s*(\d+)?')
NUM = re.compile(r'^\d{3,4}$')

def norm(s): return re.sub(r'[^A-Z]', '', s.upper())

def spans(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            run = []
            for s in l['spans'] + [None]:
                if s is not None and not s['text'].strip(): continue
                if s is not None and run and s['bbox'][0] - run[-1]['bbox'][2] < 4 and abs(s['size'] - run[-1]['size']) < 0.3:
                    run.append(s); continue
                if run:
                    t = ' '.join(z['text'].strip() for z in run)
                    t = re.sub(r'\s+', ' ', t).strip()
                    out.append(dict(x0=run[0]['bbox'][0], y0=run[0]['bbox'][1], x1=run[-1]['bbox'][2], y1=run[0]['bbox'][3],
                                    t=t, size=run[0]['size']))
                run = [s] if s is not None else []
    return out

def label_matches(label, ent):
    """label like 'TRUONG T.K.T. (VI', 'BAUYRZHANOV', 'LEE Y. (KOR)' against entrant (name, noc)."""
    lab = re.sub(r'\s*\([A-Z. ]*\)?\s*$', '', label).strip()        # drop (NOC or partial
    m = re.search(r'\((\.?[A-Z]{1,3})\)?\s*$', label)
    lnoc = m.group(1).lstrip('.') if m else ''
    if lnoc and not ent[1].lstrip('.').startswith(lnoc): return False
    toks = lab.split()
    if not toks: return False
    sur = norm(toks[0]) if len(toks) > 1 or lab.endswith('.') else norm(lab)
    name = norm(ent[0])
    # surname part: every word before the initials
    words = [w for w in toks if not re.fullmatch(r'([A-Z]\.)+[A-Z]?\.?|[A-Z]', w)]
    sur = norm(' '.join(words)) if words else sur
    return bool(sur) and name.startswith(sur[:max(3, len(sur))])

def parse(page):
    sp = spans(page); W = page.rect.width
    head = {}
    for s in sp:
        m = re.search(r'(Men|Women)\s+([+-]\d+kg)\s+Contestants:\s*(\d+)', s['t'])
        if m: head.update(gender=m.group(1), weight=m.group(2), count=int(m.group(3)))
        m = re.search(r'(MON|TUE|WED|THU|FRI|SAT|SUN) \d{2} [A-Z]{3} \d{4}', s['t'])
        if m and s['y0'] < 70: head['date'] = m.group(0)
    legend_y = min([s['y0'] for s in sp if s['t'].startswith('LEGEND')], default=1e9)
    cls_y = min([s['y0'] for s in sp if s['t'] == 'Classification'], default=1e9)
    body = [s for s in sp if 85 < s['y0'] < legend_y]
    ents = []
    for s in body:
        m = ENT.match(s['t'])
        if m and (s['x0'] < W * 0.3 or s['x1'] > W * 0.7):
            ents.append(dict(kind='E', name=m.group(3), noc=m.group(2).lstrip('.') or 'WT',
                             y=(s['y0'] + s['y1']) / 2, side='L' if s['x0'] < W / 2 else 'R', w=s['x1'] - s['x0']))
    nums = [s for s in body if NUM.match(s['t']) and abs(s['size'] - 7.0) < 0.6 and not ENT.match(s['t'])]
    labels = [s for s in body if not NUM.match(s['t']) and not METH.match(s['t']) and not ENT.match(s['t'])
              and abs(s['size'] - 6.0) < 0.6]
    meths = [s for s in body if METH.match(s['t'])]
    cx = W / 2
    center = [n for n in nums if abs((n['x0'] + n['x1']) / 2 - cx) < 20]
    final = min(center, key=lambda n: n['y0'])
    bronze = [n for n in center if n is not final]
    side_nums = [n for n in nums if n not in center]
    matches = []
    def build(side):
        live = [e for e in ents if e['side'] == side]
        live.sort(key=lambda e: e['y'])
        mine = [n for n in side_nums if (n['x0'] < cx) == (side == 'L')]
        cols = sorted(set(round(n['x0']) for n in mine), reverse=(side == 'R'))
        for c in cols:
            for n in sorted([n for n in mine if round(n['x0']) == c], key=lambda n: n['y0']):
                ny = (n['y0'] + n['y1']) / 2
                above = [e for e in live if e['y'] < ny]; below = [e for e in live if e['y'] > ny]
                t = max(above, key=lambda e: e['y']); b = min(below, key=lambda e: e['y'])
                node = dict(kind='M', no=n['t'], y=ny, feeders=(t, b), num=n, side=side)
                live.remove(t); live.remove(b); live.append(node); live.sort(key=lambda e: e['y'])
                matches.append(node)
        return live
    L = build('L'); R = build('R')
    assert len(L) == 1 and len(R) == 1, (head, len(L), len(R))
    fin = dict(kind='M', no=final['t'], y=(final['y0'] + final['y1']) / 2, feeders=(L[0], R[0]), num=final, side='C')
    matches.append(fin)
    # attach label + method to each match box
    inner = {id(f) for f in fin['feeders']}
    for m in matches:
        n = m['num']
        side = m['side']
        tol = 6
        if id(m) in inner: side = {'L': 'R', 'R': 'L'}[side]; tol = 13   # semifinal labels sit on the other side
        if side == 'L':
            lab = [s for s in labels if 0 < n['y0'] - s['y0'] < 16 and abs(s['x0'] - (n['x1'] + 4)) < tol]
            met = [s for s in meths if 0 < s['y0'] - n['y0'] < 14 and abs(s['x0'] - (n['x1'] + 4)) < tol]
        elif side == 'R':
            lab = [s for s in labels if 0 < n['y0'] - s['y0'] < 16 and abs(s['x1'] - (n['x0'] - 4)) < tol]
            met = [s for s in meths if 0 < s['y0'] - n['y0'] < 14 and abs(s['x1'] - (n['x0'] - 4)) < tol]
        else:
            ncx = (n['x0'] + n['x1']) / 2
            lab = [s for s in labels if 0 < n['y0'] - s['y0'] < 20 and abs((s['x0'] + s['x1']) / 2 - ncx) < 20]
            met = [s for s in meths if 0 < s['y0'] - n['y0'] < 16 and abs((s['x0'] + s['x1']) / 2 - ncx) < 20]
        m['label'] = min(lab, key=lambda s: n['y0'] - s['y0'])['t'] if lab else None
        m['method_raw'] = min(met, key=lambda s: s['y0'] - n['y0'])['t'] if met else None
    # resolve winners bottom-up (matches already in dependency order)
    def ident(x): return (x['name'], x['noc']) if x['kind'] == 'E' else x.get('winner')
    issues = []
    for m in matches:
        t, b = m['feeders']; ti, bi = ident(t), ident(b)
        if ti is None or bi is None:
            issues.append(f"match {m['no']}: feeder unresolved"); m['winner'] = None; continue
        if m['label'] is None: issues.append(f"match {m['no']}: no label"); m['winner'] = None; continue
        tm, bm = label_matches(m['label'], ti), label_matches(m['label'], bi)
        if tm == bm:
            issues.append(f"match {m['no']}: label '{m['label']}' ambiguous/unmatched vs {ti} / {bi}"); m['winner'] = None; continue
        m['winner'] = ti if tm else bi; m['loser'] = bi if tm else ti; m['win_top'] = tm
    # bronze medal match: participants are the SF losers
    br = None
    if bronze:
        n = bronze[0]; ncx = (n['x0'] + n['x1']) / 2
        lab = [s for s in labels if 0 < n['y0'] - s['y0'] < 20 and abs((s['x0'] + s['x1']) / 2 - ncx) < 20]
        met = [s for s in meths if 0 < s['y0'] - n['y0'] < 16 and abs((s['x0'] + s['x1']) / 2 - ncx) < 20]
        sfl = [f.get('loser') for f in fin['feeders']] if all(f['kind'] == 'M' for f in fin['feeders']) else []
        lab = min(lab, key=lambda s: n['y0'] - s['y0'])['t'] if lab else None
        br = dict(kind='M', no=n['t'], side='B', label=lab, method_raw=(min(met, key=lambda s: s['y0'] - n['y0'])['t'] if met else None))
        if len(sfl) == 2 and all(sfl) and lab:
            tm, bm = label_matches(lab, sfl[0]), label_matches(lab, sfl[1])
            if tm != bm:
                br['winner'] = sfl[0] if tm else sfl[1]; br['loser'] = sfl[1] if tm else sfl[0]; br['win_top'] = tm
            else: issues.append(f"bronze {n['t']}: label '{lab}' ambiguous")
        else: issues.append(f"bronze {n['t']}: cannot resolve")
    # rounds: depth below the final
    def depth(m, d=0):
        m['depth'] = d
        for f in m['feeders']:
            if f['kind'] == 'M': depth(f, d + 1)
    depth(fin)
    RN = {0: 'F', 1: 'SF', 2: 'QF', 3: 'R16', 4: 'R32', 5: 'R64', 6: 'R128'}
    rows = []
    for m in matches + ([br] if br else []):
        if not m.get('winner'): continue
        method, score = '', ''
        raw = m.get('method_raw') or ''
        mm = re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN|GDP)\s*(\d+)?\s*-?\s*(\d+)?', raw)
        if mm:
            method = mm.group(1)
            if mm.group(2) is not None and mm.group(3) is not None and not (mm.group(2) == '0' and mm.group(3) == '0'):
                a, c = mm.group(2), mm.group(3)
                score = f'{a}:{c}' if m['win_top'] else f'{c}:{a}'
        else: issues.append(f"match {m['no']}: no method")
        rows.append(dict(round='BR' if m['side'] == 'B' else RN[m['depth']], no=m['no'], winner=m['winner'][0], wnoc=m['winner'][1],
                         loser=m['loser'][0], lnoc=m['loser'][1], method=method, score=score))
    # classification (given-name-first here, so only used as a cross-check)
    ents_out = [(e['name'], e['noc']) for e in sorted([e for e in ents if e['side'] == 'L'], key=lambda e: e['y'])] + \
               [(e['name'], e['noc']) for e in sorted([e for e in ents if e['side'] == 'R'], key=lambda e: e['y'])]
    widths = {(e['name'], e['noc']): e['w'] for e in ents}
    return dict(head, entrants=ents_out, matches=rows, issues=issues, widths=widths)

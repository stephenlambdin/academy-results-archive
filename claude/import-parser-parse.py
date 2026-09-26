#!/usr/bin/env python3
"""Bracket parser for WT draw-sheet PDFs (Academy Results Archive imports)."""
import pymupdf, re, json, sys, math, glob
from collections import defaultdict

ROUND_NAMES = {128:"R128",64:"R64",32:"R32",16:"R16",8:"QF",4:"SF",2:"F"}

ENTRANT_RE = re.compile(r'^\((\d+|x)\)\s+(.+?)\s+(\.?[A-Z]{2,3})$')
MATCHNO_RE = re.compile(r'^\d{3,4}(\.\d+)?$')
LABEL_RE   = re.compile(r'^(?!\()(.*?)\s*\.*\s*\((\.?[A-Z]{2,3})\)$')
DIV_RE     = re.compile(r'(Men|Women)\s+([+-]\d+kg)\s+Contestants\s*:\s+(\d+)')
METHOD_RE  = re.compile(r'^([A-Z]{2,3})?\s*(?:(\d+)-(\d+))?\s*(\(.*\))?\s*$')

class Node:
    def __init__(self, kind, y, athlete=None, noc=None):
        self.kind = kind
        self.y = y
        self.athlete = athlete
        self.noc = noc
        self.matchno = None
        self.round = None
        self.feeders = None
        self.label = None
        self.method = None
        self.score = None
        self.flags = []

def _norm(s):
    return re.sub(r'[^A-Z0-9]', '', s.upper())

def surname_match(label_part, label_noc, athlete, noc, strict=True):
    if noc != label_noc and not (len(label_noc) < 3 and noc.startswith(label_noc)) \
       and not (len(noc) < 3 and label_noc.startswith(noc)): return False
    a = _norm(athlete)
    base = _norm(label_part)
    if strict:
        return bool(base) and (a.startswith(base) or base.startswith(a))
    cands = [base]
    toks = [t for t in re.split(r"[.\s]+", label_part) if t]
    if len(toks) > 1:
        cands.append(_norm(' '.join(toks[1:] + toks[:1])))
        core = list(toks)
        while core and len(core[-1]) == 1: core.pop()
        if core and len(core) < len(toks):
            cands.append(_norm(' '.join(core)))
    for l in cands:
        if l and a.startswith(l[:max(3, len(l) - 1)]): return True
    for l in cands:
        if len(l) >= 6 and l in a: return True
    return False

def pick_feeder(t, b, lp, ln, check):
    st, sb = check(t, lp, ln, True), check(b, lp, ln, True)
    if st != sb: return ('t' if st else 'b'), False
    if st and sb: return None, True
    lt, lb = check(t, lp, ln, False), check(b, lp, ln, False)
    if lt != lb: return ('t' if lt else 'b'), False
    if lt and lb: return None, True
    return None, False

def resolve(node, label_part, label_noc):
    if node.kind == 'entrant':
        return surname_match(label_part, label_noc, node.athlete, node.noc, False)
    if node.athlete is not None:
        return surname_match(label_part, label_noc, node.athlete, node.noc, False)
    t, b = node.feeders
    def chk(n, lp, ln, s): return resolve_check(n, lp, ln, s)
    side, amb = pick_feeder(t, b, label_part, label_noc, chk)
    if amb:
        node.flags.append('ambiguous-back-resolution'); return True
    if side == 't':
        set_winner(node, t, label_part, label_noc); node.winner_is_top = True; return True
    if side == 'b':
        set_winner(node, b, label_part, label_noc); node.winner_is_top = False; return True
    return False

def resolve_check(node, lp, ln, strict=True):
    if node.kind == 'entrant': return surname_match(lp, ln, node.athlete, node.noc, strict)
    if node.athlete is not None: return surname_match(lp, ln, node.athlete, node.noc, strict)
    t, b = node.feeders
    return resolve_check(t, lp, ln, strict) or resolve_check(b, lp, ln, strict)

def set_winner(node, feeder, lp, ln):
    if feeder.kind == 'match' and feeder.athlete is None:
        resolve(feeder, lp, ln)
    node.athlete, node.noc = feeder_identity(feeder, lp, ln)

def feeder_identity(feeder, lp, ln):
    if feeder.kind == 'entrant': return feeder.athlete, feeder.noc
    if feeder.athlete is not None: return feeder.athlete, feeder.noc
    return None, None

ETU_ENT = re.compile(r'^\s*(\(\d+\)\s+)?([A-Z]{3})\s+(.+?)\s*$')
def etu_spans(page):
    """WT results system / ActiveReports sheets (ETU events): entrants print NOC-first
    ('(1) TUR YELALDI Kaan', ' GBR DONE Cameron') and byes print as 'Free draw'.
    Rewrite entrants to the name-then-NOC form and drop the byes."""
    sp = []; W = page.rect.width
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"]; x0, y0, x1, _ = s["bbox"]
                if not t.strip() or 'Free draw' in t: continue
                if (x0 < 100 or x1 > W - 40) and y0 > 70:
                    m = ETU_ENT.match(t)
                    if m and not re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN)\b', t.strip()):
                        t = f"{m.group(1) or ''}{m.group(3)} {m.group(2)}"
                sp.append((x0, y0, t.strip(), x1))
    return sp

def parse_page(page, overrides=None, variant=None, spans_override=None):
    # 'etu2026' = me2026 geometry on WT ActiveReports sheets, with an entrant pre-pass
    # and three small tolerances (see import-2026-generator-notes.md).
    etu = (variant == 'etu2026')
    # 'gpc2025' = wt2026 on the 2025 WT Grand Prix Challenge sheets (Chrome/Skia), where
    # long entrant names wrap onto a second line that carries given names + NOC.
    gpc = (variant == 'gpc2025')
    if gpc: variant = 'wt2026'
    if etu:
        variant = 'me2026'
        if spans_override is None: spans_override = etu_spans(page)
    EDGE_TOL = 4.5 if etu else 3.5
    ORPHAN_DY = 30 if etu else 14
    spans = []
    if spans_override is not None:
        spans = list(spans_override)
    else:
      d = page.get_text("dict")
      for b in d["blocks"]:
       for l in b.get("lines", []):
            if variant == 'wt2026':
                run = []
                for s in l["spans"]:
                    if not s["text"].strip() and not run: continue
                    if run and s["bbox"][0] - run[-1]["bbox"][2] < 3.5:
                        run.append(s)
                    else:
                        if run:
                            txt = ''.join(z["text"] for z in run).strip()
                            if txt: spans.append((run[0]["bbox"][0], run[0]["bbox"][1], txt, run[-1]["bbox"][2]))
                        run = [s]
                if run:
                    txt = ''.join(z["text"] for z in run).strip()
                    if txt: spans.append((run[0]["bbox"][0], run[0]["bbox"][1], txt, run[-1]["bbox"][2]))
            else:
                for s in l["spans"]:
                    t = s["text"].strip()
                    if t:
                        spans.append((s["bbox"][0], s["bbox"][1], t, s["bbox"][2]))
    if variant == 'wt2026':
        # merge rows wrapped onto a second line carrying only the NOC
        NOCTAIL = re.compile(r'^\(?\.?[A-Z]{2,3}\)?$')
        ENDSNOC = re.compile(r'(\(\.?[A-Z]{2,3}\)|\s\.?[A-Z]{2,3})$')
        spans.sort(key=lambda s: (s[1], s[0]))
        used = set()
        out_spans = []
        for i, (x, y, t, x1) in enumerate(spans):
            if i in used: continue
            if not NOCTAIL.fullmatch(t) and not ENDSNOC.search(t) and len(t) > 3:
                cand = [(j, bx, by, bt, bx1) for j, (bx, by, bt, bx1) in enumerate(spans)
                        if j not in used and j != i
                        and (NOCTAIL.fullmatch(bt) or (gpc and re.match(r'^\((\d+|x)\)\s', t)
                             and ENDSNOC.search(bt) and not bt.startswith('(')))
                        and 0 < by - y < 9 and (abs(bx - x) < 3 or abs(bx1 - x1) < 3)]
                if cand:
                    j, bx, by, bt, bx1 = min(cand, key=lambda c: c[2])
                    used.add(j)
                    out_spans.append(((x + bx) / 2.0 if abs(bx - x) < 3 else x, (y + by) / 2.0, (t + ' ' + bt).strip(), max(x1, bx1))); continue
            out_spans.append((x, y, t, x1))
        spans = out_spans
    out = {}
    title = min(spans, key=lambda s: s[1])[2]
    datem = None
    for x, y, t, *_x1 in spans:
        m = re.search(r'(MON|TUE|WED|THU|FRI|SAT|SUN) (\d{2}) ([A-Z]{3}) (\d{4})', t)
        if m and y < 95: datem = m
        dm = DIV_RE.search(t)
        if dm and y < 95:
            out['gender'], out['weight'], out['count'] = dm.group(1), dm.group(2), int(dm.group(3))
    out['title'] = title
    out['date'] = datem.group(0) if datem else None
    class_y = None
    for x, y, t, *_x1 in spans:
        if t == 'Classification': class_y = y
    podium = []
    if class_y:
        for x, y, t, *_x1 in spans:
            if y > class_y:
                m = re.match(r'^([123])\s+(.+?)\s+(\.?[A-Z]{2,3})$', t) or \
                    re.match(r'^([123])\s+(.+?)\s+\((\.?[A-Z]{2,3})\)$', t)
                if m and 'LEGEND' not in t and abs(x - 360) < 120:
                    podium.append((int(m.group(1)), m.group(2), m.group(3).lstrip('.') or 'WT'))
    if not podium and class_y:
        pls = [(x, y, t) for x, y, t, *_ in spans
               if re.fullmatch(r'[123]', t) and 330 < x < 372 and y > class_y - 2]
        for px, py, pt in pls:
            nm = [(x, t) for x, y, t, *_ in spans
                  if abs(y - py) <= 3.5 and 352 < x < 470 and not re.fullmatch(r'[123]', t)]
            nc = [(x, t) for x, y, t, *_ in spans
                  if abs(y - py) <= 3.5 and 470 < x < 525 and re.fullmatch(r'\.?[A-Z]{2,3}', t)]
            if nm and nc:
                nm.sort(); nc.sort()
                podium.append((int(pt), nm[0][1], nc[0][1].lstrip('.') or 'WT'))
    out['podium'] = podium
    legend_y = min([y for x, y, t, *_ in spans if t.startswith('LEGEND') or t.startswith('(x)Seed') or t.startswith('Page ')
                    or re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN|GDP|R|\(x\))\s*:', t)], default=1e9)
    hdr_ys = [y for x, y, t, *_ in spans if re.search(r'Round of \d|[Qq]uarter-?finals?|[Ss]emi-?finals?', t) or t == 'Final']
    body_top = (max(hdr_ys) + 6) if hdr_ys else 45
    page_cx = page.rect.width / 2
    cls_cut = (class_y - 3) if class_y else 1e9
    # Classification rows sit in a narrow centre column. The old 360..510 window is wide
    # enough to swallow a right-half winner label (Dutch Open M-87kg match 825 at x=509.8),
    # so me2026 uses the column the rows are actually printed in.
    cls_x0, cls_x1 = (340, 465) if variant == 'me2026' else (360, 510)
    body = [(x, y, t, x1) for x, y, t, x1 in spans
            if body_top < y < legend_y and not (y > cls_cut and cls_x0 < x < cls_x1)
            and not (y > cls_cut and re.match(r'^[123]\s', t))]
    entrants, matchnos, labels, methods = [], [], [], []
    name_only, noc_only = [], []
    if variant == 'wt2026':
        # merge entrant rows wrapped onto two lines: '(n) LONG NAME' + 'NOC'
        PRE = re.compile(r'^\((\d+|x)\)\s+(.+)$')
        BARE = re.compile(r'^\.?[A-Z]{2,3}$')
        merged_body, used = [], set()
        for i, (x, y, t, x1) in enumerate(body):
            if i in used: continue
            m = PRE.match(t)
            if m and not ENTRANT_RE.match(t):
                cand = [(j, bx, by, bt, bx1) for j, (bx, by, bt, bx1) in enumerate(body)
                        if j not in used and j != i and BARE.fullmatch(bt)
                        and 0 < by - y < 9 and (abs(bx - x) < 3 or abs(bx1 - x1) < 3)]
                if cand:
                    j, bx, by, bt, bx1 = min(cand, key=lambda c: c[2])
                    used.add(j)
                    merged_body.append((x, y, f'({m.group(1)}) {m.group(2)} {bt}', x1)); continue
            merged_body.append((x, y, t, x1))
        body = merged_body
    for x, y, t, x1 in body:
        m = ENTRANT_RE.match(t)
        if m:
            raw_noc = m.group(3)
            noc = raw_noc[1:] if raw_noc.startswith('.') else raw_noc
            if not noc: noc = 'WT'
            entrants.append((x, y, m.group(2), noc)); continue
        if MATCHNO_RE.match(t):
            matchnos.append((x, y, t)); continue
        lm = LABEL_RE.match(t)
        if lm and not re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN|GDP)\b', t):
            labels.append((x, y, lm.group(1), lm.group(2).lstrip('.') or 'WT', x1)); continue
        if variant in ('me2025','me2026'):
            lt = re.match(r'^(?!\()(.*?)\s*\(\.?([A-Z]{1,3})$', t)
            if lt and not re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN|GDP)\b', t):
                labels.append((x, y, lt.group(1), lt.group(2) or 'WT', x1)); continue
        mm = re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN|GDP)\b.*$', t) or re.match(r'^\d+\s*[-:]\s*\d+$', t)
        if mm:
            methods.append((x, y, t, x1)); continue
        if re.match(r'^\((\.?[A-Z]{2,3})\)$', t):
            noc_only.append((x, y, t[1:-1].lstrip('.') or 'WT')); continue
        if re.match(r"^[A-ZÀ-Þ][A-Za-zÀ-þ'.\- ]*\s+[A-ZÀ-Þ]\.?\.?$", t):
            name_only.append((x, y, t)); continue
        if variant == 'wt2026' and re.match(r"^[A-ZÀ-Þ?][A-Za-zÀ-þ'.\-?  ]*$", t) and len(t) > 1:
            name_only.append((x, y, t)); continue
        if variant in ('me2025','me2026'):
            m2 = re.match(r'^(?!Round\b)([A-ZÀ-ÞĀ-ž.].+?)\s+(\.?[A-Z]{2,3})$' if etu else r'^(?!Round\b)([A-ZÀ-Þ.].+?)\s+(\.?[A-Z]{2,3})$', t)
            if m2 and (x < 120 or x > page.rect.width - 200) and not MATCHNO_RE.match(t):
                raw_noc = m2.group(2)
                noc = raw_noc[1:] if raw_noc.startswith('.') else raw_noc
                entrants.append((x, y, m2.group(1), noc or 'WT')); continue
    for nx, ny, nt in name_only:
        cand = [(x, y, c) for x, y, c in noc_only if abs(x - nx) < 20 and 0 < y - ny < 14]
        if cand:
            cx_, cy_, cnoc = min(cand, key=lambda c: c[1] - ny)
            labels.append((nx, ny, nt, cnoc, nx + max(60, 3.6 * len(nt))))
            noc_only.remove((cx_, cy_, cnoc))
    if variant == 'wt2026':
        INIT_ONLY = re.compile(r'^[A-Z]\.?(?:[\s.]*[A-Z]\.?)*$')
        merged = []
        for lab in labels:
            lx, ly, lp, ln, lx1 = lab
            if INIT_ONLY.fullmatch(lp.strip()):
                cand = [(nx, ny, nt) for nx, ny, nt in name_only
                        if abs(nx - lx) < 22 and 0 < ly - ny < 14]
                if cand:
                    nx, ny, nt = max(cand, key=lambda c: c[1])
                    merged.append((nx, ny, (nt + ' ' + lp.strip()).strip(), ln, max(lx1, nx + 3.6 * len(nt))))
                    name_only = [n for n in name_only if n != (nx, ny, nt)]
                    continue
            merged.append(lab)
        labels = merged
    out['entrants_raw'] = entrants
    valid3 = set(l[3] for l in labels if len(l[3]) == 3) | set(p[2] for p in podium if len(p[2]) == 3)
    fixed = []
    for x, y, nm, noc in entrants:
        if len(noc) == 2 and noc != 'WT':
            up = [v for v in valid3 if v.startswith(noc)]
            if len(up) == 1:
                out.setdefault('flags', []).append(f'noc-upgraded:{nm} {noc}->{up[0]}')
                noc = up[0]
        fixed.append((x, y, nm, noc))
    entrants = fixed
    ents = [(x, y, nm, ('WT' if noc in ('WT','.WT') else noc)) for x, y, nm, noc in entrants]
    cols = []
    for x, y, t in sorted(matchnos):
        for c in cols:
            if abs(c[0] - x) < 8: c[1].append((x, y, t)); break
        else:
            cols.append([x, [(x, y, t)]])
    cols_sorted = sorted(cols, key=lambda c: c[0])
    fin_col = None
    if cols_sorted:
        singles = [c for c in cols_sorted if len(c[1]) == 1]
        pool = singles if singles else cols_sorted
        fin_col = min(pool, key=lambda c: abs(c[0] - page_cx))
        if len(cols_sorted) % 2 == 1 and cols_sorted[len(cols_sorted)//2] is not fin_col:
            out.setdefault('flags', []).append('final-col-not-middle')
    left_cols = [c for c in cols_sorted if fin_col and c[0] < fin_col[0]]
    right_cols = sorted([c for c in cols_sorted if fin_col and c[0] > fin_col[0]], key=lambda c: -c[0])
    center_cols = [fin_col] if fin_col else []
    ncols = max(len(left_cols), len(right_cols)) if (left_cols or right_cols) else 0
    bracket = 2 ** (ncols + 1)
    out['bracket'] = bracket
    def rname_for(side_cols, i):
        k = len(side_cols)
        return ROUND_NAMES[2 ** (k - i + 1)]
    lab_assign = {}
    lcol_xs = [c[0] for c in left_cols]
    rcol_xs = [c[0] for c in right_cols]
    in_l = max(lcol_xs) if lcol_xs else page_cx - 100
    in_r = min(rcol_xs) if rcol_xs else page_cx + 100
    center_labels, side_labels = [], []
    if variant == 'wt2026': labels_for_assign = []
    else: labels_for_assign = labels
    for lab in labels_for_assign:
        lx = lab[0]
        if variant in ('me2025','me2026'):
            is_center = (in_l + 4 < lx) and (lab[4] < in_r - 2)
        else:
            is_center = in_l + 4 < lx < in_r - 4
        if is_center: center_labels.append(lab)
        else: side_labels.append(lab)
    for lx, ly, lp, ln, lx1 in side_labels:
        items = None
        if lx < page_cx:
            cands = [x for x in lcol_xs if x < lx]
            if cands:
                colx = max(cands)
                items = next(c[1] for c in left_cols if c[0] == colx)
        else:
            anchor = (lx1 - 2) if variant in ('me2025','me2026') else lx
            cands = [x for x in rcol_xs if x > anchor]
            if cands:
                colx = min(cands)
                items = next(c[1] for c in right_cols if c[0] == colx)
        if not items:
            best, bd = None, 1e9
            for mx, my, mt in matchnos:
                dd = math.hypot(lx - mx, (ly - my) * 1.2)
                if dd < bd: bd, best = dd, (mx, my, mt)
            if best: lab_assign.setdefault(best, []).append((bd, lp, ln, lx, ly))
            continue
        best = min(items, key=lambda it: abs(it[1] - ly))
        lab_assign.setdefault(best, []).append((abs(best[1] - ly), lp, ln, lx, ly))
    cen_cands = []
    if left_cols: cen_cands += left_cols[-1][1]
    if fin_col: cen_cands += fin_col[1]
    if right_cols: cen_cands += right_cols[-1][1]
    if center_labels:
        import itertools
        best_perm, best_cost = None, 1e18
        k = len(center_labels)
        for perm in itertools.permutations(cen_cands, min(k, len(cen_cands))):
            cost = 0
            for lab, mno in zip(center_labels, perm):
                cost += math.hypot(lab[0] - mno[0], (lab[1] - mno[1]) * 1.5)
            if cost < best_cost: best_cost, best_perm = cost, perm
        if best_perm:
            for lab, mno in zip(center_labels, best_perm):
                lx, ly, lp, ln = lab[:4]
                lab_assign.setdefault(mno, []).append((math.hypot(lx - mno[0], ly - mno[1]), lp, ln, lx, ly))
    if variant in ('wt2026',):
        lab_assign = {}
        mn_items = [(mx, my, mt) for mx, my, mt in matchnos]
        for lx, ly, lp, ln, lx1 in labels:
            lc = (lx + lx1) / 2.0
            cands = [(round((my - ly) * 2) / 2.0, abs(((mx + mx + 12) / 2.0) - lc), mx, my, mt)
                     for mx, my, mt in mn_items
                     if lx - 30 <= mx <= lx1 + 30 and 4 <= my - ly <= 22]
            if not cands:
                out.setdefault('flags', []).append(f'label-unassigned:{lp} {ln}@{round(lx)},{round(ly)}')
                continue
            cands.sort()
            dy, d, mx, my, mt = cands[0]
            lab_assign.setdefault((mx, my, mt), []).append((d, lp, ln, lx, ly))
        meth_assign = {}
        meth_orphans = []
        for x, y, t, _mx1 in methods:
            mc = x
            best, bd = None, 1e9
            for lx, ly, lp, ln, lx1 in labels:
                if 4 <= y - ly <= 32 and abs(((lx + lx1) / 2.0) - ((x + x + 25) / 2.0)) < 40:
                    dd = (y - ly) + abs(lx - x) * 0.1
                    if dd < bd: bd, best = dd, (lx, ly)
            if best: meth_assign.setdefault(best, t)
            else: meth_orphans.append((x, y, t))
    elif variant == 'me2026':
      # Martial.Events / DXperience: the method sits directly under its winner label and
      # shares an edge with it -- left-aligned on the left half, RIGHT-aligned on the right
      # half. Matching on x0 alone silently steals a neighbouring column's method.
      meth_assign = {}
      meth_orphans = []
      for x, y, t, mx1 in methods:
        best, bd = None, 1e9
        for lx, ly, lp, ln, lx1 in labels:
            if not (0 < y - ly < 14): continue
            edge = min(abs(lx - x), abs(lx1 - mx1))
            if edge > EDGE_TOL: continue
            dd = (y - ly) + edge * 0.1
            if dd < bd: bd, best = dd, (lx, ly)
        if best is not None and best not in meth_assign: meth_assign[best] = t
        elif best is None: meth_orphans.append((x, y, t))
    else:
      meth_assign = {}
      meth_orphans = []
      unpaired = []
      for x, y, t, _mx1 in methods:
        best, bd = None, 1e9
        for lx, ly, lp, ln, lx1 in labels:
            if abs(lx - x) < 9 and 0 < y - ly < 26:
                dd = y - ly
                if dd < bd: bd, best = dd, (lx, ly)
        if best: meth_assign[best] = t
        else: unpaired.append((x, y, t))
      if variant == 'me2025':
        for x, y, t in unpaired:
            best, bd = None, 1e9
            for lx, ly, lp, ln, lx1 in labels:
                if abs(lx - x) < 80 and 0 < y - ly < 12:
                    dd = (y - ly) * 10 + abs(lx - x)
                    if dd < bd: bd, best = dd, (lx, ly)
            if best and best not in meth_assign: meth_assign[best] = t
    def build(side_ents, side_cols, mirror):
        live = [Node('entrant', y, nm, noc) for x, y, nm, noc in sorted(side_ents, key=lambda e: e[1])]
        matches = []
        for i, (cx, items) in enumerate(side_cols):
            for mx, my, mt in sorted(items, key=lambda it: it[1]):
                above = [n for n in live if n.y < my]
                below = [n for n in live if n.y > my]
                if not above or not below:
                    n = Node('match', my); n.flags.append('no-feeders'); n.matchno = mt; matches.append(n); continue
                top = max(above, key=lambda n: n.y)
                bot = min(below, key=lambda n: n.y)
                node = Node('match', my)
                node.matchno = mt; node.round = rname_for(side_cols, i)
                node.feeders = (top, bot)
                key = (mx, my, mt)
                if key in lab_assign:
                    cand = sorted(lab_assign[key])[0]
                    node.label = (cand[1], cand[2])
                    if (cand[3], cand[4]) in meth_assign:
                        node.method_raw = meth_assign[(cand[3], cand[4])]
                if overrides and mt in overrides:
                    ov = overrides[mt]
                    node.label = (ov[0], ov[1])
                    if len(ov) > 2: node.method_raw = ov[2]
                    node.flags.append('override-applied')
                live.remove(top); live.remove(bot); live.append(node)
                live.sort(key=lambda n: n.y)
                matches.append(node)
        return live, matches
    lents = [e for e in ents if e[0] < page_cx]
    rents = [e for e in ents if e[0] > page_cx]
    llive, lmatches = build(lents, left_cols, False)
    rlive, rmatches = build(rents, right_cols, True)
    allm = lmatches + rmatches
    fin = None
    if len(llive) == 1 and len(rlive) == 1 and center_cols:
        citems = center_cols[0][1]
        mx, my, mt = citems[0]
        fin = Node('match', my); fin.matchno = mt; fin.round = 'F'
        fin.feeders = (llive[0], rlive[0])
        key = (mx, my, mt)
        if key in lab_assign:
            cand = sorted(lab_assign[key])[0]
            fin.label = (cand[1], cand[2])
            if (cand[3], cand[4]) in meth_assign:
                fin.method_raw = meth_assign[(cand[3], cand[4])]
        if overrides and mt in overrides:
            ov = overrides[mt]
            fin.label = (ov[0], ov[1])
            if len(ov) > 2: fin.method_raw = ov[2]
            fin.flags.append('override-applied')
        if fin.label is None and podium:
            golds = [p for p in podium if p[0] == 1]
            if golds:
                fin.label = (golds[0][1], golds[0][2])
                out.setdefault('notes', []).append('final-winner-from-classification')
        if getattr(fin, 'method_raw', None) is None and meth_orphans:
            near = [(abs(ox - mx), ok) for ok, (ox, oy, ot) in enumerate(meth_orphans)
                    if abs(ox - mx) < 40 and 2 <= my - oy <= ORPHAN_DY]
            if near:
                near.sort()
                ok = near[0][1]
                fin.method_raw = meth_orphans[ok][2]
                out.setdefault('notes', []).append('final-method-from-orphan')
                meth_orphans.pop(ok)
        allm.append(fin)
    else:
        out.setdefault('flags', []).append(f'final-shape L{len(llive)} R{len(rlive)} C{len(center_cols)}')
    for node in allm:
        if node.label and node.feeders:
            lp, ln = node.label
            t, b = node.feeders
            def chk(n, p, c, s): return resolve_check(n, p, c, s)
            side, amb = pick_feeder(t, b, lp, ln, chk)
            if amb:
                node.flags.append('ambiguous-winner')
            elif side == 't':
                if t.kind == 'match' and t.athlete is None: resolve(t, lp, ln)
                node.athlete, node.noc = t.athlete, t.noc; node.winner_is_top = True
            elif side == 'b':
                if b.kind == 'match' and b.athlete is None: resolve(b, lp, ln)
                node.athlete, node.noc = b.athlete, b.noc; node.winner_is_top = False
            else:
                node.flags.append('label-no-match:' + lp + ' ' + ln)
    for ox, oy, ot in meth_orphans:
        out.setdefault('flags', []).append(f'method-unassigned:{ot}@{round(ox)},{round(oy)}')
    out['nodes'] = allm
    out['left_entrants'] = lents
    out['right_entrants'] = rents
    out['entrants'] = [(nm, noc) for x, y, nm, noc in sorted(lents, key=lambda e: e[1])] + \
                      [(nm, noc) for x, y, nm, noc in sorted(rents, key=lambda e: e[1])]
    return out

def emit_division(out, score_order='top'):
    issues = []
    matches = []
    for n in out['nodes']:
        if not n.feeders:
            issues.append(f'match {n.matchno}: no feeders'); continue
        t, b = n.feeders
        tw = (t.athlete, t.noc); bw = (b.athlete, b.noc)
        if n.athlete is None:
            issues.append(f'match {n.matchno} ({n.round}): winner unresolved ' + str(n.flags))
            continue
        win_top = getattr(n, 'winner_is_top', None)
        if win_top is None:
            if tw[0] is not None and (n.athlete, n.noc) == tw: win_top = True
            elif bw[0] is not None and (n.athlete, n.noc) == bw: win_top = False
            else:
                issues.append(f'match {n.matchno}: orientation unknown'); continue
        winner = tw if win_top else bw
        loser  = bw if win_top else tw
        if winner[0] is None or loser[0] is None:
            issues.append(f'match {n.matchno}: participant identity missing')
            continue
        method, score = '', ''
        raw = getattr(n, 'method_raw', None)
        if raw:
            mm = re.match(r'^([A-Z]{2,3})?\s*(?:(\d+)\s*[-:]\s*(\d+))?', raw)
            method = mm.group(1) or ''
            if mm.group(2) is not None:
                a, bsc = mm.group(2), mm.group(3)
                if not (a == '0' and bsc == '0'):
                    if score_order == 'winner':
                        score = f'{a}:{bsc}'
                    else:
                        score = f'{a}:{bsc}' if win_top else f'{bsc}:{a}'
        matches.append(dict(round=n.round, no=n.matchno,
                            winner=winner[0], wnoc=winner[1],
                            loser=loser[0], lnoc=loser[1],
                            method=method, score=score))
        for f in n.flags: issues.append(f'match {n.matchno}: {f}')
    return matches, issues

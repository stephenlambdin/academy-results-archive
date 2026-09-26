#!/usr/bin/env python3
"""Grand Prix Challenge sheets with a Bronze Medal Match below the final.
Pull the bronze match out of the page, redact it, parse the rest with an
existing variant, and return the bronze match separately."""
import pymupdf, re
from parse import parse_page, emit_division

def spans(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if s['text'].strip(): out.append((s['bbox'], s['text']))
    return out

def bronze_region(page):
    sp = spans(page)
    bm = [bb for bb, t in sp if 'Bronze Medal Match' in t]
    cl = [bb for bb, t in sp if t.strip() == 'Classification']
    if not bm: return None, sp
    y0 = bm[0][1] + 18
    y1 = (cl[0][1] - 2) if cl else bm[0][1] + 90
    return (bm[0], pymupdf.Rect(300, y0, 545, y1)), sp

def extract_bronze(page, sp, rect):
    inside = [(bb, t.strip()) for bb, t in sp if pymupdf.Rect(bb).intersects(rect)]
    nums = [(bb, t) for bb, t in inside if re.fullmatch(r'\d{3,4}', t)]
    meth = [(bb, t) for bb, t in inside if re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN)', t)]
    # method may be split ('PTF 2:' + '1'): join spans on the method's line
    mline = ''
    if meth:
        my = meth[0][0][1]
        parts = sorted([(bb[0], t) for bb, t in inside if abs(bb[1] - my) < 1.5 and bb[0] >= meth[0][0][0] - 1])
        mline = ''.join(t for _, t in parts)
    no = nums[0] if nums else None
    labs = [(bb, t) for bb, t in inside if re.search(r'\([A-Z]{2,3}\)\s*$', t) and not re.fullmatch(r'\([A-Z]{3}\)', t)]
    ny = no[0][1] if no else None
    side = [(bb, t) for bb, t in labs if ny is not None and abs(bb[1] - ny) < 8]
    left = min(side, key=lambda z: z[0][0]) if side else None
    right = max(side, key=lambda z: z[0][0]) if side else None
    # winner label: spans above the number, centred
    top = sorted([(bb, t) for bb, t in inside if ny is not None and bb[1] < ny - 2 and 395 < bb[0] < 450
                  and not re.match(r'^(PTF|RSC|WDR|DSQ|DQB|PTG|SUP|PUN)', t)], key=lambda z: z[0][1])
    wl = ' '.join(t for _, t in top)
    return dict(no=no[1] if no else None, left=left[1] if left else None,
                right=right[1] if right else None, winner=wl, method=mline)

def parse_gpc_page(page, variant, overrides=None):
    reg, sp = bronze_region(page)
    bronze = None
    if reg:
        bm, rect = reg
        bronze = extract_bronze(page, sp, rect)
        page.add_redact_annot(rect)
        page.add_redact_annot(pymupdf.Rect(bm))
        page.apply_redactions(images=0, graphics=0)
    out = parse_page(page, overrides=overrides, variant=variant)
    return out, bronze

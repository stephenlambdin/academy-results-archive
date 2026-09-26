# The 2026 WT draw-sheet generators — parser notes

Written 2026-09-11 while importing the Muju Grand Prix and Taiyuan Women's Open; revised the same day once the Taiyuan Type3 sheets were cracked, and again after the Swiss Open, Presidents Cup Oceania, Dutch Open and Australian Open. Both are new layouts that the pre-2026 parser could not read. Support lives in `claude/import-parser-parse.py` under **`variant='wt2026'`**; the Type3 decoder is `claude/import-decoder-type3.py`. The older sheets are unaffected (batch 2/3 still parse identically).

## What changed in 2026

Two different producers now appear:

| | Muju Grand Prix | Taiyuan Women's Open |
|---|---|---|
| Producer | Chrome (Skia/PDF) | day 1 Chrome; **days 2–3 Acrobat Distiller 26 / PScript5** |
| Page | 842×619 landscape | 842×595 landscape |
| Score text | `PTF 2 - 0` (spaced dash) | `PTF 2:0` (colon) |
| **Score order** | **winner-first** | **top-feeder-first** |
| Long names | truncated at ~18 chars | printed in full |
| Classification | 3 columns: place ≈ x350, `First LAST` ≈ x359, NOC ≈ x484 | one span, `1<nbsp> NAME (NOC)` ≈ x378 |

### Score order is the dangerous one
Muju prints the **winner's** rounds first regardless of which side of the bracket the winner is on; Taiyuan prints the **top feeder** first. Flipping the wrong one silently produces rows like `CONTI def. AGENJO 0:2`. Verified by counting: across all Muju divisions the printed `a>b` in **234 of 234** decided matches (98 top-wins, 136 bottom-wins); Taiyuan day 1 splits cleanly 73 top-wins `a>b` / 46 bottom-wins `a<b`. Days 2–3 confirmed the same convention independently: the W-73 final prints `PTF 0:2` and the gold medallist (CHAARI) is the **right**-hand finalist. `emit_division(out, score_order='winner'|'top')` — pick it per event and re-run that count as a check. After emitting, every score in the TSV should read winner-first (`2:0`, `2:1`, `1:0`); any `0:2` means the flag is wrong.

For the final, "top feeder" means the **left** side of the bracket.

## What `variant='wt2026'` does
1. **Joins horizontally adjacent fragments within a line** (gap < 3.5pt). The final's winner label arrives as `WILLIAMS` `L` `. (` `GBR` `)`.
2. **Merges rows wrapped onto a second line carrying only the NOC** — entrants (`(1) ZARRINKAMAR ROUDBARI Hana` + `IRI`), labels (`BEKULOVA M.` + `(RUS)`) and classification rows all wrap. The merged row takes the **vertical centre** of the two lines; using the first line's y puts the entrant on the wrong side of its match number and the tree mis-builds.
3. **Merges `SURNAME` + `I.N. (NOC)` split labels** (Taiyuan splits the surname from the initials). The bare-surname pattern must allow a literal `?` — see the diacritics note below.
4. **Assigns labels to match numbers geometrically**, replacing the old side/centre column logic: the match number sits 4–22pt *below* its winner label and within the label's x-span ±30. Rank candidates by **Δy first**, x-distance only as a tie-break — the centre block (both semis and the final at the same y) needs the x tie-break, and a label sitting between two columns needs the Δy one. Methods attach to the label above them (4–32pt).
5. **Division header and body top** are found dynamically (`Contestants` may read `Contestants :`, and the header sits at y≈57, below the old `y < 50` window). Body starts below the round-label row.
6. **Legend detection** also matches `PTF: Win by …` style lines, which sit *above* the `LEGEND` marker.
7. **Final with no winner label** — on the Taiyuan day 2/3 sheets the final's small winner label is simply *not in the text layer* (only the big centre headline is, and that is drawn as vector art). Two fallbacks handle it, both recorded in `out['notes']` rather than as issues:
   - the **gold medallist from the classification block** becomes the final's winner label;
   - the final's `PTF 2:0` span, which has no label to attach to, is adopted as the final's method/score if it sits 2–14pt above the final's match number within ±40pt in x. Any method span still unattached after that is flagged `method-unassigned`.

## Truncated names (Muju only)
44 of 242 entrants print truncated — `ABDUSALAMOV M.`, `PACHECO M.C.`, `RODRIGUES FERNAND.`. **Stephen's call, 2026-09-11: expand them against the archive**, same principle as the Paris 9. `expand()` resolves in this order: the event's Medallists PDF (authoritative, clean `SURNAME First`), then a unique archive match on NOC + surname, then an archive match filtered by given-name initials, preferring a candidate with no trailing period and with the archive's lowercase-second-given-name convention. 43 of 44 resolved; `BATHILY A.K.F.` (CIV) has no archive match and stays as printed.

The **Medallists PDFs are a clean independent podium source** for these events and should always be cross-checked against the parsed podium — all 8 Muju and all 8 Taiyuan podiums matched exactly.

## Taiyuan days 2 and 3 — the Type3 cipher (solved 2026-09-11)

Days 2 and 3 were printed through **Acrobat Distiller 26 / PScript5**, which embeds a **Type3 font with no ToUnicode and meaningless glyph names** (`/Differences [0 /0 2 /1 /2 …]`, `/CharProcs` keyed `/0 /1 /2 …`). Text extracts as raw glyph codes. It is a simple substitution cipher, and it is solvable exactly — do **not** fall back to OCR.

**The method**
1. **Read the content stream yourself.** pymupdf's `rawdict` char positions are wrong inside multi-glyph `Tj` strings (every glyph gets the string's origin), so interpret `Tm` / `Td` / `TD` / `Tf` / `Tj` / `TJ` directly. `claude/import-decoder-type3.py` does this.
2. **Codes are assigned in order of first appearance**, and the subset is **per page**. So one known line of plaintext at the top of a page pins a large block of codes. The title line decodes to: `0x00`=T `0x02`=a `0x03`=i `0x04`=y `0x05`=u `0x06`=n `0x07`=space `0x08`=2 `0x09`=0 `0x0a`=6 `0x0b`=W `0x0c`=o `0x0d`=r `0x0e`=l `0x0f`=d `0x10`=e `0x11`=k `0x12`=w `0x13`=m `0x14`=`'` `0x15`=s `0x16`=O `0x17`=p `0x18`=C `0x19`=h (`0x01` is never used). Codes above ~`0x25` are a **second sub-alphabet** — the bold weight gets its own codes in the same font, so ~104 codes cover roughly two alphabets.
3. **Seed the rest from a screenshot.** Stephen supplied one image per bracket page; transcribing the visible entrant list gives enough aligned plaintext to fill every remaining code. Alignment is mechanical (`dec/learn.py`) — plaintext run against code run.
4. **Result**: all five pages decode with **zero unknown codes**, and the 102 independently transcribed entrants match the decode character-for-character. All 20 medallists match the Medalist PDFs exactly.

**The bug that hid inside this.** The first stream reader took only the *last* string of a `TJ` array (`strs[-1]`). PScript5 emits kerned pairs like `[(7*) 56 (,)] TJ`, so **leading glyphs were being silently dropped** — `MORADI SHEIKHLAR` came out as `RADI SHEIKHLAR` on every one of its eight occurrences, consistently enough to look like a real name. A dropped-glyph bug that is *consistent* will not trip the verification suite. `glyphs()` now emits every string in a `TJ` array in order.

**Literal `?` in the source.** Code `101` on the W-57 page is a genuine `?` glyph: the source PDF prints `MEI?TININKAIT? Gerda` because the Lithuanian `Š`/`Ė` failed in the producer. That is a printing defect, not a decode failure. The archive already holds `MEIŠTININKAITĖ Gerda`, so the import aligns to that (judgment decision 9 in the deployment record). Keep a literal `?` allowed in the bare-surname label regex or the split-label merge fails and the match goes unresolved.

## Martial.Events sheets (DXperience) — `variant='me2026'`

Four 2026 events came from Martial.Events draw-sheet PDFs (producer *DevExpress DXperience v24.1*, sometimes re-wrapped by SAMBox): **Swiss Open, Presidents Cup Oceania, Dutch Open, Australian Open**. They share one layout, and `variant='me2026'` reads all 64 divisions with zero issues.

- The layout is the classic one — entrant column at the page edge, match number, winner label immediately to its **right** on the left half (to its **left** on the right half) at the same y, method/score directly below the label. Match numbers can be 3 or 4 digits.
- **Unseeded athletes print with no `(x)` prefix** — just `TRABELSI Amen allah TUN`. The base parser then finds only the seeded entrants and the whole tree collapses into `no feeders` / `label-no-match` noise; that symptom is the tell. The bare-entrant rule (`x < 120` or `x > width − 200`), inherited from `me2025`, is what fixes it.
- **Score order is top-feeder-first** on all four. Always confirm with the count; Swiss 79/59, Oceania 111/85, Dutch 252/231, Australian 104/98, no contradictions in any.
- A `RSC 1 - 1` is legitimate — a referee stoppage can land on an even round score, so the "every score reads winner-first" check applies to PTF, not to RSC/WDR/DSQ.
- Some matches print a winner label and **no method or score at all** (15 across batch 11, 2 in Swiss). Record both blank rather than guessing; check the PDF before assuming it is a parser fault.
- One division header per page, `Seniors / Men -58kg   Contestants: 19`. The same file may carry cadet, junior, senior and Para pages — select the page range deliberately. A Medalist table is sometimes bundled as the first pages (Dutch pages 1–2); **always cross-check it**.

### Two bugs `me2026` exists to fix

Both were found on the Dutch Open and both are the quiet kind — they produce plausible output, not an error.

1. **Label and method are right-aligned on the right half of the bracket**, not left-aligned. Pairing them on `x0` (as `me2025` does, with a loose `|Δx| < 80` fallback) lets a neighbouring column's method reach a label first and claim it: Dutch M-58 match 305 printed `PTF 2 - 0` but received match 315's `PTF 0 - 2`, silently reversing a score. `me2026` pairs on a **shared edge** — `min(|lx − x|, |lx1 − mx1|) ≤ 3.5` with `0 < Δy < 14` — which is exact on both halves. The single `topwin / a<b` entry in the score-order count is what exposed it; that count is the check that catches this class of error.
2. **The classification-row filter was swallowing right-half labels.** The base parser drops anything below the `Classification` heading in `360 < x < 510`; the Dutch M-87kg match 825 label sits at x=509.8 and vanished, taking its method with it. `me2026` narrows the window to `340 < x < 465`, which is the column the classification rows are actually printed in (`x0 = 346.4` on every one of these sheets).

The already-imported **Swiss Open was re-parsed under `me2026` and came out byte-identical** — its right-half labels happen to sit at x=538, clear of both traps — so no correction was needed. Re-run the previous event after any change here; that is what established this.

## WT results system sheets from the ETU: `variant='etu2026'` (added 2026-09-26)

First seen on the **2026 Multi European Games** (Niš). The ETU posts senior results as `P11-Competition-Draw-Sheets.pdf` and `P14-Medallists-by-Weight-Category.pdf`, produced by **ActiveReports 19** (the WT results system). Page 842x595, one division per page, header `Men -54kg     Contestants: 31`, date `SUN 13 SEP 2026`. The bracket geometry is the Martial.Events one (label beside the match number, method directly under the label, right half right-aligned), so `etu2026` is `me2026` plus a span pre-pass and three tolerances.

- **Entrants print NOC-first**: `(1) TUR YELALDI Kaan`, and unseeded ones with a leading space, ` GBR DONE Cameron`. `etu_spans()` rewrites them to `NAME NOC` so the existing entrant rules apply.
- **Byes print as `Free draw`** in the entrant slot and have no match number. Dropping the span is enough: the seeded athlete's node simply feeds the next round's match.
- **Final method sits about 22pt above the final number**, outside the old 14pt orphan window. `etu2026` widens it to 30pt.
- **Long right-half labels overflow their right edge by about 3.6pt** (`HOSSEINI BIJI KOLA S. (BUL)`), just past the 3.5pt shared-edge rule. `etu2026` allows 4.5pt; columns are 55pt apart, so nothing can be stolen.
- **Names starting with Latin Extended letters** (`CRO ĐODAN Ivan`) were missed by the bare-entrant regex (`À-Þ` stops at U+00DE). `etu2026` adds `Ā-ž`.
- **Decimal match numbers** (`548.1`, `942.3`) are printed for a handful of contests and are kept as printed. Sort matches with `float()`, not `int()`.
- Second given names print in Title Case (`ELIA Luigi Antonio`), unlike the archive's lowercase convention; expect case-only clashes and flag them.
- Score order is top-feeder-first, same as Martial.Events. Confirmed: zero loser-first scores across 442 matches.
- All three tolerances are gated on `etu2026`, so `me2026` output is unchanged (German Open regression byte-identical).

**Fetching.** `europetaekwondo.org` sits behind a SiteGround bot check. `curl` from the container gets a challenge page instead of the PDF; a normal browser (Cowork's Chrome) downloads the files directly. `web_fetch` with PDF text extraction also works for reading, but gives no coordinates.

## taekwondo.tv as a source (checked 2026-09-26, not used)

`https://taekwondo.tv/api/tournaments/<id>/brackets` lists divisions and `/brackets/<bracketId>` returns every match as JSON, and it is reachable from the container. It is useful for finding events and checking field sizes, **but it is not an import source**: names are reversed to `Given SURNAME` with only the last word capitalised (double surnames are lost), methods are missing, and some NOCs come back as country names. Nations Cup 2026 was held on this basis.

## Browser leg — the recurring blocker
The Chrome window must be **in the foreground**. When it is backgrounded, synthetic input stops working: Google Sheets ignores `Cmd+V` (this blocked the Fujairah paste on 2026-08-16), `Tab` does not move focus, and GitHub rejects a commit whose summary was set via JS with *"You can't perform that action at this time."*

- `document.visibilityState` is **not a reliable signal** — it stayed `"hidden"` through the entire successful batch-9 paste. `document.hasFocus()` was `true` and everything worked. Test by clicking a field and checking `document.activeElement`.
- `navigator.clipboard.readText()` returns **empty** in this state even when the write succeeded, so **do not use readback as verification**. Write with a hidden `<textarea>` + `document.execCommand('copy')` (which reports success), paste, then verify with gviz counts.
- The guard-row technique is what actually protects the paste: prepend a copy of the current last data row and anchor there. If the clipboard were empty the paste is a no-op and the counts do not move — harmless and detectable.

Reading (gviz, the GitHub API, `raw.githubusercontent.com`) works fine either way, and the container **can reach `docs.google.com`** directly, so sheet *reads* never need the browser. Writes still do.

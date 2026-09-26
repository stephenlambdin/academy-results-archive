# Academy Results Archive — Deployment Record

Deployed 2026-08-03 per BUILD_GUIDE.md. **Fifty-one events live as of 2026-09-26** after batch 14 (2025 Dutch Open, Belgian Open, Muju GPC, Presidents Cup Pan Am, Bangkok GPC) was pasted that day, following batches 12 and 13 (German Open, Multi European Games) earlier the same day; the 2026 U.S. Season Final was added outside these sessions. Forty-three events were live as of 2026-09-11 (batch 8: Taiyuan Women's Open day 1 + Muju Grand Prix; batch 9: Taiyuan days 2–3, completing that event; batch 10: Swiss Open; batch 11: Presidents Cup Oceania, Dutch Open, Australian Open). Events page has collapsible year grouping; podium/entry/match rows use uniform NOC + medal columns. The site nav now carries a third view, **ACADEMY ATHLETES**, added outside these import sessions.

## Live system
- **Site**: https://stephenlambdin.github.io/academy-results-archive/
- **Repo**: https://github.com/stephenlambdin/academy-results-archive (public, GitHub Pages from `main` / root)
- **Database**: Google Sheet "Academy Results Archive", Sheet ID `16--LTisSbdw9xpA-dTtN40EiEaf5_bdmjQHI2Czf6Lg`, "Anyone with the link: Viewer"; tabs README / Events / Results / Matches / Roster.
- Import staging TSVs live in repo `data/` (`Batch2_*` … `Batch11_ME3_*`; deletable).

## Conventions (confirmed against live sheet)
- Event Name = "Year Name", official-style, **no G-grade in the name**. Grade goes in the **Level** column: "International, G1/G2", "Grand Prix", "Grand Prix Challenge", "National", "Team Trials", "World Championships", "Club Championships", "Presidents Cup", "University Games", "Olympic Games".
- Never include "Kyorugi". Locations "City, Country". Start Date = earliest printed day, real date cells.
- Divisions: `Senior Men -68kg` etc.; U21 events labeled `U21 Men -54kg`. European Senior Olympic uses its printed Olympic categories (+80/+67).
- Names/match numbers as printed; **scores winner-first `2:0`** — see the score-order warning below; 0-0 walkover scores blank; parenthetical round/time annotations dropped; `.WT` → `WT`.
- **Domestic (US Nationals / Team Trials)**: names as printed by Martial.Events (mixed case, first-name-first), NOC `USA`, weight-bracket names mapped to standard divisions. Runs of spaces inside names collapsed to one.
- **Round codes**: R256, R128, R64, R32, R16, QF, SF, F, plus **RPC** (Olympic repechage) and **BRZ** (Olympic bronze contest), plus **BR** (a single Bronze Medal Match between the two SF losers, as on the 2025 Grand Prix Challenge sheets; added batch 14). `ROUND_ORDER` in index.html sorts BR between SF and F (`BR:6.5`); RPC/BRZ are still not in the map and sort *after* the final.
- **Bronze Medal Match placements**: the BR winner gets 3 in Results; the BR loser's placement is blank (Stephen, 2026-09-26).
- **Method codes**: PTF, PTG, GDP, SUP, PUN, RSC, DSQ, DQB, WDR. Olympic sheets print `WWD` — normalised to WDR.

## ⚠️ Score order differs by generator
The 2026 sheets do **not** all print the score top-feeder-first. Muju prints the **winner's** rounds first; Taiyuan prints the **top feeder** first (and for the final, "top" means the **left** half of the bracket). `emit_division(out, score_order='winner'|'top')` — set it per event and verify. **After emitting, every score in the TSV must read winner-first (`2:0`, `2:1`, `1:0`); a single `0:2` means the flag is wrong.** Details and the counting check in `claude/import-2026-generator-notes.md`.

## Current contents (as of 2026-09-26, after batch 14)
Site header: **51 events · 6,722 athletes · 14,894 results**. Sheet: 51 Events, 14,899 Results rows, 13,511 Matches rows. (Site Results runs 5 below the sheet, the long-standing same-name collapses, unchanged by batches 5 to 14.)

Batch 1 (8): 2023 Baku Worlds · 2025 Wuxi Worlds · 2026 Belgian Open · 2026 British Open · 2026 Pan Am Championship · 2026 Roma Grand Prix · 2026 US Nationals · 2026 Chuncheon Korea Open.

Batch 2 (9, 2026-08-13): 2025 Dracula Open · 2025 European Senior Olympic Weight Categories · 2025 Nairobi U21 Worlds · 2026 Canada Open · 2026 U.S. Open · 2026 Dominican Open · 2026 Solidarity Center Open · 2026 FISU America Games · 2026 Portugal Open.

Batch 3 (11, 2026-08-14): 2025 Canada Open · 2025 U.S. Open · 2025 WT Presidents Cup Africa · 2025 Spanish Open · 2025 Asian Club Championships · 2025 Swedish Open · 2025 Rio Open · 2025 Charlotte Grand Prix Challenge · 2025 African Club Championships · 2025 U.S. Under 21 Team Trials · 2025 U.S. National Championships.

Batch 5 (1, 2026-08-16): **2026 Kazakhstan Open** — 16 divisions, 334 athletes, 318 matches, from a markdown transcription of the WT results system. Match No blank throughout.

Batch 6 (2, 2026-08-16): **2024 U.S. National Championships** (16 divisions, 155 athletes, 139 matches; only pages 1–16 of the PDF are senior and in scope) · **2024 Paris Olympic Games** (8 divisions, 134 athletes, 158 matches incl. 16 RPC + 16 BRZ).

**Added between 2026-08-16 and 2026-09-11, outside these sessions** (present in the sheet, provenance not recorded here): 2026 Presidents Cup Pan Am · 2026 American Open East · 2026 American Open West · 2025 Presidents Cup Asia · 2026 Asian Taekwondo Indonesia Open · 2026 El Hassan International Open.

Batch 8 (2, 2026-09-11):
- **2026 Taiyuan World Taekwondo Women's Open Championships** — `taiyuan-womens-open-2026`, 2026-08-28, Taiyuan China, International (grade not printed). Day 1: W-46, W-62, W+73 — 122 athletes, 119 matches.
- **2026 Muju Taekwondowon World Taekwondo Grand Prix** — `muju-grand-prix-2026`, 2026-09-05, Muju Korea, Grand Prix. All 8 Olympic divisions, 242 athletes, 234 matches. All 8 podiums cross-checked against the Medallists PDFs and matched exactly.

Batch 9 (0 new events, 2026-09-11): **Taiyuan days 2 and 3** — the five remaining divisions (W-49 41, W-53 43, W-57 48, W-67 42, W-73 35), **209 athletes, 204 matches**, appended to the existing Taiyuan event. Taiyuan is now **complete at 8 divisions, 331 results, 323 matches**. The Type3-font problem that blocked these on 2026-09-11 was solved rather than worked around — see the generator notes. Files: `data/Batch9_Taiyuan_D23_{Results,Matches}.tsv` (no Events row; the event already existed).

Batch 10 (1, 2026-09-11): **2026 Swiss Open** — `swiss-open-2026`, 2026-09-04, St. Gallen Switzerland, International G1. The 2nd Swiss Open Kyorugi, 4–6 September 2026; seniors ran Sunday 6 September. **16 senior divisions, 163 athletes, 147 matches.** Source: the single 54-page Martial.Events draw-sheet PDF (`Results-Competition-Draw-Sheets.pdf`), pages 36–51. Parsed with **`variant='me2025'` unchanged** — the DXperience/Martial.Events international layout is the same one the 2025 U.S. Open uses. Files: `data/Batch10_SwissOpen2026_{Events,Results,Matches}.tsv`.

Batch 11 (3, 2026-09-11) — all three from Martial.Events draw-sheet PDFs, all senior-only files, all parsed with the new **`variant='me2026'`**:
- **2026 Presidents Cup Oceania** — `presidents-cup-oceania-2026`, 2026-06-18, Gold Coast Australia, Presidents Cup (G3). 16 divisions, 218 athletes, 202 matches.
- **2026 Dutch Open** — `dutch-open-2026`, 2026-03-15, Eindhoven Netherlands, International G1. The 53rd Dutch Open; seniors ran Sunday 15 March. 16 divisions, **512 athletes, 496 matches — the largest event in the archive.** All 64 medallists cross-checked against the Medalist table on pages 1–2 of the same PDF: exact match.
- **2026 Australian Open** — `australian-open-2026`, 2026-06-20, Gold Coast Australia, International G2. 16 divisions, 232 athletes, 216 matches. Shares the Gold Coast Sports and Leisure Centre with the Presidents Cup two days earlier.

Files: `data/Batch11_ME3_{Events,Results,Matches}.tsv` (all three events in one set of files).

**Added between 2026-09-11 and 2026-09-26, outside these sessions:** 2026 U.S. Season Final (`us-season-final-2026`, National). Sheet stood at 44 Events, 12,357 Results, 11,049 Matches on 2026-09-26 before batches 12 and 13.

Batch 12 (1, pasted 2026-09-26): **2026 German Open**, `german-open-2026`, 2026-09-20, Hamburg Germany, International G1. Senior day was Sunday 20 September (cadets and juniors ran the 19th). **16 divisions, 300 athletes, 284 matches.** Source: DTU drawsheets-results page, `GO-2026_Results_Draw-Sheet.pdf` pages 41 to 56 (Martial.Events / DXperience), parsed with **`variant='me2026'` unchanged**, score order top. All 64 medallists match `GO-2026_Medalists.pdf` exactly. Files: `data/Batch12_GermanOpen2026_{Events,Results,Matches}.tsv`.

Batch 13 (1, pasted 2026-09-26): **2026 Multi European Games**, `multi-european-games-2026`, 2026-09-13, Niš Serbia, International G1 (seniors G1, juniors and cadets E2). Senior day was Sunday 13 September. **16 divisions, 458 athletes, 442 matches.** Source: ETU documents page, `P11-Competition-Draw-Sheets.pdf` (WT results system, ActiveReports 19), parsed with the new **`variant='etu2026'`**, score order top. All 64 medallists match `P14-Medallists-by-Weight-Category.pdf` exactly. Files: `data/Batch13_MultiEuropeanGames2026_{Events,Results,Matches}.tsv`.

All batch 12 and 13 divisions pass the full rule 4.04 suite with zero issues.

Batch 14 (5, pasted 2026-09-26). Stephen asked for these by name; all five pass rule 4.04 with zero issues.
- **2025 Dutch Open**, `dutch-open-2025`, 2025-03-08, Eindhoven Netherlands, International G1. 16 divisions, 556 athletes, 540 matches. Martial.Events draw sheets, `variant='me2025'` with overrides for matches 846, 246 (M-58/p11) and 605 (p13). W-53 podium taken from the bracket because the classification NOC is truncated. W-67 #1210 prints `0:2` with CASTRO BURGOS as winner; stored `2:0`.
- **2025 Belgian Open**, `belgian-open-2025`, 2025-03-15, Lommel Belgium, International G1. 16 divisions, 308 athletes, 292 matches. Martial.Events, pages 3 to 18, override on #604. All 64 medallists match the Medalist table on pages 1 to 2.
- **2025 Muju Taekwondowon World Taekwondo Grand Prix Challenge**, `muju-grand-prix-challenge-2025`, 2025-08-28, Muju Korea, Grand Prix Challenge. 8 divisions, 311 athletes, 311 matches (includes 8 BR bronze matches). WT KPNP sheets need their own reader, `claude/import-parser-kpnp.py` (NOC-first entrants, labels above and method below the box, mirrored SF labels). Names clip at ~18 characters: 72 expanded (Medallists PDF first, then the archive), about 11 left as printed where nothing matched (e.g. `BEN ELBACARIA Ah`, `NOAH BEKADA Flori`, `GROSSI Sophia Cleli`). Podiums match the Medallists PDF.
- **2025 Presidents Cup Pan Am**, `presidents-cup-america-2025`, 2025-09-06, Lima Peru, Presidents Cup. 16 divisions, 404 athletes, 388 matches. Stephen's call: **names from the official PATU draw sheet, winners and round scores from taekwondo.tv** (tournament 36) joined on match number; Method blank throughout (tv carries none). Five matches where the tv winner flag contradicts bracket progression (M-80 #1003, M-74 #906, M+87 #728, W-57 #731, W-49 #627) take the progression winner with a blank score. 22 long names expanded. Podiums match the official medallist PDF. Script: `claude/import-batch14-panam.py`.
- **2025 Bangkok World Taekwondo Grand Prix Challenge**, `bangkok-grand-prix-challenge-2025`, 2025-11-21, Bangkok Thailand, Grand Prix Challenge. 8 divisions, 205 athletes, 205 matches (8 BR). WT results system sheets via the new `variant='gpc2025'` plus `claude/import-parser-gpc.py` for the Bronze Medal Match. M+80 bronze #213 prints `PTF 1:2` with KIM Woojin as winner; stored `2:1`. M-80 podium from the Medallists PDF.

Files: `data/Batch14_{DutchOpen2025,BelgianOpen2025,MujuGPC2025,PresidentsCupPanAm2025,BangkokGPC2025}_{Events,Results,Matches}.tsv`; paste blocks in `paste/Paste_*_Batch14.tsv`. WT SimplyCompete had no draws for these events (as Stephen expected); the WT results site (`downloadZip`, boards per division) and taekwondo.tv were the sources.

All batch 8, 9, 10 and 11 divisions pass the full rule 4.04 suite with zero issues, and all 8 Taiyuan podiums match the Medalist PDFs exactly. Parser support is `variant='wt2026'` in `claude/import-parser-parse.py`; the Type3 decoder is `claude/import-decoder-type3.py`; the format work is written up in **`claude/import-2026-generator-notes.md`** — read that before touching a 2026 sheet.

## Judgment decisions (Stephen approved)
1. **U21 M-63 match 210** (batch 2): recorded TLEULES def. YASER, method/score blank.
2. **FISU M-80 classification misprint** → podium from bracket: 1 MOSTELLER, 2 CORNELL, 3 ROMMEL, 3 GRANADOS.
3. **FISU W-46**: printed bronze to AVELLANEDA (QF loser) kept as printed per rule 4.04.
4. **Presidents Cup Africa W-73 ran twice**; both imported, day-3 rows ordered first so its placements win the read-time dedup.
5. **NICKOLAS resolved** — canonical `NICKOLAS CJ`; the US Open and Muju print `NICKOLAS Cj`, kept as printed (site matches case-insensitively).
6. **Kazakhstan Open NOCs kept as printed — RUS and BLR, not AIN** (2026-08-16). 28 athletes consequently hold two cards. A single find-and-replace on the NOC column would unify them if it ever matters.
7. **Paris 2024 name-spelling exceptions** (2026-08-16) — 9 athletes aligned to the archive's existing spelling rather than kept as printed. List in the previous revision of this doc and in the Paris notes; the four EOR athletes deliberately keep EOR.
8. **Muju truncated names expanded** (2026-09-11). The Muju sheets clip names at ~18 characters; 44 of 242 entrants printed as `ABDUSALAMOV M.`, `PACHECO M.C.` etc. Stephen's call: **expand against the archive** rather than keep as printed. 43 of 44 resolved. `BATHILY A.K.F.` (CIV) has no archive match and stays as printed.
9. **Taiyuan W-57 `MEI?TININKAIT? Gerda` (LTU)** (2026-09-11, batch 9). The source PDF prints literal question marks — the Lithuanian `Š`/`Ė` failed in the producer, so this is a printing defect, not a decode error. The archive already holds `MEIŠTININKAITĖ Gerda` from an earlier event, so the three batch-9 rows use that spelling (same principle as decision 7). The archive still contains two older `MEI?TININKAIT? Gerda` rows from a previous import; a find-and-replace would unify them.

10. **Swiss Open cadets, juniors and Para excluded** (2026-09-11). The PDF carries 54 pages: 16 cadet, 19 junior, 16 senior kyorugi and 3 Senior K44 Para divisions. Cadets and juniors fall outside the archive's senior/U21 scope. Stephen's call on the Para divisions (K44 Men -58/-70/+80kg, 9 athletes, 6 matches): **skip** — Para taekwondo is a separate discipline and the archive holds no Para rows, so importing them would set a new precedent. The pages are there if that changes.
11. **Swiss Open `GARCIA Angel  jesus` (SUI)** — printed with a double space; collapsed to one, per the existing whitespace convention. Everything else kept exactly as printed, including `TRT` (Taekwondo Refugee Team) NOCs and the diacritics in `ĐOKOVIĆ Ines` (SRB).
12. **Swiss Open matches 601 (M-58) and 701 (M-63)** print a winner label but **no method and no score**. Recorded with both fields blank, same as decision 1.

13. **Start Date for a part-of-event draw sheet** (2026-09-11). Several 2026 files cover only the senior day of a multi-day event. Stephen's call: **use the date printed in the source**, so the event date always corresponds to rows that are actually in the archive — Dutch 2026-03-15 (event ran 14–15 March), Oceania 2026-06-18 (17–19 June), Australian 2026-06-20 (19–21 June). The **Swiss Open was corrected from 2026-09-04 to 2026-09-06** at the same time for consistency.
14. **Dutch Open given-name capitalisation** (2026-09-11). Five entrants are already in the archive under a different capitalisation: the Dutch sheets print `SILVA RICARDO`, `MARTINHO MANUEL`, `OSSIN KIMI LAURENE`, `FARNES Ricki gene`, `NAVARRETE Fabricio Antonio`. Stephen's call: **align to the archive** (`SILVA Ricardo`, `MARTINHO Manuel`, `OSSIN Kimi laurene`, `FARNES Ricki Gene`, `NAVARRETE Fabricio antonio`) — same principle as decisions 7 and 8. The all-caps forms would otherwise read as part of the surname and split each athlete across two cards. Note `OSSIN` already had two archive forms; the `SURNAME First given` one was chosen.
15. **Fifteen batch-11 matches print a winner label and no method or score.** Recorded with both blank, same as decision 12. Verified against the PDFs — nothing is printed near those match numbers.

16. **German Open 2026 kept exactly as printed** (2026-09-26, Stephen: "Add it"). That covers `A AJ` (USA, Men -74kg; the same unidentified athlete stored at El Hassan as `A Aj`), `HABULIN Kim vivian` (archive has `HABULIN Kim Vivian`), `JELIĆ Matea` (archive has `JELIC Matea`), and the printed NOCs `KAZLOU Yahor` / `SHADZEUSKI Yauheni` BLR (AIN elsewhere) and `AMINI Mohammad ramin` GER (AFG elsewhere). Each will show as a second athlete card until normalised.
17. **German Open matches with no method or score**: -58 #407, -63 #512, -80 #508, W-57 #308, W-62 #802, W-67 #805, W-73 #602 print a winner label only. Recorded blank, same as decision 15.
18. **Multi European Games imported as printed, pending Stephen's calls** (see Open items). The sheet uses WT-system Title Case for second given names, prints RUS and BLR rather than AIN, and prints eight decimal match numbers (`548.1`, `942.2`, `441.1`, `137.1`, `942.1`, `942.3`, `437.1`, `437.2`), kept as printed. W-67 SF #439 prints `WDR 1-1` and is stored `1:1`; W-67 #407 is a `DSQ 0-0`, stored with blank score.

## Checked and deliberately not imported
- **2026 Nations Cup** (G1, Quito Ecuador, 12 to 13 September). **Stephen's call, 2026-09-26: hold until the Ecuadorian federation posts official draw sheets.** The only source found is taekwondo.tv, which reverses names (`Jared Esteban Vargas VERA`), capitalises only the last word, and carries no methods. The senior field is small: 14 divisions, 50 athletes, 36 matches.
- **13th Fujairah Open 2026** (G-2, Feb 2026, Fujairah UAE). No senior results exist in any public source — the organiser never uploaded to the WT results system. **Stephen's call, 2026-08-16: skip entirely — no Events row.**
- **2025 Fujairah Open** (12th, G-2, 9–13 Feb 2025). Fully parsed and verified on 2026-08-16 — 16 divisions, 460 athletes, 444 matches, zero issues, both medal tables in the source reconciled exactly. TSVs are committed at `data/Batch7_Fujairah2025_*.tsv` but the sheet paste was blocked at the time (see the browser note below). **Stephen's call, 2026-09-11: skip.** If it is ever wanted, the files are ready and only need the three pastes.

## Import tooling (project docs, reusable)
- **`claude/import-parser-parse.py`** — standard WT draw sheets, plus `variant='me2025'` (2025 U.S. Open Martial.Events), **`variant='wt2026'`** (both 2026 WT generators) and **`variant='me2026'`** (2026 Martial.Events / DXperience — Swiss, Oceania, Dutch, Australian).
- **`variant='gpc2025'`** (batch 14) reads the 2025 WT Grand Prix Challenge sheets: `wt2026` plus a wrap-merge for entrants whose second line is `Given NOC`. `parse()` also accepts `overrides` on the final. Regression: German Open, MEG, Dutch 2025 and Bangkok byte-identical.
- **`claude/import-parser-kpnp.py`** (batch 14): WT KPNP sheets (Muju GPC 2025). **`claude/import-parser-gpc.py`**: Bronze Medal Match reader for GPC sheets. **`claude/import-batch14-panam.py`**: PATU draw + taekwondo.tv join.
- **`variant='etu2026'`** (added 2026-09-26) reads the WT results system / ActiveReports sheets the ETU publishes. It pre-processes spans (NOC-first entrants, `Free draw` byes) and then runs the `me2026` geometry. Regression: German Open under `me2026` and Multi European Games under `etu2026` both reproduce byte-identical output with the new file.
- **`claude/import-decoder-type3.py`** — content-stream glyph reader + span builder for Acrobat Distiller / PScript5 sheets whose text is a Type3 substitution cipher. Needed for Taiyuan days 2–3 and for any future sheet that extracts as gibberish.
- **`claude/import-parser-domestic.py`** — Martial.Events domestic sheets. Ran unmodified on the 2024 sheets.
- **`claude/import-parser-olympic.py`** — Olympic draw sheets with repechage.
- **`claude/import-parser-run_all.py`** — rule 4.04 verification suite + event config with `overrides` / `podium_override` hooks.
- **`claude/import-2026-generator-notes.md`** — the 2026 layouts, the score-order trap, truncated-name expansion, and the Taiyuan Type3 decode.
- **Markdown bracket documents** (Kazakhstan, Fujairah) need no PDF parser — a ~40-line reader over the `| **Winner** (NOC) | def. | Loser (NOC) | 2–1 PTF |` tables, asserting each round's declared match count, then the standard verification suite.
- **Always cross-check the parsed podium against the event's Medallists/Medalist PDF** when one exists. It is an independent source in clean `SURNAME First` form and costs nothing.
- **Cross-check entrant names against any screenshot the user supplies.** On Taiyuan days 2–3 the 102 transcribed entrants confirmed the decode character-for-character — and a *consistent* glyph-dropping bug (`MORADI` → `RADI` in all eight occurrences) is invisible to the verification suite, so this is the only check that catches it.
- **Regression discipline**: after any parser change, re-run the previous batch and diff against a saved baseline. The `wt2026` work was checked against Muju and Taiyuan day 1 after every edit.

## Import mechanics (browser leg)
- TSVs to /mnt/user-data/outputs → GitHub upload page (`/upload/main/data`) file input via claude-in-chrome `file_upload` → commit to main → in the Sheets tab: fetch the raw.githubusercontent URL + copy to clipboard (block starts with a copy of the current last data row) → Name Box → anchor → Cmd+V.
- **Anchor arithmetic**: gviz `select count(A)` with `headers=1` returns *data* rows. Last data row = `count + 1`; the guard-row paste anchors there, a plain append goes to `count + 2`. Getting this wrong overwrites the previous event's last row.
- **Copy to the clipboard with a hidden `<textarea>` + `document.execCommand('copy')`**, not `navigator.clipboard.writeText`. And **never verify with `clipboard.readText()`** — it returns empty in this environment even when the copy succeeded. Verify the *paste* instead, with gviz counts and a guard-row-duplication check.
- **The Chrome window must be in the foreground.** When it is backgrounded, synthetic input silently fails: Sheets ignores `Cmd+V`, `Tab` does not move focus, and GitHub rejects a JS-populated commit form with *"You can't perform that action at this time."* This blocked the Fujairah paste on 2026-08-16 and a first attempt on 2026-09-11. `document.visibilityState` stays `"hidden"` even when everything is working — **do not trust it**; `document.hasFocus()` and a click-then-check-`activeElement` test are the reliable signals.
- **Read the screenshot's coordinate frame from the tool output** (it reported `1512x801` on 2026-09-11, not the 1568 assumed earlier) and scale DOM rects by `frame_width / window.innerWidth`. Mis-scaled clicks were the single biggest time sink across these sessions.
- Type the commit summary with **real keystrokes** after confirming `#commit-summary-input` is `document.activeElement`; setting `.value` from JS trips GitHub's guard.
- After committing, `api.github.com/.../contents/data` can lag by a minute — `raw.githubusercontent.com` updates first, so confirm there.
- Verify each paste with gviz counts *and* a guard-row-duplication check before moving to the next tab.
- **The container can reach `docs.google.com` directly**, so all sheet *reads* (gviz CSV, `select count(A)`) can be done with curl from bash — no browser needed. Writes still need the browser.

## Open items
- **Batch 14 pasted 2026-09-26.** Verified: totals 51 / 14,899 / 13,511; per event Dutch 1/556/540, Belgian 1/308/292, Muju 1/311/311, Pan Am 1/404/388, Bangkok 1/205/205; every pasted row equals its source TSV; start dates are real dates; site header shows 51 events.
- **Batch 14 case-only clashes** (kept as printed, Stephen to decide): Dutch 2025 `FARNES Ricki gene`, `KARMELY Lea anais`; Muju GPC many TPE/KOR hyphenated given names (e.g. `CHEN Pen-Ren`) and `PACHECO Maria Clara`; Pan Am `GRIPPOLI Maria Sara`, `PACHECO Maria Clara`, `SOUZA Daniela Paola`.
- **Muju GPC 2025 truncated names left as printed** (~11, no source to expand from): `BEN ELBACARIA Ah`, `dos SANTOS de ASSI`, `NOAH BEKADA Flori`, `NTYAM LEVODO Da`, `ESCOLAR PARRA Iva`, `SALANOVA LISTE Adr`, `ALBAKER Abed Almaj`, `AL HARBI Mohamme`, `GOMES PEREIRA M`, `RUKUNDO Guy Gerli`, `GROSSI Sophia Cleli`.
- **Batches 12 and 13 were pasted 2026-09-26** (handoff `HANDOFF_Batch12-13.md`). Verified: totals 46 / 13,115 / 11,775; per event 1/300/284 and 1/458/442; every pasted row matches its source TSV exactly; one US Season Final guard row at each anchor; start dates stored as real dates.
- **Multi European Games calls for Stephen** (imported as printed until he decides):
  - 11 case-only clashes with the archive: `AYDOGAN Hamza Osman`, `BOUROGIANNI Konstantina Eleni`, `CEYLAN Ahmet Bogachan`, `DASGIN Elif Eylul`, `ELIA Luigi Antonio`, `KAVUKCUOGLU Zehra Begum`, `KESGIN Tuvanna Nazli`, `LAMPIS Filippo Maria`, `TURAN Sila Zeynep`, `YILMAZ Damla Nur`, `ZENOZI Kimia Alizadeh`. The archive holds each with a lowercase second given name.
  - Cross-batch: `YIGITALP Hatice Pinar` (MEG) against `YIGITALP Hatice pinar` (German Open).
  - Five Russian athletes print RUS here and AIN elsewhere; `KLARIC Tianna` prints SLO here and GBR in the archive.
  - `VARGA V Iktoria` (CRO, W-49) is almost certainly a misprint of Viktoria.
- **`A AJ` / `A Aj`** (USA): identity still unknown; now appears at El Hassan and the German Open.
- **2026 Nations Cup**: waiting on official draw sheets.
- **2025 Solidarity Open** and **2025 Niger Open** — listed in the batch-3 upload but the files never arrived; re-upload to import.
- **Match No blank** for all web-sourced rows: Roma M-58/W-49 (59), Kazakhstan (318), Paris (158).
- Location cells blank (not printed) on a number of events; Level "(grade not printed)" on Dracula, Solidarity, Portugal, Spanish, Swedish, and Taiyuan.
- Two legacy `MEI?TININKAIT? Gerda` (LTU) rows predate decision 9 and could be normalised to `MEIŠTININKAITĖ Gerda`.
- Automation five-event trial still to run (every batch so far went through chat import, not the Drive inbox).
- Consider adding RPC/BRZ to `ROUND_ORDER` in index.html so Olympic match logs read chronologically.

## Known limits
- Same-name athletes in one division collapse to one entry.
- Public repo + link-view sheet = public data; team-only needs a private repo + Pages access control.
- Brand questions on public content → media@usatkd.org.

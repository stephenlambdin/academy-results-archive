# USATKD National Academy, Results Archive

A static front end for the Academy results database. The database is a Google Sheet; this site reads it and never writes to it. Scope: senior black belt kyorugi, including U21 divisions, national and international events.

## One-time setup

1. **Create the sheet.** In Google Sheets: File, Import, Upload, choose `Academy_Results_Archive_Sheet.xlsx`, and select "Replace spreadsheet." Keep the tab names exactly `Events`, `Results`, and `Matches`.
2. **Share it.** Share, General access, "Anyone with the link," role "Viewer."
3. **Connect the site.** Copy the Sheet ID from the sheet URL (the long string between `/d/` and `/edit`) and paste it into the `SHEET_ID` constant near the top of `index.html`.
4. **Add the photos.** Unzip `photos.zip` so the repo contains a `photos/` folder next to `index.html` (13 Academy headshots, named by member number).
5. **Publish.** Push this folder to a GitHub repository and enable GitHub Pages (Settings, Pages, deploy from branch, root). The site appears at `https://<user>.github.io/<repo>/`.

## Academy athlete photos

The sheet's `Roster` tab lists Academy athletes: Display Name, Member No, Gender, NOC, and Photo (a filename inside `photos/`). The site shows the headshot beside an athlete's name when the NOC matches and every word of the roster Display Name appears in the name printed on the draw sheet, so "CJ Nickolas" matches "NICKOLAS CJ" and "Ethan Gun" matches "GUN Youngsuk ethan." To add an athlete: add a Roster row and commit their 240x240 circular PNG to `photos/`.

## Duplicate protection

Multiple coaches can add data without coordinating. The site de-duplicates on read: events with the same EventID, or the same Event Name and Start Date, are merged into one; repeated Results rows (same event, division, athlete) and repeated Matches rows (same event, division, round, winner, loser) collapse to a single entry, preferring the row that carries a placement. Claude also generates the EventID deterministically from the event name and date, so two coaches importing the same PDF produce identical rows. Duplicate rows left in the sheet are harmless and can be tidied whenever convenient.

## Adding an event

1. Upload the results PDF or screenshots in the Claude project chat.
2. Claude returns rows formatted for the `Results` and `Matches` tabs.
3. Check the rows against the official results (rule 4.04: every score, placement, and medal must match), then paste them into the sheet.
4. Refresh the site. No redeploy is needed; the site reads the sheet live.

## Data model

| Tab | Columns |
| --- | --- |
| Events | EventID, Event Name, Start Date (YYYY-MM-DD), Location, Level |
| Results | EventID, Division, Athlete, NOC, Placement (1, 2, 3, or blank) |
| Matches | EventID, Division, Round, Match No, Winner, Winner NOC, Loser, Loser NOC, Method, Score (winner first) |

Round codes: R64, R32, R16, QF, SF, F. Method codes: PTF (final score), RSC (referee stops contest), WDR (withdrawal), DSQ (disqualification), DQB (disqualification for unsportsmanlike behavior).

Division labels follow the brand standard format, `Senior Men -68kg`, with U21 divisions labeled as printed, for example `U21 Women -57kg`.

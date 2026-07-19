# Begbilnorr fordonskatalog-feed (Meta)

Auto-genererad Meta-fordonsfeed från begbilnorr.se lager.

## Vad detta gör
`build_feed.py` crawlar sitemap → varje bil-sida → läser schema.org/Car JSON-LD →
skriver `begbilnorr-vehicles-feed.csv` i Metas fordonskatalog-format.
GitHub Action kör varje timme → **ny bil på sajten hamnar automatiskt i feeden → i katalogen → i annonserna**. Såld bil faller bort automatiskt.

## Feed-URL till Meta (efter push)
`https://raw.githubusercontent.com/<OWNER>/<REPO>/main/begbilnorr-vehicles-feed.csv`

## Koppla i Commerce Manager
1. Skapa katalog, typ **Fordon** (act_1301310184349774).
2. Datakällor → **Schemalagd feed** → klistra in feed-URL:en → hämtning **varje timme**.
3. Koppla pixel **1248277947434113** (matchning sker på `vehicle_id` = regnr).

## UTM-spårning
Varje bils `url` har: `utm_source=facebook&utm_medium=paid-social&utm_campaign=lagerannonser&utm_content=<REGNR>`
→ GA4 ser Meta-katalogtrafiken. (Vid behov: sätt dynamiska macron på annons-nivå istället.)

## KÄND SAJT-BUGG (be dev fixa)
VDP-JSON-LD anger `mileageFromOdometer.unitCode = "KMT"` men VÄRDET är i **mil**.
Skriptet korrigerar (×10 → km) i feeden, men fixa gärna `unitCode` på sajten
så alla integrationer (Google, Blocket m.fl.) blir rätt.

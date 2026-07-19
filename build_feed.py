#!/usr/bin/env python3
"""Begbilnorr -> Meta fordonskatalog-feed.
Crawlar begbilnorr.se, läser schema.org/Car JSON-LD per bil, skriver Meta-CSV
med UTM-spårning. Kör automatiskt (t.ex. via GitHub Actions varje timme) så att
nya bilar i lagret auto-hamnar i katalogen och därmed i annonserna.
"""
import re, json, csv, sys, ssl, urllib.request
try:
    import certifi; _CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _CTX = ssl.create_default_context()

BASE = "https://begbilnorr.se"
UA = {"User-Agent": "Mozilla/5.0 (BegbilnorrFeedBot)"}
# UTM: så att GA4 ser att trafiken kommer från Meta-katalogannonserna
UTM = "utm_source=facebook&utm_medium=paid-social&utm_campaign=lagerannonser&utm_content={vid}"

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30, context=_CTX).read().decode("utf-8", "ignore")

def car_urls():
    sm = fetch(f"{BASE}/sitemap.xml")
    return [u for u in re.findall(r"<loc>(.*?)</loc>", sm) if "/bilar/" in u]

def get_car(html):
    for b in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try: d = json.loads(b.strip())
        except Exception: continue
        for it in (d if isinstance(d, list) else [d]):
            if it.get("@type") == "Car":
                return it
    return None

COLS = ["vehicle_id","title","description","url","make","model","year",
        "mileage.value","mileage.unit","price","state_of_vehicle","condition",
        "availability","body_style","fuel_type","transmission","image_link",
        "additional_image_link","address"]

def row(c):
    off = c.get("offers", {}) or {}
    mil = c.get("mileageFromOdometer", {}) or {}
    imgs = c.get("image") or []
    imgs = [imgs] if isinstance(imgs, str) else imgs
    vid = (c.get("vehicleIdentificationNumber") or "").upper().strip()
    brand = c.get("brand", {}); brand = brand.get("name") if isinstance(brand, dict) else brand
    mv = mil.get("value")
    km = int(mv) * 10 if mv not in (None, "") else ""   # SAJT-BUGG: värdet är MIL, ×10 = km
    base_url = c.get("url", "")
    sep = "&" if "?" in base_url else "?"
    url = f"{base_url}{sep}{UTM.format(vid=vid)}" if base_url else ""
    return {
        "vehicle_id": vid, "title": c.get("name",""),
        "description": (c.get("description") or c.get("name",""))[:5000],
        "url": url, "make": brand or "", "model": c.get("model",""),
        "year": (c.get("vehicleModelDate") or "")[:4],
        "mileage.value": km, "mileage.unit": "KM",
        "price": f"{off.get('price')} SEK" if off.get("price") else "",
        "state_of_vehicle": "used", "condition": "used",
        "availability": "available" if "InStock" in str(off.get("availability","")) else "out of stock",
        "body_style": c.get("bodyType",""), "fuel_type": c.get("fuelType",""),
        "transmission": "automatic" if "utomat" in str(c.get("vehicleTransmission","")) else "manual",
        "image_link": imgs[0] if imgs else "",
        "additional_image_link": ",".join(imgs[1:20]),
        "address": '{"addr1":"Fabriksvägen 18","city":"Luleå","region":"Norrbotten","country":"SE","postal_code":"972 54"}',
    }

def main(out="begbilnorr-vehicles-feed.csv"):
    urls = car_urls(); rows=[]; miss=[]
    for u in urls:
        try:
            c = get_car(fetch(u))
            if c and c.get("vehicleIdentificationNumber"): rows.append(row(c))
            else: miss.append(u)
        except Exception as e:
            miss.append(f"{u} ({e})")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow(r)
    print(f"{len(rows)} bilar skrivna till {out}; {len(miss)} hoppade: {miss}", file=sys.stderr)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "begbilnorr-vehicles-feed.csv")

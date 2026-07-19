#!/usr/bin/env python3
"""Begbilnorr -> Meta katalog-feeds (fordon + produkt).
Crawlar begbilnorr.se, laser schema.org/Car JSON-LD per bil, skriver tva feeds:
  begbilnorr-vehicles-feed.csv  (fordonskatalog-format, for framtida AIA)
  begbilnorr-products-feed.csv  (produktkatalog-format, kors NU via Advantage+ katalog)
Bada med UTM-sparning. GitHub Action kor varje timme -> ny bil auto-in i katalogen.
"""
import re, json, csv, sys, ssl, urllib.request
try:
    import certifi; _CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _CTX = ssl.create_default_context()

BASE = "https://begbilnorr.se"
UA = {"User-Agent": "Mozilla/5.0 (BegbilnorrFeedBot)"}
UTM = "utm_source=facebook&utm_medium=paid-social&utm_campaign=lagerannonser&utm_content={vid}"

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30, context=_CTX).read().decode("utf-8", "ignore")

def car_urls():
    return [u for u in re.findall(r"<loc>(.*?)</loc>", fetch(f"{BASE}/sitemap.xml")) if "/bilar/" in u]

def get_car(html):
    for b in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try: d = json.loads(b.strip())
        except Exception: continue
        for it in (d if isinstance(d, list) else [d]):
            if it.get("@type") == "Car": return it
    return None

def parse(c):
    off = c.get("offers", {}) or {}; mil = c.get("mileageFromOdometer", {}) or {}
    imgs = c.get("image") or []; imgs = [imgs] if isinstance(imgs, str) else imgs
    vid = (c.get("vehicleIdentificationNumber") or "").upper().strip()
    brand = c.get("brand", {}); brand = brand.get("name") if isinstance(brand, dict) else (brand or "")
    year = (c.get("vehicleModelDate") or "")[:4]
    mv = mil.get("value"); mil_mil = int(mv) if mv not in (None, "") else ""
    km = int(mv) * 10 if mv not in (None, "") else ""   # SAJT-BUGG: varde ar MIL, x10 = km
    bu = c.get("url", ""); sep = "&" if "?" in bu else "?"
    link = f"{bu}{sep}{UTM.format(vid=vid)}" if bu else ""
    avail = "in stock" if "InStock" in str(off.get("availability", "")) else "out of stock"
    fuel = c.get("fuelType", ""); trans = "Automat" if "utomat" in str(c.get("vehicleTransmission", "")) else "Manuell"
    return dict(vid=vid, name=c.get("name",""), desc=(c.get("description") or c.get("name",""))[:5000],
                link=link, brand=brand, model=c.get("model",""), year=year, km=km, mil=mil_mil,
                price=off.get("price"), avail=avail, body=c.get("bodyType",""), fuel=fuel, trans=trans,
                img=imgs[0] if imgs else "", imgs2=",".join(imgs[1:20]))

VCOLS = ["vehicle_id","title","description","url","make","model","year","mileage.value","mileage.unit","price","state_of_vehicle","condition","availability","body_style","fuel_type","transmission","image_link","additional_image_link","address"]
PCOLS = ["id","title","description","availability","condition","price","link","image_link","additional_image_link","brand","product_type","google_product_category","custom_label_0","custom_label_1","custom_label_2","custom_label_3","custom_label_4"]
ADDR = '{"addr1":"Fabriksvägen 18","city":"Luleå","region":"Norrbotten","country":"SE","postal_code":"972 54"}'

def vrow(p): return {"vehicle_id":p["vid"],"title":p["name"],"description":p["desc"],"url":p["link"],"make":p["brand"],"model":p["model"],"year":p["year"],"mileage.value":p["km"],"mileage.unit":"KM","price":f"{p['price']} SEK" if p["price"] else "","state_of_vehicle":"used","condition":"used","availability":p["avail"].replace("in stock","available").replace("out of stock","out of stock"),"body_style":p["body"],"fuel_type":p["fuel"],"transmission":"automatic" if p["trans"]=="Automat" else "manual","image_link":p["img"],"additional_image_link":p["imgs2"],"address":ADDR}
def prow(p): return {"id":p["vid"],"title":f"{p['name']} {p['year']}".strip(),"description":p["desc"],"availability":p["avail"],"condition":"used","price":f"{p['price']} SEK" if p["price"] else "","link":p["link"],"image_link":p["img"],"additional_image_link":p["imgs2"],"brand":p["brand"],"product_type":f"Bilar > {p['brand']}","google_product_category":"Vehicles & Parts > Vehicles > Motor Vehicles","custom_label_0":p["year"],"custom_label_1":f"{p['mil']} mil","custom_label_2":p["fuel"],"custom_label_3":p["trans"],"custom_label_4":p["body"]}

def write(fn, cols, rows):
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow(r)

def main():
    ps=[]; miss=[]
    for u in car_urls():
        try:
            c = get_car(fetch(u))
            if c and c.get("vehicleIdentificationNumber"): ps.append(parse(c))
            else: miss.append(u)
        except Exception as e: miss.append(f"{u} ({e})")
    write("begbilnorr-vehicles-feed.csv", VCOLS, [vrow(p) for p in ps])
    write("begbilnorr-products-feed.csv", PCOLS, [prow(p) for p in ps])
    print(f"{len(ps)} bilar; {len(miss)} hoppade: {miss}", file=sys.stderr)

if __name__ == "__main__":
    main()

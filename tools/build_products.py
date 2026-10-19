#!/usr/bin/env python3
"""Builds the app's own copy of the Open Food Facts product database.

Reads the full Open Food Facts export (tab-separated, gzipped), keeps products sold
in the UK plus products scanned often anywhere, and writes small JSON files the app
fetches on demand:

  meta.json             version, counts, chunk size
  <v>/p/<n>.json        product records, CHUNK per file, most scanned first
  <v>/t/<xx>.json       search index: word -> product numbers, by first two letters

Data: Open Food Facts, https://world.openfoodfacts.org, licensed ODbL 1.0.
Usage: build_products.py <export.csv.gz or URL> <out dir>
"""
import csv, gzip, io, json, math, os, re, sys, time, unicodedata, urllib.request
from collections import defaultdict

CHUNK = 500
CAP = 4000           # most-scanned products kept per word; rarer products still match their rarer words
MIN_SCANS_WORLD = 25 # products not sold in the UK are kept if scanned at least this often

csv.field_size_limit(1 << 30)

def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"['’`&]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def r1(x): return round(x * 10) / 10

def nice_brand(raw):
    """'MARS POLSKA SP. Z O.O., Twix' -> 'Twix'; 'walkers-crisps' -> 'Walkers Crisps'; 'alpro' -> 'Alpro'."""
    parts = [b.strip() for b in (raw or "").split(",") if b.strip()][:3]
    if not parts: return ""
    b = min(parts, key=len) if len(parts[0]) > 18 else parts[0]
    if re.fullmatch(r"[a-z0-9-]+", b):
        b = re.sub(r"-s$", "'s", b).replace("-", " ")
    if b == b.lower() or (b == b.upper() and len(b) > 4):
        b = re.sub(r"(^|\s)(\S)", lambda m: m.group(1) + m.group(2).upper(), b.lower())
    return b[:40]

def open_source(src):
    if re.match(r"https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "CalorieScanner-family-app/1.0 (github.com/Charles-Rehn/calorie-scanner)"})
        raw = urllib.request.urlopen(req, timeout=120)
    else:
        raw = open(src, "rb")
    return io.TextIOWrapper(gzip.GzipFile(fileobj=raw), encoding="utf-8", errors="replace", newline="")

def main(src, out):
    t0 = time.time()
    f = open_source(src)
    rd = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    head = next(rd)
    col = {h: i for i, h in enumerate(head)}
    need = ["code", "product_name", "countries_tags", "energy-kcal_100g", "proteins_100g", "carbohydrates_100g", "fat_100g"]
    missing = [c for c in need if c not in col]
    if missing: sys.exit(f"export is missing columns {missing}")
    g = lambda row, k: row[col[k]] if k in col and col[k] < len(row) else ""
    rows, seen, total = [], set(), 0
    for row in rd:
        total += 1
        code = g(row, "code").strip()
        if not code.isdigit() or code in seen: continue
        name = (g(row, "product_name_en") or g(row, "product_name") or g(row, "generic_name")).strip()
        if not name or len(name) > 120: continue
        k = num(g(row, "energy-kcal_100g"))
        if k is None:
            kj = num(g(row, "energy-kj_100g")) or num(g(row, "energy_100g"))
            k = kj / 4.184 if kj is not None else None
        if k is None or k < 0 or k > 950: continue
        p, c, fat = (num(g(row, x)) for x in ("proteins_100g", "carbohydrates_100g", "fat_100g"))
        p, c, fat = (max(0.0, v or 0.0) for v in (p, c, fat))
        if p + c + fat > 105: continue
        uk = "en:united-kingdom" in g(row, "countries_tags")
        scans = int(num(g(row, "unique_scans_n")) or 0)
        if not uk and scans < MIN_SCANS_WORLD: continue
        seen.add(code)
        brand = nice_brand(g(row, "brands") or g(row, "brands_en") or g(row, "brands_tags"))
        sq = num(g(row, "serving_quantity"))
        sl = g(row, "serving_size").strip()[:40]
        img = ""
        m = re.search(r"/front_([a-z]{2})\.(\d+)\.\d+\.jpg", g(row, "image_small_url") or g(row, "image_front_small_url"))
        if m: img = f"{m.group(1)}.{m.group(2)}"
        # UK products first: a UK family mostly buys what UK shops sell
        rows.append(((scans * 4 + 100 if uk else scans / 3) + (5 if img else 0), [code, name, brand, round(k), r1(p), r1(c), r1(fat),
                     sl if sq and 0 < sq <= 2000 else "", round(sq, 1) if sq and 0 < sq <= 2000 else 0, 1 if uk else 0, img]))
    rows.sort(key=lambda r: -r[0])
    print(f"read {total:,} rows, kept {len(rows):,} products in {time.time() - t0:.0f}s", flush=True)

    ver = time.strftime("%Y%m%d%H%M")
    base = os.path.join(out, ver)
    os.makedirs(os.path.join(base, "p"), exist_ok=True)
    os.makedirs(os.path.join(base, "t"), exist_ok=True)
    os.makedirs(os.path.join(base, "b"), exist_ok=True)
    # barcode -> product number, by the barcode's last two digits
    codes = defaultdict(dict)
    for i, (_, rec) in enumerate(rows):
        codes[rec[0][-2:]][rec[0]] = i
    for key, d in codes.items():
        with open(os.path.join(base, "b", f"{key}.json"), "w") as fh:
            json.dump(d, fh, separators=(",", ":"))
    index = defaultdict(list)
    for i, (_, rec) in enumerate(rows):
        for tok in set(norm(rec[1] + " " + rec[2]).split()):
            if len(tok) > 30: continue
            index[tok].append(i)
    for n in range(0, len(rows), CHUNK):
        with open(os.path.join(base, "p", f"{n // CHUNK}.json"), "w") as fh:
            json.dump([r[1] for r in rows[n:n + CHUNK]], fh, separators=(",", ":"), ensure_ascii=False)
    shards = defaultdict(dict)
    capped = 0
    for tok, ids in index.items():
        key = tok[:2] if len(tok) >= 2 else tok + "_"
        if len(ids) > CAP: ids, capped = ids[:CAP], capped + 1
        deltas, prev = [], -1
        for i in ids:  # ids are in popularity order; store gaps to keep files small
            deltas.append(i - prev); prev = i
        shards[key][tok] = deltas
    for key, d in shards.items():
        with open(os.path.join(base, "t", f"{key}.json"), "w") as fh:
            json.dump(d, fh, separators=(",", ":"), ensure_ascii=False)
    size = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(base) for fn in fns)
    meta = {"v": ver, "products": len(rows), "barcodes": True, "chunk": CHUNK, "cap": CAP, "words": len(index), "capped": capped,
            "shards": len(shards), "bytes": size, "source": "Open Food Facts (ODbL)", "built": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
    with open(os.path.join(out, "meta.json"), "w") as fh:
        json.dump(meta, fh)
    print(json.dumps(meta), flush=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

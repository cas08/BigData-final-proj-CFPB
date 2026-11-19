"""Крок 1. Профіль сирого CSV на чистому Python (без Spark). Дає числа для оцінок (крок 2).

Запуск:  docker compose run --rm job python3 scripts/01_profile.py /data/complaints.csv full
Вихід:   out/01_profile_<tag>.txt
"""
import collections
import csv
import os
import sys
import time

import rules

SPLIT = 128 * 1024 * 1024  # spark.sql.files.maxPartitionBytes: розмір шматка, який читає одна задача


def dist(cnt: collections.Counter) -> str:
    v = sorted(cnt.values(), reverse=True)
    tot = sum(v)
    return (f"keys={len(v):,} max={v[0]:,} median={v[len(v) // 2]:,} "
            f"top10_share={sum(v[:10]) / tot:.1%}  top1={cnt.most_common(1)[0][0]}")


def main(path: str, tag: str) -> None:
    t0 = time.time()
    size = os.path.getsize(path)
    nsplits = -(-size // SPLIT)
    rows = 0
    resp, product, sub_cards = collections.Counter(), collections.Counter(), collections.Counter()
    company, k1, k2, k4 = (collections.Counter() for _ in range(4))
    prange = {}
    split_k1 = [set() for _ in range(nsplits)]
    split_rows = [0] * nsplits
    ids, dup, ws, sent_before = set(), 0, 0, 0
    len_sum = collections.Counter()

    with open(path, newline="", encoding="utf-8") as f:
        f.readline()  # заголовок
        reader = csv.reader(iter(f.readline, ""))
        for row in reader:
            part = min(f.tell() // SPLIT, nsplits - 1)
            rows += 1
            split_rows[part] += 1
            d, p, sp, i, c, cr, cid = row[0], row[1], row[2], row[3], row[6], row[12], row[14]
            m = d[:7]
            resp[cr] += 1
            product[p] += 1
            company[c] += 1
            lo, hi = prange.get(p, (m, m))
            prange[p] = (min(lo, m), max(hi, m))
            if p == rules.MERGED_CARDS:
                sub_cards[sp] += 1
            key1 = (c, p, i, m)
            k1[key1] += 1
            k2[(p, i, m)] += 1
            k4[(c, p)] += 1
            split_k1[part].add(key1)
            cid_int = int(cid)
            if cid_int in ids:
                dup += 1
            ids.add(cid_int)
            if c != c.strip(" ") or p != p.strip(" ") or i != i.strip(" "):
                ws += 1
            if row[11] and row[11] < d:
                sent_before += 1
            len_sum["company"] += len(c)
            len_sum["product"] += len(rules.fix_product(p, sp))
            len_sum["issue"] += len(i)

    case_pairs = collections.defaultdict(list)
    for c in company:
        case_pairs[c.strip(" ").upper()].append(c)
    case_pairs = [v for v in case_pairs.values() if len(v) > 1]

    out = [
        f"file={path} size={size:,} B rows={rows:,} seconds={time.time() - t0:.0f}",
        f"duplicate complaint_id={dup:,}  whitespace-padded rows={ws:,}  date_sent<date_received={sent_before:,}",
        "company_response: " + ", ".join(f"{k or '<empty>'}={v:,}" for k, v in resp.most_common()),
        f"companies={len(company):,} (case-only duplicates: {len(case_pairs)} groups) {case_pairs[:7]}",
        "avg string length: " + ", ".join(f"{k}={v / rows:.1f}" for k, v in len_sum.items()),
        "products (rows, first month .. last month):",
        *[f"  {product[p]:>11,}  {prange[p][0]}..{prange[p][1]}  {p}" for p in sorted(prange, key=prange.get)],
        "sub_product inside 'Credit card or prepaid card': "
        + ", ".join(f"{k or '<empty>'}={v:,}" for k, v in sub_cards.most_common()),
        "key distributions on raw data (weight = complaints):",
        f"  stage1 (company, product, issue, month): {dist(k1)}",
        f"  stage2 (product, issue, month):          {dist(k2)}",
        f"  stage4 (company, product):               {dist(k4)}",
        f"splits of {SPLIT // 2**20} MB: {nsplits}; rows per split min={min(split_rows):,} max={max(split_rows):,}",
        f"stage1 records after map-side combine (sum of distinct keys per split) = "
        f"{sum(len(s) for s in split_k1):,}  vs distinct keys overall = {len(k1):,}",
    ]
    text = "\n".join(out)
    print(text)
    os.makedirs("out", exist_ok=True)
    with open(f"out/01_profile_{tag}.txt", "w", encoding="utf-8") as fo:
        fo.write(text + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "full")

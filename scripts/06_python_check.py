"""Крок 6. Незалежна перевірка: той самий алгоритм на чистому Python (один потік, словники в пам'яті).

1) Рахує ті самі етапи 0-4 за rules.py і порівнює рейтинг з out/05_result_<tag>.csv (вихід Spark).
2) Час виконання = довідка «а якщо інший інструмент».

Запуск:  docker compose run --rm job python3 scripts/06_python_check.py /data/complaints.csv full
Вихід:   out/06_python_<tag>.json
"""
import collections
import csv
import json
import os
import sys
import time

import rules


def main(path: str, tag: str) -> None:
    t0 = time.time()
    dropped = collections.Counter()
    s1 = collections.defaultdict(lambda: [0, 0])  # етап 1: (company, product, issue, month) -> [n, r]
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            reason, rec = rules.clean_row(row)
            if reason:
                dropped[reason] += 1
                continue
            company, product, issue, month, relief = rec
            cell = s1[(company, product, issue, month)]
            cell[0] += 1
            cell[1] += relief

    s2 = collections.defaultdict(lambda: [0, 0])  # етап 2: (product, issue, month) -> [N, R]
    for (c, p, i, m), (n, r) in s1.items():
        s2[(p, i, m)][0] += n
        s2[(p, i, m)][1] += r

    s4 = collections.defaultdict(lambda: [0, 0.0])  # етапи 3+4: (company, product) -> [n_total, excess_total]
    dropped_cells = 0
    for (c, p, i, m), (n, r) in s1.items():
        big_n, big_r = s2[(p, i, m)]
        if big_n - n == 0:
            dropped_cells += 1
            s4[(c, p)]
            continue
        s4[(c, p)][0] += n
        s4[(c, p)][1] += n * (big_r - r) / (big_n - n) - r

    ranked = sorted(((c, p, n, e, e / n) for (c, p), (n, e) in s4.items() if n >= rules.MIN_N),
                    key=lambda x: -x[4])
    seconds = time.time() - t0

    comparison = "out/05_result_*.csv не знайдено"
    spark_file = f"out/05_result_{tag}.csv"
    if os.path.exists(spark_file):
        with open(spark_file, newline="", encoding="utf-8") as f:
            spark_rows = {(r["company"], r["product"]): float(r["deviation_pp"]) for r in csv.DictReader(f)}
        py_rows = {(c, p): round(100 * d, 2) for c, p, n, e, d in ranked}
        diff = [k for k in py_rows.keys() | spark_rows.keys()
                if abs(py_rows.get(k, 1e9) - spark_rows.get(k, -1e9)) > 0.011]
        comparison = (f"Spark і Python збігаються: {len(py_rows)} пар, відхилення однакові до 0,01 п.п."
                      if not diff else f"РОЗБІЖНІСТЬ у {len(diff)} парах, приклади: {diff[:5]}")

    result = {
        "tag": tag, "seconds": round(seconds, 1), "dropped": dict(dropped),
        "kept": sum(n for n, r in s1.values()),
        "stage1_keys": len(s1), "stage2_keys": len(s2), "stage4_keys": len(s4),
        "dropped_cells": dropped_cells, "pairs_ranked": len(ranked), "comparison_with_spark": comparison,
        "top": [{"company": c, "product": p, "n_total": n, "deviation_pp": round(100 * d, 2)}
                for c, p, n, e, d in ranked[:rules.TOP]],
    }
    with open(f"out/06_python_{tag}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "top"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

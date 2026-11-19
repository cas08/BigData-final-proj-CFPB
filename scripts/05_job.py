"""Крок 5. Основний конвеєр: чистка + етапи 1-4.

Етап 1  groupBy(company, product, issue, month) -> n, r          shuffle №1
Етап 2  groupBy(product, issue, month) з виходу 1 -> N, R         shuffle №2
Етап 3  join 1 і 2 за (product, issue, month) -> excess           broadcast, без shuffle
Етап 4  groupBy(company, product) -> Σn, Σexcess, відхилення      shuffle №3

Запуск (вибірка):  docker compose run --rm --service-ports job
Запуск (повний):   docker compose run --rm --service-ports job \
                     spark-submit scripts/05_job.py --input /data/complaints.csv --tag full
Вихід:  out/05_result_<tag>.csv (рейтинг), out/05_summary_<tag>.json, out/05_plan_<tag>.txt (EXPLAIN)
"""
import argparse
import contextlib
import csv
import io
import json
import time

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

import common
import rules


def stage1(clean: DataFrame) -> DataFrame:
    """(company, product, issue, month) -> n скарг, r з relief. Spark сам робить часткову агрегацію (combiner)."""
    return clean.groupBy("company", "product", "issue", "month").agg(
        F.count(F.lit(1)).alias("n"), F.sum("relief").alias("r"))


def stage2(s1: DataFrame) -> DataFrame:
    """(product, issue, month) -> N, R: норма категорії, рахується з виходу етапу 1.
    У коді N, R звуться cat_n, cat_r: Spark SQL не розрізняє регістр імен колонок (N і n конфліктують)."""
    return s1.groupBy("product", "issue", "month").agg(F.sum("n").alias("cat_n"), F.sum("r").alias("cat_r"))


def stage3(s1: DataFrame, s2: DataFrame) -> DataFrame:
    """Join за категорією. Leave-one-out: excess = n * (R - r) / (N - n) - r. Якщо N == n, порівнювати нема з ким."""
    others = F.col("cat_n") - F.col("n")
    valid = others > 0
    excess = F.when(valid, F.col("n") * (F.col("cat_r") - F.col("r")) / others - F.col("r"))
    return s1.join(s2, ["product", "issue", "month"]).select(
        "company", "product", "n", valid.alias("valid"), excess.alias("excess"))


def stage4(s3: DataFrame) -> DataFrame:
    """(company, product) -> n_total, excess_total, відхилення = excess_total / n_total."""
    agg = s3.groupBy("company", "product").agg(
        F.sum(F.when(F.col("valid"), F.col("n")).otherwise(0)).alias("n_total"),
        F.sum("excess").alias("excess_total"),
        F.sum(F.when(~F.col("valid"), 1).otherwise(0)).alias("dropped_cells"),
        F.sum(F.when(~F.col("valid"), F.col("n")).otherwise(0)).alias("dropped_n"),
    )
    return agg.withColumn(
        "deviation", F.when(F.col("n_total") > 0, F.col("excess_total") / F.col("n_total")))


def explain(df: DataFrame) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        df.explain(mode="formatted")
    return buf.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--format", default="csv", choices=["csv", "parquet"])
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()

    spark = common.session(f"final-05-{a.tag}")
    clean = common.clean(common.read_raw(spark, a.input, a.format))
    s1 = stage1(clean)
    s4 = stage4(stage3(s1, stage2(s1)))

    plan_before = explain(s4)
    t0 = time.time()
    rows = [r.asDict() for r in s4.collect()]  # єдина дія: ~26 тис. пар (компанія, продукт)
    seconds = time.time() - t0
    plan_after = explain(s4)  # після виконання AQE показує фінальний план (isFinalPlan=true)

    ranked = sorted((r for r in rows if r["n_total"] >= rules.MIN_N), key=lambda r: -r["deviation"])
    with open(f"out/05_result_{a.tag}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "company", "product", "n_total", "excess_total", "deviation_pp"])
        for i, r in enumerate(ranked, 1):
            w.writerow([i, r["company"], r["product"], r["n_total"],
                        f"{r['excess_total']:.2f}", f"{100 * r['deviation']:.2f}"])
    summary = {
        "tag": a.tag, "input": a.input, "format": a.format, "action_seconds": round(seconds, 1),
        "pairs": len(rows), "pairs_ranked": len(ranked),
        "complaints_used": sum(r["n_total"] for r in rows),
        "dropped_cells": sum(r["dropped_cells"] for r in rows),
        "dropped_complaints": sum(r["dropped_n"] for r in rows),
        "top": [{k: r[k] for k in ("company", "product", "n_total", "excess_total", "deviation")}
                for r in ranked[:rules.TOP]],
    }
    with open(f"out/05_summary_{a.tag}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with open(f"out/05_plan_{a.tag}.txt", "w", encoding="utf-8") as f:
        f.write("=== EXPLAIN до запуску ===\n" + plan_before + "\n=== EXPLAIN після запуску (AQE) ===\n" + plan_after)

    print(f"\n{a.tag}: {len(rows):,} пар, у рейтингу {len(ranked):,}, дія {seconds:.1f} с")
    for i, r in enumerate(ranked[:rules.TOP], 1):
        print(f"{i:>2}. {100 * r['deviation']:+6.2f} п.п.  n={r['n_total']:>9,}  {r['company']} | {r['product']}")
    spark.stop()


if __name__ == "__main__":
    main()

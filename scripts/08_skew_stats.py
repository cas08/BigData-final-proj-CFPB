"""Крок 8. Розподіл ключів на кожному shuffle: найчастіший ключ, медіана, частка топ-10.

Для кожного shuffle дві одиниці:
  - вага ключа у скаргах (скільки сирих скарг стоїть за ключем);
  - скільки рядків з цим ключем приходить на вхід shuffle (до часткової агрегації).
Розміри задач (чи «коштує» перекіс) беруться з кроку 7 (out/07_stages_<tag>.md).

Запуск:  docker compose run --rm job spark-submit scripts/08_skew_stats.py --input /data/complaints.csv --tag full
Вихід:   out/08_skew_<tag>.md
"""
import argparse
import importlib

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

import common

job = importlib.import_module("05_job")  # ті самі функції етапів, що й в основному конвеєрі


def describe(df: DataFrame, keys: list, value: str) -> dict:
    stats = df.agg(F.sum(value).alias("total"), F.count(F.lit(1)).alias("keys"),
                   F.percentile_approx(value, 0.5, 100000).alias("median")).first()
    top = df.orderBy(F.desc(value)).limit(10).collect()
    return {"keys": stats["keys"], "median": stats["median"], "max": top[0][value],
            "max_key": " / ".join(str(top[0][k]) for k in keys),
            "top10_share": sum(r[value] for r in top) / stats["total"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--format", default="csv")
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()

    spark = common.session(f"final-08-skew-{a.tag}")
    clean = common.clean(common.read_raw(spark, a.input, a.format))
    s1 = job.stage1(clean).cache()
    s3 = job.stage3(s1, job.stage2(s1)).cache()

    k1, k2, k4 = ["company", "product", "issue", "month"], ["product", "issue", "month"], ["company", "product"]
    rows = [
        ("№1 (етап 1)", "скарги на ключ = рядки на вході", k1, s1.select(*k1, F.col("n").alias("v"))),
        ("№2 (етап 2)", "скарги на ключ", k2, s1.groupBy(*k2).agg(F.sum("n").alias("v"))),
        ("№2 (етап 2)", "рядки етапу 1 на ключ (компаній у категорії)", k2, s1.groupBy(*k2).count()
         .withColumnRenamed("count", "v")),
        ("№3 (етап 4)", "скарги на ключ", k4, s3.groupBy(*k4).agg(F.sum("n").alias("v"))),
        ("№3 (етап 4)", "рядки етапу 3 на ключ (клітинок проблема×місяць)", k4, s3.groupBy(*k4).count()
         .withColumnRenamed("count", "v")),
    ]
    md = [f"# Розподіл ключів на shuffle ({a.tag})", "",
          "| Shuffle | Одиниця | Ключів | Найчастіший ключ | Max | Медіана | Частка топ-10 |",
          "|---|---|---|---|---|---|---|"]
    for name, unit, keys, df in rows:
        d = describe(df, keys, "v")
        md.append(f"| {name} | {unit} | {d['keys']:,} | {d['max_key']} | {d['max']:,} | {d['median']:,} "
                  f"| {d['top10_share']:.1%} |")
    text = "\n".join(md) + "\n"
    with open(f"out/08_skew_{a.tag}.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    spark.stop()


if __name__ == "__main__":
    main()

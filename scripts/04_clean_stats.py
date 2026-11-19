"""Крок 4. Статистика чистки (етап 0): скільки рядків відкинуто / виправлено кожним правилом + приклади.

Правила ті самі, що в common.clean() (і rules.clean_row у Python). Пріоритет відкидання: D1, потім D2, потім D3.

Запуск:  docker compose run --rm job spark-submit scripts/04_clean_stats.py --input data/sample.csv --tag sample
Вихід:   out/04_clean_<tag>.json, out/04_clean_<tag>.md
"""
import argparse
import json

from pyspark.sql import functions as F

import common
import rules

EXAMPLE_COLS = ["complaint_id", "date_received", "product", "sub_product", "issue", "company", "company_response"]


def flags():
    closed = F.coalesce(F.col("company_response").isin(*rules.CLOSED), F.lit(False))
    nonempty = (common._nonempty(F.trim("company")) & common._nonempty(F.trim("product"))
                & common._nonempty(F.trim("issue")))
    date_ok = F.coalesce(F.col("date_received").rlike(rules.DATE_REGEX), F.lit(False))
    d1 = ~closed
    d2 = closed & ~nonempty
    d3 = closed & nonempty & ~date_ok
    keep = closed & nonempty & date_ok
    f1 = keep & ((F.trim("company") != F.col("company")) | (F.trim("product") != F.col("product"))
                 | (F.trim("issue") != F.col("issue")))
    f3 = keep & (common.fixed_product() != F.trim("product"))
    return {"D1": d1, "D2": d2, "D3": d3, "kept": keep, "F1": f1, "F3": f3}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--format", default="csv")
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()

    spark = common.session(f"final-04-clean-{a.tag}")
    raw = common.read_raw(spark, a.input, a.format)
    fl = flags()

    # job 1: усі лічильники одним проходом
    row = raw.agg(
        F.count(F.lit(1)).alias("total"),
        *[F.sum(c.cast("long")).alias(k) for k, c in fl.items()],
        F.countDistinct(F.when(fl["kept"], F.trim("company"))).alias("companies_before_F2"),
        F.countDistinct(F.when(fl["kept"], F.upper(F.trim("company")))).alias("companies_after_F2"),
    ).first().asDict()

    # job 2: розподіл company_response
    responses = {r["company_response"] or "<empty>": r["count"]
                 for r in raw.groupBy("company_response").count().collect()}

    # job 3-5: приклади рядків (рідкісні правила одним проходом, часті через limit)
    rare = raw.where(fl["D2"] | fl["D3"] | fl["F1"]).select(
        *EXAMPLE_COLS, F.when(fl["D2"], "D2").when(fl["D3"], "D3").otherwise("F1").alias("rule")).collect()
    examples = {k: [] for k in ("D1", "D2", "D3", "F1", "F3")}
    for r in rare:
        if len(examples[r["rule"]]) < 3:
            examples[r["rule"]].append({c: r[c] for c in EXAMPLE_COLS})
    for k in ("D1", "F3"):
        examples[k] = [r.asDict() for r in raw.where(fl[k]).select(*EXAMPLE_COLS).limit(3).collect()]
    for ex in examples["F3"]:
        ex["product_after_F3"] = rules.fix_product(ex["product"].strip(" "), ex["sub_product"])

    result = {"counts": row, "company_response": responses, "examples": examples}
    with open(f"out/04_clean_{a.tag}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    t = row["total"]
    md = [f"# Чистка ({a.tag}): {t:,} рядків на вході, {row['kept']:,} лишилось ({row['kept'] / t:.2%})", "",
          "| Правило | Що робить | Рядків |", "|---|---|---|",
          f"| D1 | відкинуто: company_response не закрита (In progress, Untimely response, порожнє) | {row['D1']:,} |",
          f"| D2 | відкинуто: порожні company / product / issue | {row['D2']:,} |",
          f"| D3 | відкинуто: date_received не у форматі yyyy-MM-dd | {row['D3']:,} |",
          f"| F1 | виправлено: пробіли на краях company / product / issue | {row['F1']:,} |",
          f"| F2 | виправлено: регістр назви компанії (upper) | {row['companies_before_F2']:,} -> "
          f"{row['companies_after_F2']:,} різних компаній |",
          f"| F3 | виправлено: стара назва продукту -> чинна | {row['F3']:,} |", "",
          "company_response: " + ", ".join(f"{k}={v:,}" for k, v in sorted(responses.items(), key=lambda x: -x[1])),
          "", "## Приклади рядків", ""]
    for k, rows in examples.items():
        md.append(f"**{k}**")
        md += [f"- `{json.dumps(r, ensure_ascii=False)}`" for r in rows] or ["- (немає таких рядків)"]
        md.append("")
    with open(f"out/04_clean_{a.tag}.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("\n".join(md[:12]))
    spark.stop()


if __name__ == "__main__":
    main()

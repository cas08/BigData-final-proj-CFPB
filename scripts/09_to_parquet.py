"""Крок 9. Конвертація сирого CSV у Parquet для експерименту (крок 10).

Конвертуються всі 15 колонок без чистки: різницю в експерименті має давати лише формат.
Запуск:  docker compose run --rm job spark-submit scripts/09_to_parquet.py \
            --input /data/complaints.csv --output /data/complaints_parquet
"""
import argparse
import os
import time

import common


def column_sizes(spark, path: str) -> dict:
    """Стиснений розмір кожної колонки за футерами Parquet (через Java-бібліотеку Parquet усередині Spark)."""
    jvm = spark._jvm
    conf = spark._jsc.hadoopConfiguration()
    sizes = {}
    for f in sorted(os.listdir(path)):
        if not f.endswith(".parquet"):
            continue
        hpath = jvm.org.apache.hadoop.fs.Path(f"file://{os.path.join(path, f)}")
        reader = jvm.org.apache.parquet.hadoop.ParquetFileReader.open(
            jvm.org.apache.parquet.hadoop.util.HadoopInputFile.fromPath(hpath, conf))
        for block in reader.getFooter().getBlocks():
            for col in block.getColumns():
                name = col.getPath().toDotString()
                sizes[name] = sizes.get(name, 0) + col.getTotalSize()
        reader.close()
    return sizes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--sizes-only", action="store_true", help="не конвертувати, лише розміри колонок")
    a = ap.parse_args()

    spark = common.session("final-09-to-parquet")
    if a.sizes_only:
        sizes = column_sizes(spark, a.output)
        used = ["date_received", "product", "sub_product", "issue", "company", "company_response"]
        lines = [f"{k}: {v / 2**20:,.1f} МіБ" for k, v in sorted(sizes.items(), key=lambda x: -x[1])]
        lines.append(f"разом {sum(sizes.values()) / 2**20:,.1f} МіБ; 6 колонок конвеєра: "
                     f"{sum(sizes[c] for c in used) / 2**20:,.1f} МіБ")
        print("\n".join(lines))
        with open("out/09_parquet_columns.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        spark.stop()
        return
    t0 = time.time()
    common.read_raw(spark, a.input).write.mode("overwrite").parquet(a.output)
    seconds = time.time() - t0
    size = sum(os.path.getsize(os.path.join(a.output, f)) for f in os.listdir(a.output) if f.endswith(".parquet"))
    files = sum(1 for f in os.listdir(a.output) if f.endswith(".parquet"))
    line = (f"CSV {os.path.getsize(a.input):,} B -> Parquet {size:,} B ({files} файлів), "
            f"у {os.path.getsize(a.input) / size:.1f} рази менше, конвертація {seconds:.0f} с")
    print(line)
    with open("out/09_to_parquet.txt", "w", encoding="utf-8") as f:
        f.write(line + "\n")
    spark.stop()


if __name__ == "__main__":
    main()

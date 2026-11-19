"""Крок 3. Детермінована вибірка: рядки, де complaint_id % 200 == 0 (~0,5 %).

Рядки копіюються як є (з усім брудом), тому чистка на вибірці теж має що робити.
Відбір за id не залежить від дати, компанії чи продукту.

Запуск:  docker compose run --rm job python3 scripts/03_make_sample.py /data/complaints.csv data/sample.csv
"""
import csv
import sys

MOD = 200


def main(src: str, dst: str) -> None:
    kept = total = 0
    with open(src, newline="", encoding="utf-8") as f, open(dst, "w", newline="", encoding="utf-8") as out:
        out.write(f.readline())  # заголовок
        for line in f:
            total += 1
            row = next(csv.reader([line]))
            if int(row[14]) % MOD == 0:
                out.write(line)
                kept += 1
    print(f"rows read={total:,} kept={kept:,} ({kept / total:.2%}) -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

# Компанії, що закривають скарги без компенсації частіше за інших (CFPB, Spark)

Фінальний проєкт з BigData. Датасет CFPB Consumer Complaint Database (19,2 млн скарг, 5,82 ГБ CSV).
Питання: які фінансові компанії в тих самих категоріях (продукт, проблема, місяць) частіше за інших
закривають скарги без компенсації клієнту. Норма категорії рахується без самої компанії (leave-one-out).

Що де лежить:
- `PLAN.md`: план, складений до коду;
- `STEPS.md`: журнал кроків 0-14 (що зроблено, якою командою, що вийшло);
- `docs/`: оцінка до коду (`02_`), оцінка проти факту і карта фаз (`11_`), звіт (`12_report.md`);
- `scripts/`: кроки з номерами, `rules.py` (правила) і `common.py` (читання й чистка в Spark);
- `out/`: результати кроків; `evidence/`: повні логи запусків; `spark-events/`: event logs для History Server;
- `slides/`: презентація.

## Версії

- Docker image `apache/spark:4.2.0-python3` (digest `sha256:fc64959c04bd87b0ac686be9aaa9008b69cdb1afc695400528279c8b01f43d89`): Spark 4.2.0, Java 21, Python 3.10.12.
- Spark: `local[4]`, driver 2 ГБ (`conf/spark-defaults.conf`).
- Python-скрипти використовують лише стандартну бібліотеку.

## Демо на вибірці (без інтернету, ~10 с)

```bash
docker compose run --rm --service-ports job
```

Spark UI http://localhost:4040 живе лише під час запуску (~5 с на вибірці). Для демо зручніше History Server, де вже є повний запуск `final-05-full` і всі заміри експерименту:

```bash
docker compose up -d history
```

і http://localhost:18080.

Очікуваний результат на вибірці (95 809 рядків, у рейтинг з порогом 1000 скарг потрапляють лише три кредитні бюро):

```
sample: 2,548 пар, у рейтингу 3
 1. +37.72 п.п.  n=   21,210  EXPERIAN INFORMATION SOLUTIONS INC. | Credit reporting or other personal consumer reports
 2. -11.97 п.п.  n=   24,939  EQUIFAX, INC. | Credit reporting or other personal consumer reports
 3. -26.68 п.п.  n=   25,014  TRANSUNION INTERMEDIATE HOLDINGS, INC. | Credit reporting or other personal consumer reports
```

Файли результату: `out/05_result_sample.csv`, `out/05_summary_sample.json`, `out/05_plan_sample.txt`.

## Повний датасет

Повний CSV не входить у здачу: посилання і sha256 у `data/SOURCE.md`. Для запуску на повних даних завантажений `complaints.csv` кладу в `data/`, і в контейнері він доступний як `/data/complaints.csv`.
Команди всіх кроків по порядку є в `STEPS.md`; основний запуск:

```bash
docker compose run --rm --service-ports job spark-submit scripts/05_job.py --input /data/complaints.csv --tag full
```

Вибірку з повного CSV відтворює:

```bash
docker compose run --rm job python3 scripts/03_make_sample.py /data/complaints.csv data/sample.csv
```

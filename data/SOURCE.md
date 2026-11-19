# Дані

Повний датасет до здачі не входить. Для запуску на повних даних `complaints.csv` кладеться в `data/`.

- Джерело: CFPB Consumer Complaint Database, https://www.consumerfinance.gov/data-research/consumer-complaints/ (повне завантаження CSV, `complaints.csv.zip`).
- Ліцензія: дані у відкритому доступі опублікувало федеральне агентство США (CFPB), завантаження безкоштовне. Роботи федерального уряду США не охороняються авторським правом (17 U.S.C. § 105), тож навчальне використання дозволене.
- Завантажено: 2026-11-16.
- `complaints.csv`: 5 824 441 185 Б, 19 203 798 рядків, 15 колонок.
- sha256 `complaints.csv`: `76b0ea22f4969769f3b1aaec7e43339030a1d807025b1b3ee969f05a3845ec7d`
- `complaints.csv.zip`: 367 797 920 Б.

Вибірка `sample.csv` входить до архіву. Її створює `scripts/03_make_sample.py` (рядки з `complaint_id % 200 == 0`).

- 95 809 рядків + заголовок, 29 036 268 Б.
- sha256 `sample.csv`: `2a1f399d1e63adb53794e92d8760ade72cf52cc6128ec8f6538fc55cc2de1687`

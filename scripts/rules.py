"""Правила чистки і метрики. Один файл для Python-кроків (01, 03, 06) і для Spark (common.py),
щоб обидві реалізації рахували за однаковими правилами."""

COLS = [
    "date_received", "product", "sub_product", "issue", "sub_issue",
    "company_public_response", "company", "state", "zip_code", "tags",
    "submitted_via", "date_sent_to_company", "company_response",
    "timely_response", "complaint_id",
]

# Компенсація = будь-яка дія на користь клієнта (relief = 1).
RELIEF = ("Closed with monetary relief", "Closed with non-monetary relief", "Closed with relief")
# Закрито лише поясненням / без дії (relief = 0).
NO_RELIEF = ("Closed with explanation", "Closed", "Closed without relief")
CLOSED = RELIEF + NO_RELIEF  # D1: усе інше (In progress, Untimely response, порожнє) відкидаємо

# F3: CFPB перейменовував продукти у 2017-04 і 2023-08. Старі назви -> чинна назва.
CREDIT_REPORTING = "Credit reporting or other personal consumer reports"
PAYDAY = "Payday loan, title loan, personal loan, or advance loan"
MONEY = "Money transfer, virtual currency, or money service"
PRODUCT_MAP = {
    "Credit reporting": CREDIT_REPORTING,
    "Credit reporting, credit repair services, or other personal consumer reports": CREDIT_REPORTING,
    "Payday loan": PAYDAY,
    "Payday loan, title loan, or personal loan": PAYDAY,
    "Bank account or service": "Checking or savings account",
    "Money transfers": MONEY,
    "Virtual currency": MONEY,
}
# У 2017-04...2023-08 кредитні й prepaid-картки були злиті в одну назву; ділимо за sub_product.
MERGED_CARDS = "Credit card or prepaid card"
CREDIT_CARD_SUBS = ("General-purpose credit card or charge card", "Store credit card")

MIN_N = 1000  # поріг для рейтингу етапу 4
TOP = 20


def fix_product(product: str, sub_product: str) -> str:
    if product == MERGED_CARDS:
        return "Credit card" if sub_product in CREDIT_CARD_SUBS else "Prepaid card"
    return PRODUCT_MAP.get(product, product)


def valid_date(d: str) -> bool:
    """D3: рядок має вигляд yyyy-MM-dd з місяцем 01-12 (те саме перевіряє регулярний вираз у Spark)."""
    return (len(d) == 10 and d[4] == "-" and d[7] == "-" and d[:4].isdigit()
            and d[5:7].isdigit() and d[8:].isdigit() and "01" <= d[5:7] <= "12")


DATE_REGEX = r"^[0-9]{4}-(0[1-9]|1[0-2])-[0-9]{2}$"


def clean_row(row: list) -> tuple:
    """Повертає (причина_відкидання, None) або (None, (company, product, issue, month, relief))."""
    d, product, sub_product, issue = row[0], row[1].strip(" "), row[2], row[3].strip(" ")
    company, response = row[6].strip(" ").upper(), row[12]
    if response not in CLOSED:
        return "D1", None
    if not company or not product or not issue:
        return "D2", None
    if not valid_date(d):
        return "D3", None
    return None, (company, fix_product(product, sub_product), issue, d[:7], 1 if response in RELIEF else 0)


if __name__ == "__main__":  # самоперевірка правил
    row = ["2026-05-07", " Credit reporting ", "", "Incorrect info", "", "", "Acme inc ", "", "", "", "",
           "", "Closed with non-monetary relief", "Yes", "1"]
    assert clean_row(row) == (None, ("ACME INC", CREDIT_REPORTING, "Incorrect info", "2026-05", 1))
    assert clean_row(row[:12] + ["In progress"] + row[13:])[0] == "D1"
    assert clean_row(row[:6] + [" "] + row[7:])[0] == "D2"
    assert clean_row(["2026-13-01"] + row[1:])[0] == "D3"
    assert fix_product(MERGED_CARDS, "Gift card") == "Prepaid card"
    assert fix_product(MERGED_CARDS, "Store credit card") == "Credit card"
    print("rules OK")

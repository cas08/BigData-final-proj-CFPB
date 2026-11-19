# Чистка (sample): 95,809 рядків на вході, 92,454 лишилось (96.50%)

| Правило | Що робить | Рядків |
|---|---|---|
| D1 | відкинуто: company_response не закрита (In progress, Untimely response, порожнє) | 3,355 |
| D2 | відкинуто: порожні company / product / issue | 0 |
| D3 | відкинуто: date_received не у форматі yyyy-MM-dd | 0 |
| F1 | виправлено: пробіли на краях company / product / issue | 0 |
| F2 | виправлено: регістр назви компанії (upper) | 1,504 -> 1,502 різних компаній |
| F3 | виправлено: стара назва продукту -> чинна | 13,098 |

company_response: Closed with explanation=59,533, Closed with non-monetary relief=31,606, In progress=3,164, Closed with monetary relief=1,118, Untimely response=191, Closed without relief=91, Closed=76, Closed with relief=30

## Приклади рядків

**D1**
- `{"complaint_id": "26865200", "date_received": "2026-09-09", "product": "Student loan", "sub_product": "Private student loan", "issue": "Getting a loan", "company": "MOHELA", "company_response": "Untimely response"}`
- `{"complaint_id": "29889400", "date_received": "2026-10-13", "product": "Credit reporting or other personal consumer reports", "sub_product": "Credit reporting", "issue": "Incorrect information on your report", "company": "Experian Information Solutions Inc.", "company_response": "In progress"}`
- `{"complaint_id": "29893000", "date_received": "2026-10-13", "product": "Credit reporting or other personal consumer reports", "sub_product": "Credit reporting", "issue": "Improper use of your report", "company": "TRANSUNION INTERMEDIATE HOLDINGS, INC.", "company_response": "In progress"}`

**D2**
- (немає таких рядків)

**D3**
- (немає таких рядків)

**F1**
- (немає таких рядків)

**F3**
- `{"complaint_id": "6706400", "date_received": "2023-03-17", "product": "Credit reporting, credit repair services, or other personal consumer reports", "sub_product": "Credit reporting", "issue": "Incorrect information on your report", "company": "Experian Information Solutions Inc.", "company_response": "Closed with explanation", "product_after_F3": "Credit reporting or other personal consumer reports"}`
- `{"complaint_id": "3673200", "date_received": "2020-05-29", "product": "Credit reporting, credit repair services, or other personal consumer reports", "sub_product": "Credit reporting", "issue": "Problem with a credit reporting company's investigation into an existing problem", "company": "ALLY FINANCIAL INC.", "company_response": "Closed with explanation", "product_after_F3": "Credit reporting or other personal consumer reports"}`
- `{"complaint_id": "3925400", "date_received": "2020-10-29", "product": "Credit card or prepaid card", "sub_product": "General-purpose credit card or charge card", "issue": "Other features, terms, or problems", "company": "JPMORGAN CHASE & CO.", "company_response": "Closed with non-monetary relief", "product_after_F3": "Credit card"}`

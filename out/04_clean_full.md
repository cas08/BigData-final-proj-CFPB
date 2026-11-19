# Чистка (full): 19,203,798 рядків на вході, 18,517,797 лишилось (96.43%)

| Правило | Що робить | Рядків |
|---|---|---|
| D1 | відкинуто: company_response не закрита (In progress, Untimely response, порожнє) | 685,995 |
| D2 | відкинуто: порожні company / product / issue | 6 |
| D3 | відкинуто: date_received не у форматі yyyy-MM-dd | 0 |
| F1 | виправлено: пробіли на краях company / product / issue | 0 |
| F2 | виправлено: регістр назви компанії (upper) | 7,736 -> 7,729 різних компаній |
| F3 | виправлено: стара назва продукту -> чинна | 2,636,220 |

company_response: Closed with explanation=11,862,075, Closed with non-monetary relief=6,389,281, In progress=649,654, Closed with monetary relief=225,665, Untimely response=36,320, Closed without relief=17,867, Closed=17,611, Closed with relief=5,304, <empty>=21

## Приклади рядків

**D1**
- `{"complaint_id": "22315929", "date_received": "2026-05-18", "product": "Debt collection", "sub_product": "I do not know", "issue": "Took or threatened to take negative or legal action", "company": "Credit Systems of the Fox Valley, Inc.", "company_response": "Untimely response"}`
- `{"complaint_id": "23097335", "date_received": "2026-06-11", "product": "Debt or credit management", "sub_product": "Credit repair services", "issue": "Charged upfront or unexpected fees", "company": "Credit Sage LLC", "company_response": "Untimely response"}`
- `{"complaint_id": "23900125", "date_received": "2026-07-06", "product": "Prepaid card", "sub_product": "Government benefit card", "issue": "Trouble using the card", "company": "Conduent Incorporated", "company_response": "Untimely response"}`

**D2**
- `{"complaint_id": "8550796", "date_received": "2024-03-13", "product": "Checking or savings account", "sub_product": null, "issue": null, "company": "WELLS FARGO & COMPANY", "company_response": "Closed with explanation"}`
- `{"complaint_id": "8698781", "date_received": "2024-04-02", "product": "Checking or savings account", "sub_product": null, "issue": null, "company": "WELLS FARGO & COMPANY", "company_response": "Closed with explanation"}`
- `{"complaint_id": "8698636", "date_received": "2024-04-03", "product": "Checking or savings account", "sub_product": null, "issue": null, "company": "BANK OF AMERICA, NATIONAL ASSOCIATION", "company_response": "Closed with explanation"}`

**D3**
- (немає таких рядків)

**F1**
- (немає таких рядків)

**F3**
- `{"complaint_id": "6706758", "date_received": "2023-03-17", "product": "Credit reporting, credit repair services, or other personal consumer reports", "sub_product": "Credit reporting", "issue": "Improper use of your report", "company": "Experian Information Solutions Inc.", "company_response": "Closed with non-monetary relief", "product_after_F3": "Credit reporting or other personal consumer reports"}`
- `{"complaint_id": "6706410", "date_received": "2023-03-17", "product": "Credit reporting, credit repair services, or other personal consumer reports", "sub_product": "Credit reporting", "issue": "Improper use of your report", "company": "TRANSUNION INTERMEDIATE HOLDINGS, INC.", "company_response": "Closed with non-monetary relief", "product_after_F3": "Credit reporting or other personal consumer reports"}`
- `{"complaint_id": "6706409", "date_received": "2023-03-17", "product": "Credit reporting, credit repair services, or other personal consumer reports", "sub_product": "Credit reporting", "issue": "Improper use of your report", "company": "EQUIFAX, INC.", "company_response": "Closed with explanation", "product_after_F3": "Credit reporting or other personal consumer reports"}`

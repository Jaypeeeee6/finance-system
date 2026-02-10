"""
Temporary script: Update request 899 to custom schedule and insert 5 installments.
- Sets payment_requests.recurring_interval to custom:date1:amount1,date2:amount2,...
- Removes existing schedule rows for request 899, then inserts the 5 rows below.
- 1st schedule is marked paid with receipt_path = finance admin receipt for request 899.
"""
import json
import sqlite3

DB = r"c:\Users\glori\finance-system\instance\payment_system.db"

# Installments in order (payment_order 1..5)
INSTALLMENTS = [
    ("2026-02-01", 5600),
    ("2026-02-09", 4200),
    ("2026-02-16", 5600),
    ("2026-04-12", 5600),
    ("2026-06-10", 7000),
]

CREATED_AT = "2026-01-29 11:47:10.354093"


def get_finance_admin_receipt_path(cur, request_id):
    """Get first finance admin receipt path for request_id from payment_requests."""
    cur.execute(
        "SELECT finance_admin_receipt_path, receipt_path FROM payment_requests WHERE request_id = ?",
        (request_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    finance_path, legacy_path = row[0], row[1]
    # Prefer finance_admin_receipt_path (JSON list or single path)
    if finance_path:
        try:
            parsed = json.loads(finance_path)
            if isinstance(parsed, list) and parsed:
                return parsed[0]
            if isinstance(parsed, str):
                return parsed
        except (json.JSONDecodeError, TypeError):
            if "," in finance_path:
                parts = [p.strip() for p in finance_path.split(",") if p.strip()]
                return parts[0] if parts else None
            return finance_path
    return legacy_path


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Get finance admin receipt for request 899 (for 1st schedule)
    receipt_path_1st = get_finance_admin_receipt_path(cur, 899)
    print("Finance admin receipt for request 899 (1st schedule):", receipt_path_1st or "(none)")

    # Build recurring_interval from installments: custom:date1:amount1,date2:amount2,...
    custom_parts = [f"{date}:{amount}" for date, amount in INSTALLMENTS]
    recurring_interval = "custom:" + ",".join(custom_parts)

    # 1) Update payment_requests
    cur.execute(
        "UPDATE payment_requests SET recurring_interval = ? WHERE request_id = 899",
        (recurring_interval,),
    )
    print("payment_requests updated, recurring_interval set to:", recurring_interval)
    print("Rows updated:", cur.rowcount)

    # 2) Remove existing schedule rows for request 899
    cur.execute("DELETE FROM recurring_payment_schedules WHERE request_id = 899")
    deleted = cur.rowcount
    print("Deleted existing schedule rows for request 899:", deleted)

    # 3) Insert the 5 rows; 1st is paid with receipt_path = finance admin receipt
    for i, (payment_date, amount) in enumerate(INSTALLMENTS, start=1):
        is_paid = 1 if i == 1 else 0
        paid_date = payment_date if i == 1 else None
        receipt_path = receipt_path_1st if i == 1 else None
        cur.execute(
            """INSERT INTO recurring_payment_schedules
               (request_id, payment_date, amount, payment_order, is_paid, paid_date, receipt_path, created_at, has_been_edited)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (899, payment_date, amount, i, is_paid, paid_date, receipt_path, CREATED_AT),
        )
    print("Inserted", len(INSTALLMENTS), "rows; 1st schedule is_paid=1, receipt_path=", receipt_path_1st or "NULL")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()

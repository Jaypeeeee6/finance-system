"""
Temporary script to populate reference_number in procurement_receipt_entries
from receipt_reference_number in procurement_item_requests (for old item requests
where receipt entries were created without the reference number).

*** DATABASE IMPACT: ONLY ONE COLUMN IS EVER MODIFIED ***
  - ONLY the column "reference_number" in the table "procurement_receipt_entries"
    is updated (copy of value from procurement_item_requests.receipt_reference_number).
  - NO other columns in procurement_receipt_entries are touched.
  - NO other tables are modified. procurement_item_requests is READ-ONLY (we only
    read receipt_reference_number to copy into procurement_receipt_entries.reference_number).

Usage: python scripts/populate_receipt_entry_reference_numbers.py

Example: receipt with item_request_id=202 gets the same reference_number
         as procurement_item_requests.id=202.receipt_reference_number.
"""

import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from config import Config
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
    if os.name == "nt":
        db_path = db_path.replace("/", "\\")

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    print(f"Using database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Find receipt entries with empty reference_number
        cursor.execute("""
            SELECT pre.id, pre.item_request_id, pre.reference_number
            FROM procurement_receipt_entries pre
            WHERE pre.reference_number IS NULL OR trim(pre.reference_number) = ''
        """)
        entries_to_update = cursor.fetchall()

        if not entries_to_update:
            print("No receipt entries with empty reference_number found. Nothing to do.")
            return

        print(f"Found {len(entries_to_update)} receipt entry/entries with empty reference_number.")

        # READ-ONLY from procurement_item_requests (no changes to that table).
        updated = 0
        skipped_no_ref = 0
        for row in entries_to_update:
            entry_id = row["id"]
            item_request_id = row["item_request_id"]
            # Only read from procurement_item_requests; do not modify it.
            cursor.execute(
                "SELECT receipt_reference_number FROM procurement_item_requests WHERE id = ?",
                (item_request_id,),
            )
            req = cursor.fetchone()
            ref = (req["receipt_reference_number"] or "").strip() if req else ""

            # ONLY write: procurement_receipt_entries.reference_number (no other column, no other table).
            cursor.execute(
                "UPDATE procurement_receipt_entries SET reference_number = ? WHERE id = ?",
                (ref, entry_id),
            )
            if ref:
                updated += 1
                print(f"  Entry id={entry_id} (item_request_id={item_request_id}) -> reference_number='{ref}'")
            else:
                skipped_no_ref += 1
                print(f"  Entry id={entry_id} (item_request_id={item_request_id}) -> no ref on request, set to ''")

        conn.commit()
        print(f"\nDone. Updated {updated} entries with reference numbers; {skipped_no_ref} left empty (no ref on request).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

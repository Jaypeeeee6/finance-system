"""
Temporary script: Add procurement categories and items for the "Branch" department
by copying from the "Operation" department. Run once from project root:

    python copy_operation_procurement_to_branch.py

Safe to run multiple times: only copies categories/items that don't already exist
for Branch (by name). Existing Branch categories/items are left unchanged.
"""

import os
import sys

# Project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, ProcurementCategory, ProcurementItem

SOURCE_DEPARTMENT = "Operation"
TARGET_DEPARTMENT = "Branch"


def main():
    with app.app_context():
        # Fetch Operation categories and items
        op_categories = (
            ProcurementCategory.query.filter_by(department=SOURCE_DEPARTMENT)
            .order_by(ProcurementCategory.id)
            .all()
        )
        op_items = (
            ProcurementItem.query.filter_by(department=SOURCE_DEPARTMENT)
            .order_by(ProcurementItem.id)
            .all()
        )

        if not op_categories and not op_items:
            print(f"No procurement categories or items found for department '{SOURCE_DEPARTMENT}'. Nothing to copy.")
            return

        # Existing Branch category names and item (name, category_id) for skip logic
        existing_branch_cat_names = {
            c.name for c in ProcurementCategory.query.filter_by(department=TARGET_DEPARTMENT).all()
        }
        existing_branch_items = {
            (i.name, i.category_id) for i in ProcurementItem.query.filter_by(department=TARGET_DEPARTMENT).all()
        }

        # Map: Operation category id -> Branch category id (we build this as we create)
        op_to_branch_category_id = {}

        added_categories = 0
        for op_cat in op_categories:
            if op_cat.name in existing_branch_cat_names:
                # Find existing Branch category with this name for mapping
                branch_cat = (
                    ProcurementCategory.query.filter_by(department=TARGET_DEPARTMENT, name=op_cat.name).first()
                )
                if branch_cat:
                    op_to_branch_category_id[op_cat.id] = branch_cat.id
                continue
            new_cat = ProcurementCategory(
                name=op_cat.name,
                department=TARGET_DEPARTMENT,
                is_active=op_cat.is_active,
                created_by_user_id=op_cat.created_by_user_id,
            )
            db.session.add(new_cat)
            db.session.flush()  # so new_cat.id is set
            op_to_branch_category_id[op_cat.id] = new_cat.id
            existing_branch_cat_names.add(op_cat.name)
            added_categories += 1
            print(f"  Added category: {op_cat.name}")

        db.session.commit()
        if added_categories:
            print(f"Added {added_categories} procurement categor(y/ies) for '{TARGET_DEPARTMENT}'.")
        else:
            print(f"No new categories added for '{TARGET_DEPARTMENT}' (already present).")

        # Create Branch items (same name, description, is_active; category -> Branch category)
        added_items = 0
        for op_item in op_items:
            branch_cat_id = op_to_branch_category_id.get(op_item.category_id) if op_item.category_id else None
            if (op_item.name, branch_cat_id) in existing_branch_items:
                continue
            new_item = ProcurementItem(
                name=op_item.name,
                department=TARGET_DEPARTMENT,
                category_id=branch_cat_id,
                description=op_item.description,
                is_active=op_item.is_active,
                created_by_user_id=op_item.created_by_user_id,
            )
            db.session.add(new_item)
            existing_branch_items.add((op_item.name, branch_cat_id))
            added_items += 1
            print(f"  Added item: {op_item.name} (category_id={branch_cat_id})")

        db.session.commit()
        if added_items:
            print(f"Added {added_items} procurement item(s) for '{TARGET_DEPARTMENT}'.")
        else:
            print(f"No new items added for '{TARGET_DEPARTMENT}' (already present).")

        print("Done.")


if __name__ == "__main__":
    main()

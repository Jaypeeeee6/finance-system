#!/usr/bin/env python3
"""
One-time script to add ProcurementItems for the Operation department.

Usage:
  python scripts/one_time_add_procurement_items_operation.py [--dry-run]

Run with --dry-run to see what would be created without committing.
After running successfully on production, delete this file.
"""
from __future__ import annotations

import sys
from typing import Dict, List

from sqlalchemy.exc import SQLAlchemyError

from app import app, db
from models import ProcurementCategory, ProcurementItem


CATEGORIES_TO_ADD: Dict[str, List[str]] = {
    "Kitchen": [
        "JUICE BLENDER (500ML)",
        "PLASTIC JAG COVER (2L)",
        "JUICE BLENDER JUG 5000ML",
        "BER SPOON",
        "JUICE CUP HOLDER",
        "MEASUREMENT CUP (SET)",
        "MEASUREMENT MUG",
        "MEASUREMENT SPOON (1/4) SET",
        "TONG",
        "FORTE SLOTTED SPATULA STAINLESS STEEL",
        "STAINLESS STEEL SERVING SPOON BIG",
        "SOUP LADLE 3 OZ SIZE",
        "STAINLESS STEEL BURGER SMASHER CIRCULAR",
        "STAINLESS STEEL FRENCH FRY SCOOP",
        "SHARPING STONE",
        "SPATULA WOODEN",
        "PLASTIC SPATULA (40CM)",
        "STAINLESS STEEL SALT SHAKER TOP FULLY HOLE",
        "TIMER",
        "GAS LIGHTER",
        "BRUSH FOR BREAD POLISH",
        "GRILL CLEANING BRUSH TRIANGLE",
        "FRYER CLEANING BRUSH",
        "STAINLESS STEEL ALLOY SCOOP MEDUIM SIZE",
        "STAINLESS STEEL SPOON WITH HOLES (3OZ)",
        "FRYING PAN FOR PASTA (20CM)",
        "FRYING PAN FOR PASTA (30CM)",
        "STAINLESS STEEL COOKING POT (30CM)",
        "STAINLESS STEEL TREY 40*30",
        "STAINLESS STEEL CONTAINERS WITH COVER (1 /1 15 CM)",
        "STAINLESS STEEL CONTAINERS WITH HOLES WITH COVER (1/1 15CM)",
        "STAINLES STEEL CONTAINERS WITH COVER (1/2 15CM)",
        "STAINLESS STEEL CONTAINER WITH HOLES WITH COVER (1/2 15CM)",
        "STAINLES STEEL CONTAINERS WITH COVER (1/3 15CM)",
        "STAINLESS STEEL CONTAINERS WITH HOLES WITH COVER (1/3 15 CM)",
        "STAINLESS STEEL CONTAINERS WITH COVER (1/6 15CM)",
        "STAINLESS STEEL FOOD KIPPER (3KG)",
        "SPICE BOX 4IN1",
        "STAINLESS STEEL BOWL (10L)",
        "STAINLESS STEEL COLANDER STRAINER 30CM",
        "STAINLESS STEEL STRAINER 11 INCHES WITH HANDLE",
        "STAINLESS STEEL STRAINER 7 INCHES WITH HANDLE",
        "STAINLESS STEEL STRAINER SMALL 7 INCHES WITH LONG HANDLE",
        "STAINLESS STEEL STRAINER SQUARE SHAPE 40*25CM",
        "STAINLESS STEEL STRAINER FOR CRISPY (27*37)CM",
        "STAINLESS STEEL STRAINER FOR DRAINAGE (10X10) INCHES",
        "POLYCARBONATED GN CONTAINER WITH COVER 1/2 (15CM)",
        "YELLOW CHOPPING BOARD BIG (60/40)",
        "YELLOOW CHOPPING BOARD SMALL (40/30)",
        "GREEN CHOPPING BOARD BIG (60/40)",
        "GREEN CHOPPING BOARD SMALL (40/30)",
        "RED CHOPPING BOARD BIG (60/40)",
        "RED CHOPPING BOARD SMALL (40/30)",
        "CHOPPING BOARD STAND",
        "GREEN KNIFE BIG (12INCH)",
        "YELLOW KNIFE BIG (12INCH)",
        "RED KNIFE BIG (12INCH)",
        "BREAD KNIFE BIG (12 INCH)",
        "BREAD KNIFE SMALL",
        "DINING TREY BIG",
        "DINING TREY MEDUIM",
        "DINING TREY SMALL",
        "DINING PLATE FOR FRIES",
        "DINING PLATE FOR BURGER",
        "DINING CUP FOR EXTRA SAUCE (2OZ)",
        "SQUEEZER BOTTLE YELLOW BIG 1000ML",
        "SQUEEZER BOTTLE RED BIG 1000ML",
        "SQUEEZAR BOTTLE WHITE BIG 1000ML",
        "WHISK",
        "BIG WHITE SCALE (30/40KG)",
        "SMALL WEIGHT SCALE (IN TOP GLASS)",
        "BAIN MARIE (56*35)",
        "FRIES WARMER",
        "CABBAGE CUTER MACHINE",
        "GARLIC PEELER MACHINE",
        "ONION/MUSHROOM CUTTER",
        "PATTY PRESSER MACHINE BIG",
        "CAN OPENER",
        "TROLLY HEAVY BIG SIZE",
        "LADDER",
        "EXTENSION BOARD HEAVY DUTY",
        "PALETTE",
        "DRAINAGE CLEANING ACID",
        "SAFETY GLOVES",
        "TISSUE DISPENSER",
        "BROOM HOLDER",
    ],
    "Stationery": [
        "DUSTBIN BIG OPEN WITH LEG 120L",
        "DUSTBIN MEDUIM OPEN WITH LEG 60L",
        "DUSTBIN SMALL OPEN WITH LEG 40L",
        "DUSTBIN SMALL WITH LEG 40L FOR DINING AREA TOILET",
        "DUSTPAN WITH STICK BRUSH",
        "GRABBER TOOL",
    ],
}


def add_items(dry_run: bool = False) -> None:
    """Add categories and items to the DB under the Operation department."""
    department = "Operation"
    with app.app_context():
        for category_name, item_names in CATEGORIES_TO_ADD.items():
            normalized_category_name = category_name.strip()
            # Find or create category
            category = ProcurementCategory.query.filter_by(
                name=normalized_category_name, department=department
            ).first()
            if category:
                print(f"Found existing category: {category.name} (id={category.id})")
            else:
                print(f"Creating category: {normalized_category_name}")
                if not dry_run:
                    category = ProcurementCategory(
                        name=normalized_category_name,
                        department=department,
                        is_active=True,
                        created_by_user_id=None,
                    )
                    db.session.add(category)
                    try:
                        db.session.commit()
                        print(f"  Created category id={category.id}")
                    except SQLAlchemyError as exc:
                        db.session.rollback()
                        print(f"  ERROR creating category {normalized_category_name}: {exc}", file=sys.stderr)
                        continue
                else:
                    # In dry-run mode we don't have an id; print and continue
                    print(f"  (dry-run) would create category: {normalized_category_name}")
                    # We cannot create items in dry-run without a category id, so continue to next category
                    continue

            # Add items for this category
            created_count = 0
            for name in item_names:
                item_name = name.strip()
                exists = ProcurementItem.query.filter_by(
                    name=item_name, department=department, category_id=category.id
                ).first()
                if exists:
                    print(f"  Skipping existing item: {item_name}")
                    continue
                print(f"  Adding item: {item_name}")
                if not dry_run:
                    new_item = ProcurementItem(
                        name=item_name,
                        category_id=category.id,
                        department=department,
                        is_active=True,
                        created_by_user_id=None,
                    )
                    db.session.add(new_item)
                    created_count += 1

            if not dry_run:
                try:
                    db.session.commit()
                    print(f"  Committed {created_count} new items for category {category.name}")
                except SQLAlchemyError as exc:
                    db.session.rollback()
                    print(f"  ERROR committing items for {category.name}: {exc}", file=sys.stderr)

    print("Script finished.")


def parse_args() -> bool:
    """Return True if dry-run was requested via CLI."""
    return "--dry-run" in sys.argv or "-n" in sys.argv


if __name__ == "__main__":
    dry = parse_args()
    if dry:
        print("Running in dry-run mode. No changes will be committed.")
    add_items(dry_run=dry)



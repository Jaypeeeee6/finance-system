#!/usr/bin/env python3
"""Seed flat branches from a list of (name, flat_code) pairs.

Parses each flat code to derive parent branch code, floor, flat, or villa number,
then looks up the parent branch and creates a Branch with branch_type='flat'.

Usage (from project root):
  python scripts/seed_flats_from_codes.py
  python scripts/seed_flats_from_codes.py --db instance/payment_system.db
  python scripts/seed_flats_from_codes.py --dry-run   # print only, no DB writes
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# (display name, flat_code). Empty code => no parsing; record still added with placeholder location.
FLATS_DATA = [
    ("Boom Mabella 33", "B-MU002-F3F33"),
    ("Boom Mabella 34", "B-MU002-F3F34"),
    ("Boom Alkoud 104", "B-MU004-F1F104"),
    ("Boom Alkoud 106", "B-MU004-F1F106"),
    ("Boom Nizwa F.1F1", "B-DK001F1F1"),
    ("Boom Al Hail 13", "B-MU003-F1F13"),
    ("Boom Al Hail 15", "B-MU003-F1F15"),
    ("Thoum Al khuwair 407", "T-MU001-F4F407"),
    ("Thoum Al khuwair 402", "T-MU001-F4F402"),
    ("Thoum Mabella 13", "T-MU002-F1F13"),
    ("Thoum Mabella 14", "T-MU002-F1F14"),
    ("Thoum Sohar", "T-BA001-V64"),
    ("Kucu Al Amrat : flat 13", "K-MU003-F1F13"),
    ("Kucu Al Amrat : flat 18", "K-MU003-F1F18"),
    ("Kucu Al khuwair 303", "K-MU004-F1F303"),
    ("Kucu Al khuwair 205", "K-MU004-F1F205"),
    ("Kucu Al khuwair , New  401", "K-MU009-F4F401"),
    ("Kucu Avenues Mall 504", "K-MU007-F5F504"),
    ("Kucu Oman Mall 11", "K-MU005-F1F11"),
    ("Kucu Oman Mall 44", "K-MU005-F4F44"),
    ("Kucu Al Mouj 12", "K-MU006-F1F12"),
    ("Kucu Al Mouj 32", "K-MU006-F3F32"),
    ("Kucu Alkoud New/2", "K-MU001-F1F2"),
    ("Kucu Alkoud 14 Up Tea time", "K-MU001-F1F14"),
    ("Kucu Mawalih 51", "K-MU008-F5F51"),
    ("Kucu Mawalih 14", "K-MU008-F1F14"),
    ("Kucu Mabella 31", "K-MU002-F3F31"),
    ("Kucu Mabella 30", "K-MU002-F3F30"),
    ("Kucu Barka 6", "K-BA005-F1F6"),
    ("Kucu Barka 15", "K-BA005-F1F15"),
    ("Kucu Al-Musanaa 3", "K-BA006-F1F3"),
    ("Kucu Al-Musanaa 4", "K-BA006-F1F4"),
    ("Kucu Al-Musanaa 5", "K-BA006-F1F5"),
    ("Kucu Albidaya F1 F.1", "K-BA004-F1F1"),
    ("Kucu Albidaya F1 F.4", "K-BA004-F1F4"),
    ("Kucu Rustaq 1", "K-BA003-F1F1"),
    ("Kucu Rustaq 2", "K-BA003-F1F2"),
    ("Kucu Sohar gate 1", "K-BA001-F1F1"),
    ("Kucu Sohar City Centr 67", "K-BA002-F6F67"),
    ("Kucu Nizwa F.2 F2", "K-DA001-F2F2"),
    ("Kucu Nizwa F.2 F3", "K-DA001-F2F3"),
    ("Kucu Alaqar F1.F2", "K-DK002-F1F2"),
    ("Kucu Sur 1", "K-SH001-F1F1"),
    ("Kucu Sur 4", "K-SH001-F1F4"),
    ("Administrative staff 101", "O-F1F101"),
    ("G&D FLAT 53", ""),
    ("R&R FLAT 83", ""),
    ("Kucu Al Qurum 404", "K-MU010-F4F404"),
    ("Kucu Shinas 1", "K-BA007-F1F1"),
    ("Kucu Shinas 2", "K-BA007-F1F2"),
    ("Kucu Ibri V N.O 3", "K-DH001-V3"),
]


def parse_flat_code(code):
    """
    Parse flat code into branch_code (parent), and either (floor_number, flat_number) or villa_number.
    - Villa: ...-V123 or ...V123 at end -> branch_code, villa_number.
    - Flat: ...-F3F33 or ...F1F1 at end -> branch_code, floor_number, flat_number.
    Returns dict or None if code is empty/invalid.
    """
    code = (code or "").strip()
    if not code:
        return None
    # Villa: -V123 at end
    m = re.search(r"-V(\d+)$", code)
    if m:
        return {
            "branch_code": code[: m.start()].rstrip("-"),
            "villa_number": str(m.group(1)),
            "floor_number": None,
            "flat_number": None,
        }
    # Flat: -F3F33 or F1F1 at end (e.g. B-DK001F1F1)
    m = re.search(r"-?F(\d+)F(\d+)$", code, re.IGNORECASE)
    if m:
        branch_code = code[: m.start()].rstrip("-")
        return {
            "branch_code": branch_code,
            "floor_number": m.group(1),
            "flat_number": m.group(2),
            "villa_number": None,
        }
    return None


def resolve_parent_branch(Branch, branch_code):
    """Resolve parent branch by branch_code. For 'O' also try restaurant 'Office'."""
    branch = Branch.query.filter(
        (Branch.branch_type == None) | (Branch.branch_type == "branch"),
        Branch.branch_code == branch_code,
    ).first()
    if branch:
        return branch
    if branch_code == "O":
        branch = Branch.query.filter(
            (Branch.branch_type == None) | (Branch.branch_type == "branch"),
            Branch.restaurant.ilike("%Office%"),
        ).first()
        return branch
    return None


def main():
    p = argparse.ArgumentParser(
        description="Seed flat branches from name/code list; parse codes for parent, floor, flat, villa"
    )
    p.add_argument(
        "--db",
        default=None,
        help="Path to SQLite DB (default: use Flask app config)",
    )
    p.add_argument("--dry-run", action="store_true", help="Only print what would be created")
    args = p.parse_args()

    if args.db:
        db_path = os.path.abspath(args.db).replace("\\", "/")
        os.environ["DATABASE_URL"] = "sqlite:///" + db_path
        if not os.path.exists(args.db):
            print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
            sys.exit(1)

    from app import app
    from models import db, Branch

    with app.app_context():
        created = 0
        skipped_dup = 0
        skipped_no_parent = 0
        skipped_no_code = 0

        for name, flat_code in FLATS_DATA:
            name = (name or "").strip()
            if not name:
                continue

            if not (flat_code or "").strip():
                # No code: add flat with placeholder location, no parent/code/numbers
                if Branch.query.filter_by(name=name, branch_type="flat").first():
                    skipped_dup += 1
                    continue
                print(
                    f"{'Would create' if args.dry_run else 'Create'} (no code): {name!r} -> restaurant=Unassigned"
                )
                if not args.dry_run:
                    branch = Branch(
                        name=name,
                        restaurant="Unassigned",
                        branch_type="flat",
                        branch_code=None,
                        parent_branch_id=None,
                        accommodation_type=None,
                        floor_number=None,
                        flat_number=None,
                        villa_number=None,
                        is_active=True,
                    )
                    db.session.add(branch)
                    created += 1
                continue

            parsed = parse_flat_code(flat_code)
            if not parsed:
                print(f"Skip (unparseable code): {name!r} -> {flat_code!r}", file=sys.stderr)
                skipped_no_code += 1
                continue

            parent = resolve_parent_branch(Branch, parsed["branch_code"])
            if not parent:
                print(
                    f"Skip (no parent branch for code {parsed['branch_code']!r}): {name!r}",
                    file=sys.stderr,
                )
                skipped_no_parent += 1
                continue

            existing = Branch.query.filter_by(branch_code=flat_code).first()
            if existing:
                skipped_dup += 1
                continue

            accommodation = "Villa" if parsed.get("villa_number") else "Flat"
            parent_desc = f"{parent.branch_code or 'no-code'} ({parent.restaurant})"
            print(
                f"{'Would create' if args.dry_run else 'Create'}: {name!r} -> {flat_code!r} "
                f"parent={parent_desc} "
                f"floor={parsed.get('floor_number')} flat={parsed.get('flat_number')} villa={parsed.get('villa_number')}"
            )
            if not args.dry_run:
                branch = Branch(
                    name=name,
                    restaurant=parent.restaurant,
                    branch_type="flat",
                    branch_code=flat_code,
                    parent_branch_id=parent.id,
                    accommodation_type=accommodation,
                    floor_number=parsed.get("floor_number"),
                    flat_number=parsed.get("flat_number"),
                    villa_number=parsed.get("villa_number"),
                    is_active=True,
                )
                db.session.add(branch)
                created += 1

        if not args.dry_run and created:
            db.session.commit()
            print(f"Committed: {created} flat(s) created.")
        if skipped_dup:
            print(f"Skipped (already exists): {skipped_dup}")
        if skipped_no_parent:
            print(f"Skipped (no parent branch): {skipped_no_parent}")
        if skipped_no_code:
            print(f"Skipped (unparseable code): {skipped_no_code}")


if __name__ == "__main__":
    main()

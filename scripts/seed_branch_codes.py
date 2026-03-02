#!/usr/bin/env python3
"""Add branch_code and region to existing branches from a fixed order list.

Branch names and order match production. Format: BrandLetter-RegionCodeNNN
(e.g. K-MU001). If a branch is not in the local DB, it is skipped.

Ensure the regions table is seeded first (scripts/migrate_create_regions_table.py)
so that Muscat, Al Batinah, Al Dakhilia, Al Sharqiah, Al Dhahira (and Al Maabilah)
exist; otherwise branches in missing regions will be skipped.

Usage (from project root):
  python scripts/seed_branch_codes.py
  python scripts/seed_branch_codes.py --db instance/payment_system.db
  python scripts/seed_branch_codes.py --dry-run   # print only, no DB writes
"""
import argparse
import os
import sys

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ordered list: (branch_name, restaurant, region) - names as in production DB.
# Order within each region+restaurant defines the sequence (001, 002, ...).
BRANCHES_ORDERED = [
    # Muscat
    ('Kucu Al Khoud', 'Kucu', 'Muscat'),
    ('Kucu Al Maabilah Nuzha', 'Kucu', 'Muscat'),
    ('Kucu Al Amerat', 'Kucu', 'Muscat'),
    ('Kucu Al Khwair (take away)', 'Kucu', 'Muscat'),
    ('Kucu Mall of Oman', 'Kucu', 'Muscat'),
    ('Kucu North Al Mawaleh', 'Kucu', 'Muscat'),
    ('Kucu Avenues Mall', 'Kucu', 'Muscat'),
    ('Kucu South Al Mawaleh', 'Kucu', 'Muscat'),
    ('Kucu Al Khwair (dine in)', 'Kucu', 'Muscat'),
    ('Kucu City Center Al Qurum', 'Kucu', 'Muscat'),
    ('Kucu Yas', 'Kucu', 'Muscat'),
    ('Mishmisha Al Khoud', 'Mishmisha', 'Muscat'),
    ('Thoum Al Khwair', 'Thoum', 'Muscat'),
    ('Thoum Al Maabilah', 'Thoum', 'Muscat'),
    ('Thoum Alhail (cloud kitchen)', 'Thoum', 'Muscat'),
    ('Boom Al Maabilah', 'Boom', 'Muscat'),
    ('Boom Al Hail', 'Boom', 'Muscat'),
    ('Boom Al Khoud', 'Boom', 'Muscat'),
    ('Boom Al Khwair (cloud kitchen)', 'Boom', 'Muscat'),
    # Al Batinah
    ('Kucu Sohar Gate', 'Kucu', 'Al Batinah'),
    ('Kucu City Center Sohar', 'Kucu', 'Al Batinah'),
    ('Kucu Rustaq', 'Kucu', 'Al Batinah'),
    ('Kucu Swaiq', 'Kucu', 'Al Batinah'),
    ('Kucu Barka', 'Kucu', 'Al Batinah'),
    ('Kucu Musannah', 'Kucu', 'Al Batinah'),
    ('Kucu Shinas', 'Kucu', 'Al Batinah'),
    ('Thoum Sohar Gate', 'Thoum', 'Al Batinah'),
    ('Boom Sohar Gate (cloud kitchen)', 'Boom', 'Al Batinah'),
    # Al Dakhilia
    ('Kucu Nizwa', 'Kucu', 'Al Dakhilia'),
    ('Kucu Al Aqr', 'Kucu', 'Al Dakhilia'),
    ('Boom Nizwa', 'Boom', 'Al Dakhilia'),
    ('Thoum Nizwa (cloud kitchen)', 'Thoum', 'Al Dakhilia'),
    # Al Sharqiah
    ('Kucu Sur', 'Kucu', 'Al Sharqiah'),
    # Al Dhahira
    ('Kucu Ibri', 'Kucu', 'Al Dhahira'),
]


def main():
    p = argparse.ArgumentParser(description='Seed branch_code and region for existing branches')
    p.add_argument('--db', default=None, help='Path to SQLite DB (default: use Flask app config)')
    p.add_argument('--dry-run', action='store_true', help='Only print what would be updated')
    args = p.parse_args()

    if args.db:
        os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.abspath(args.db).replace('\\', '/')
        if not os.path.exists(os.path.abspath(args.db)):
            print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
            sys.exit(1)

    from app import app, get_region_code
    from models import db, Branch

    with app.app_context():
        # Compute sequence per (region, restaurant) and build branch_code for each
        seq_per_key = {}
        codes_to_apply = []
        for name, restaurant, region in BRANCHES_ORDERED:
            key = (region, restaurant)
            seq = seq_per_key.get(key, 0) + 1
            seq_per_key[key] = seq
            brand_letter = (restaurant.strip() or 'X')[0].upper()
            region_code = get_region_code(region)
            if not region_code:
                print(f"WARNING: No region code for region '{region}'; skipping branch '{name}'", file=sys.stderr)
                continue
            branch_code = f'{brand_letter}-{region_code}{seq:03d}'
            codes_to_apply.append((name, restaurant, region, branch_code))

        updated = 0
        skipped_not_found = 0
        for name, restaurant, region, branch_code in codes_to_apply:
            branch = Branch.query.filter_by(name=name).first()
            if not branch:
                print(f"Skip (not in DB): {name!r}")
                skipped_not_found += 1
                continue
            if branch.branch_code == branch_code and branch.region == region:
                continue
            print(f"{'Would update' if args.dry_run else 'Update'}: {name!r} -> {branch_code}  region={region!r}")
            if not args.dry_run:
                branch.branch_code = branch_code
                branch.region = region
                updated += 1
        if not args.dry_run and updated:
            db.session.commit()
            print(f"Committed: {updated} branch(es) updated.")
        if skipped_not_found:
            print(f"Skipped (not in DB): {skipped_not_found} branch(es).")


if __name__ == '__main__':
    main()

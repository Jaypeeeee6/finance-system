#!/usr/bin/env python3
"""Quick script to check database structure"""
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    
    print("=" * 60)
    print("DEPARTMENT_TEMPORARY_MANAGERS TABLE STRUCTURE")
    print("=" * 60)
    
    # Get columns
    columns = inspector.get_columns('department_temporary_managers')
    print("\nColumns:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']} (nullable: {not col['nullable']}, default: {col['default']})")
    
    # Get indexes/constraints
    indexes = inspector.get_indexes('department_temporary_managers')
    print("\nIndexes/Constraints:")
    for idx in indexes:
        print(f"  - {idx['name']}: columns={idx['column_names']}, unique={idx['unique']}")
    
    # Get foreign keys
    fks = inspector.get_foreign_keys('department_temporary_managers')
    print("\nForeign Keys:")
    for fk in fks:
        print(f"  - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Get table SQL
    print("\n" + "=" * 60)
    print("CREATE TABLE STATEMENT:")
    print("=" * 60)
    result = db.session.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='department_temporary_managers'"))
    sql = result.fetchone()
    if sql:
        print(sql[0])
    
    print("\n" + "=" * 60)
    print("CURRENT DATA:")
    print("=" * 60)
    result = db.session.execute(text("""
        SELECT id, request_type, department, temporary_manager_id, set_by_user_id, set_at
        FROM department_temporary_managers
        ORDER BY department, request_type
    """))
    rows = result.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Request Type: {row[1]}, Department: {row[2]}, Manager ID: {row[3]}, Set By: {row[4]}, Set At: {row[5]}")

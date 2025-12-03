# Database Migration Guide: Location Priorities Feature

## Overview
This document describes the database changes required to deploy the Location Priorities feature.

---

## 1. Database Schema Changes

### New Table: `location_priorities`

The system now requires a new table to store location priorities. This table will be created automatically when you run the application (via `db.create_all()`), but here's the SQL for manual creation if needed:

#### For SQLite:
```sql
CREATE TABLE location_priorities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name VARCHAR(100) NOT NULL UNIQUE,
    priority INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_location_priorities_priority ON location_priorities(priority);
CREATE INDEX idx_location_priorities_active ON location_priorities(is_active);
```

#### For PostgreSQL:
```sql
CREATE TABLE location_priorities (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL UNIQUE,
    priority INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_location_priorities_priority ON location_priorities(priority);
CREATE INDEX idx_location_priorities_active ON location_priorities(is_active);
```

#### For MySQL:
```sql
CREATE TABLE location_priorities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL UNIQUE,
    priority INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by_user_id INT,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_location_priorities_priority ON location_priorities(priority);
CREATE INDEX idx_location_priorities_active ON location_priorities(is_active);
```

---

## 2. Automatic Table Creation

**Good News:** If you're using Flask-SQLAlchemy's `db.create_all()`, the table will be created automatically when you start the application. The code in `app.py` already includes:

```python
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
```

This will automatically create the `location_priorities` table based on the `LocationPriority` model defined in `models.py`.

---

## 3. Automatic Initialization (NEW - No Manual Script Needed!)

### Is manual script necessary?

**NO** - The initialization now happens **automatically** when the application starts! 

The app will automatically:
1. Create the `location_priorities` table (if it doesn't exist)
2. Scan all existing locations from the `branches` table
3. Create location priority entries for any locations that don't have priorities yet
4. Assign default priorities matching the old hardcoded order

**This is completely safe:**
- ✅ Only **reads** from `branches` table (no modifications)
- ✅ Only **inserts** into `location_priorities` table (new table)
- ✅ **Never modifies** `branches` or `payment_requests` tables
- ✅ **Existing requests are completely unaffected**
- ✅ Idempotent (safe to run on every startup - skips existing entries)

### Optional: Manual Script `init_location_priorities.py`

The script is now **optional** and only needed if you want to manually initialize or re-initialize location priorities. The automatic initialization handles everything on app startup.

### Purpose:

1. **Data Migration**: Populates the new `location_priorities` table with entries for all existing locations found in your `branches` table
2. **Default Priorities**: Sets default priority values matching the old hardcoded order:
   - Office: 1
   - Kucu: 2
   - Boom: 3
   - Thoum: 4
   - Kitchen: 5
   - Other locations: 999 (appear last)
3. **Idempotent**: Safe to run multiple times - it skips locations that already have priority entries

### When to run it:

- **After deploying the code** to your server
- **Before users start using the new location management features**
- **Only once** (or whenever you add new locations that don't have priorities yet)

### How to run it:

```bash
# On the server
python init_location_priorities.py
```

Or if using a virtual environment:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
python init_location_priorities.py
```

### What it does:

1. Scans all unique location names from the `branches` table
2. Creates `LocationPriority` entries for each location
3. Assigns default priorities based on the old hardcoded order
4. Skips locations that already have priority entries (safe to re-run)
5. Displays a summary of what was created

### Example Output:

```
============================================================
Location Priorities Initialization Script
============================================================

Initializing location priorities...
Found 5 unique locations: Office, Kucu, Boom, Thoum, Kitchen
  ✓ Created 'Office' with priority 1
  ✓ Created 'Kucu' with priority 2
  ✓ Created 'Boom' with priority 3
  ✓ Created 'Thoum' with priority 4
  ✓ Created 'Kitchen' with priority 5

✓ Successfully created 5 location priorities

Current location priorities (ordered by priority):
  1. Office (Active)
  2. Kucu (Active)
  3. Boom (Active)
  4. Thoum (Active)
  5. Kitchen (Active)

============================================================
Initialization completed successfully!
============================================================
```

---

## 4. Deployment Steps

### Step 1: Deploy Code
- Upload all modified files to the server
- Ensure `models.py` includes the `LocationPriority` model
- Ensure `app.py` includes the new routes and helper functions

### Step 2: Create Database Table
The table will be created automatically when you start the application, OR you can run:
```python
from app import app, db
from models import LocationPriority

with app.app_context():
    db.create_all()
```

### Step 3: Automatic Initialization
**No action needed!** The app will automatically initialize location priorities on startup.

The system will:
- Automatically detect existing locations from the `branches` table
- Create location priority entries with default priorities
- Skip locations that already have priorities (safe to restart multiple times)

**Optional:** If you want to manually run the initialization script:
```bash
python init_location_priorities.py
```
But this is **not required** - it happens automatically!

### Step 4: Verify
- Check the IT Dashboard → Branches/Locations tab
- Verify locations appear with correct priorities
- Test creating/editing locations

---

## 5. No Data Loss

**Important:** This migration:
- ✅ Does NOT modify existing `branches` table
- ✅ Does NOT delete any data
- ✅ Only ADDS a new table
- ✅ Only ADDS new records to the new table
- ✅ Is completely safe and reversible

---

## 6. Rollback (if needed)

If you need to rollback:

1. **Remove the code changes** (revert to previous version)
2. **Drop the table** (optional, if you want to clean up):
   ```sql
   DROP TABLE IF EXISTS location_priorities;
   ```

The system will fall back to alphabetical ordering if no priorities exist.

---

## 7. Summary

| Item | Required? | When? |
|------|-----------|-------|
| Database table creation | ✅ Yes | Automatically on app start |
| Run `init_location_priorities.py` | ❌ **No** | **Automatic on startup** |
| Upload script to server | ❌ Optional | Only if you want manual control |

---

## Questions?

- The table is created automatically via SQLAlchemy
- **Location priorities are initialized automatically on app startup** - no manual script needed!
- The automatic initialization is **completely safe** - it only reads from `branches` and inserts into `location_priorities`
- **Existing payment requests are NOT affected** - we never modify the `branches` or `payment_requests` tables
- The initialization is idempotent (safe to run on every startup - skips existing entries)
- The manual script (`init_location_priorities.py`) is optional and only for manual control if needed


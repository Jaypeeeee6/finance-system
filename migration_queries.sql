-- SQLite Migration Queries for department_temporary_managers Table
-- =================================================================
-- NEW COLUMN AND CONSTRAINT ADDED
-- =================================================================

-- 1. Add the new request_type column
ALTER TABLE department_temporary_managers 
ADD COLUMN request_type VARCHAR(100);

-- 2. Set default value for existing rows (if any)
UPDATE department_temporary_managers 
SET request_type = 'Both Payment and Item Request' 
WHERE request_type IS NULL;

-- 3. Add the composite unique constraint (department, request_type)
--    Note: SQLite doesn't support ALTER TABLE to add unique constraints directly,
--    so the table must be recreated. Here's the complete process:

-- Step 3a: Create new table with the unique constraint
CREATE TABLE department_temporary_managers_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_type VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    temporary_manager_id INTEGER NOT NULL,
    set_by_user_id INTEGER,
    set_at DATETIME,
    FOREIGN KEY (temporary_manager_id) REFERENCES users(user_id),
    FOREIGN KEY (set_by_user_id) REFERENCES users(user_id),
    UNIQUE(department, request_type)
);

-- Step 3b: Copy all data from old table to new table
INSERT INTO department_temporary_managers_new 
(id, request_type, department, temporary_manager_id, set_by_user_id, set_at)
SELECT id, request_type, department, temporary_manager_id, set_by_user_id, set_at
FROM department_temporary_managers;

-- Step 3c: Drop the old table
DROP TABLE department_temporary_managers;

-- Step 3d: Rename new table to original name
ALTER TABLE department_temporary_managers_new 
RENAME TO department_temporary_managers;

-- =================================================================
-- VERIFICATION QUERIES
-- =================================================================

-- Verify the request_type column exists:
SELECT name, type, notnull 
FROM pragma_table_info('department_temporary_managers') 
WHERE name = 'request_type';

-- Verify the unique constraint exists:
SELECT name, sql 
FROM sqlite_master 
WHERE type = 'index' 
AND name = 'unique_dept_request_type';

-- View all data with the new column:
SELECT id, request_type, department, temporary_manager_id, set_by_user_id, set_at
FROM department_temporary_managers
ORDER BY department, request_type;

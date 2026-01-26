-- SQLite Queries for Department Temporary Managers Table
-- ========================================================

-- 1. Check the table structure (all columns)
PRAGMA table_info(department_temporary_managers);

-- 2. Check if request_type column exists
SELECT name, type, notnull, dflt_value, pk 
FROM pragma_table_info('department_temporary_managers') 
WHERE name = 'request_type';

-- 3. View all unique constraints/indexes on the table
SELECT name, sql 
FROM sqlite_master 
WHERE type = 'index' 
AND tbl_name = 'department_temporary_managers';

-- 4. Check the unique constraint specifically
SELECT name, sql 
FROM sqlite_master 
WHERE type = 'index' 
AND name = 'unique_dept_request_type';

-- 5. View all data in department_temporary_managers table
SELECT 
    id,
    request_type,
    department,
    temporary_manager_id,
    set_by_user_id,
    set_at
FROM department_temporary_managers
ORDER BY department, request_type;

-- 6. View temporary managers with user names (join with users table)
SELECT 
    dt.id,
    dt.request_type,
    dt.department,
    dt.temporary_manager_id,
    u.name AS temporary_manager_name,
    dt.set_by_user_id,
    set_by.name AS set_by_name,
    dt.set_at
FROM department_temporary_managers dt
LEFT JOIN users u ON dt.temporary_manager_id = u.user_id
LEFT JOIN users set_by ON dt.set_by_user_id = set_by.user_id
ORDER BY dt.department, dt.request_type;

-- 7. Count temporary managers by request type
SELECT 
    request_type,
    COUNT(*) AS count
FROM department_temporary_managers
GROUP BY request_type;

-- 8. Count temporary managers by department
SELECT 
    department,
    COUNT(*) AS count
FROM department_temporary_managers
GROUP BY department
ORDER BY department;

-- 9. Find all temporary managers for a specific department (e.g., Office)
SELECT 
    dt.id,
    dt.request_type,
    dt.department,
    dt.temporary_manager_id,
    u.name AS temporary_manager_name
FROM department_temporary_managers dt
LEFT JOIN users u ON dt.temporary_manager_id = u.user_id
WHERE dt.department = 'Office'
ORDER BY dt.request_type;

-- 10. Find duplicate department+request_type combinations (should return empty if unique constraint works)
SELECT 
    department,
    request_type,
    COUNT(*) AS count
FROM department_temporary_managers
GROUP BY department, request_type
HAVING COUNT(*) > 1;

-- 11. Check for any NULL request_type values (should not exist after migration)
SELECT 
    id,
    department,
    request_type,
    temporary_manager_id
FROM department_temporary_managers
WHERE request_type IS NULL;

-- 12. View the complete table schema (CREATE TABLE statement)
SELECT sql 
FROM sqlite_master 
WHERE type = 'table' 
AND name = 'department_temporary_managers';

-- 13. Find all temporary managers for payment requests only
SELECT 
    dt.id,
    dt.department,
    dt.request_type,
    u.name AS temporary_manager_name
FROM department_temporary_managers dt
LEFT JOIN users u ON dt.temporary_manager_id = u.user_id
WHERE dt.request_type IN ('Finance Payment Request', 'Both Payment and Item Request')
ORDER BY dt.department;

-- 14. Find all temporary managers for item requests only
SELECT 
    dt.id,
    dt.department,
    dt.request_type,
    u.name AS temporary_manager_name
FROM department_temporary_managers dt
LEFT JOIN users u ON dt.temporary_manager_id = u.user_id
WHERE dt.request_type IN ('Procurement Item Request', 'Both Payment and Item Request')
ORDER BY dt.department;

-- 15. Find departments with both payment and item request temporary managers
SELECT 
    department,
    COUNT(DISTINCT request_type) AS request_types_count,
    GROUP_CONCAT(DISTINCT request_type) AS request_types
FROM department_temporary_managers
GROUP BY department
HAVING COUNT(DISTINCT request_type) > 1
ORDER BY department;

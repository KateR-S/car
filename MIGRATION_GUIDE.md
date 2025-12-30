# Migration Guide: Adding Touch Number Field

This guide explains how to migrate existing Neon database data to include the new `touch_number` field.

## Changes Made

A new `touch_number` field has been added to the `Touch` model and database schema:
- **Type**: INTEGER
- **Range**: 1 to MAX_TOUCHES_PER_PRACTICE (12)
- **Constraint**: UNIQUE per practice (one practice can only have one touch with number 2, for example)
- **Behavior**: Auto-suggested in the UI but editable by the user

## Migration Steps for Neon Database

If you have existing data in your Neon PostgreSQL database, follow these steps to migrate:

### Option 1: Manual SQL Migration (Recommended for Small Datasets)

Run the following SQL commands in your Neon database console:

```sql
-- Add the touch_number column (allows NULL initially)
ALTER TABLE touches ADD COLUMN touch_number INTEGER;

-- Assign touch numbers to existing touches
-- This assigns sequential numbers starting from 1 for each practice
WITH numbered_touches AS (
  SELECT 
    id,
    ROW_NUMBER() OVER (PARTITION BY practice_id ORDER BY id) as new_touch_number
  FROM touches
)
UPDATE touches
SET touch_number = numbered_touches.new_touch_number
FROM numbered_touches
WHERE touches.id = numbered_touches.id;

-- Make the column NOT NULL after populating data
ALTER TABLE touches ALTER COLUMN touch_number SET NOT NULL;

-- Add unique constraint
ALTER TABLE touches ADD CONSTRAINT unique_practice_touch_number UNIQUE(practice_id, touch_number);
```

### Option 2: Drop and Recreate (For Empty or Test Databases)

If your database has no important data, you can simply drop and recreate the touches table:

```sql
-- Drop the existing touches table
DROP TABLE touches;

-- The application will automatically recreate it with the new schema on next run
```

### Option 3: Backup and Restore with Transformation

For larger datasets:

1. **Backup existing data**:
```sql
-- Export touches to a backup
COPY touches TO '/tmp/touches_backup.csv' DELIMITER ',' CSV HEADER;
```

2. **Drop and recreate the table** (let the application create the new schema)

3. **Restore data with transformation**:
   - Load the CSV file
   - Transform the data to include touch_number (assign sequential numbers per practice)
   - Re-import into the new table structure

## JSON Backend Migration

For JSON file storage (`data/data.json`), you need to manually add the `touch_number` field to existing touch records:

1. **Backup your data file**:
```bash
cp data/data.json data/data.json.backup
```

2. **Edit `data/data.json`** and add `touch_number` to each touch:
```json
{
  "touches": [
    {
      "id": "touch-id-1",
      "practice_id": "practice-1",
      "method_id": "method-1",
      "touch_number": 1,
      "conductor_id": "employee-1",
      "bells": [...]
    },
    {
      "id": "touch-id-2",
      "practice_id": "practice-1",
      "method_id": "method-2",
      "touch_number": 2,
      "conductor_id": "employee-2",
      "bells": [...]
    }
  ]
}
```

3. **Assign sequential numbers** starting from 1 for touches within the same practice

## Verification

After migration, verify the changes:

1. **Check the schema**:
```sql
-- View the updated touches table structure
\d touches
```

2. **Verify data**:
```sql
-- Check that all touches have touch_numbers
SELECT practice_id, touch_number, method_id 
FROM touches 
ORDER BY practice_id, touch_number;
```

3. **Test the unique constraint**:
```sql
-- This should fail with a unique constraint violation
INSERT INTO touches (id, practice_id, method_id, touch_number, conductor_id, bells)
SELECT id || '_dup', practice_id, method_id, touch_number, conductor_id, bells
FROM touches LIMIT 1;
```

## Rollback

If you need to rollback the changes:

```sql
-- Remove the unique constraint
ALTER TABLE touches DROP CONSTRAINT IF EXISTS unique_practice_touch_number;

-- Remove the touch_number column
ALTER TABLE touches DROP COLUMN IF EXISTS touch_number;
```

## Notes

- The migration assigns touch numbers sequentially by the order of existing touch IDs
- If you have a specific ordering preference (e.g., by creation time or method name), modify the `ORDER BY` clause in the migration SQL
- The unique constraint ensures data integrity - you cannot have duplicate touch numbers within the same practice
- The UI will auto-suggest the next available touch number when creating new touches

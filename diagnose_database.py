"""
Diagnostic script to check if users table has all required columns.
Run this to verify database schema before/after migration.
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def check_users_table():
    """Check if users table has all required columns"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check what columns exist
            result = conn.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """))
            
            existing_columns = {row[0]: row for row in result}
            
            # Required columns
            required_columns = {
                'id': {'type': 'varchar', 'length': 36, 'nullable': 'NO'},
                'full_name': {'type': 'varchar', 'length': 255, 'nullable': 'NO'},
                'email': {'type': 'varchar', 'length': 255, 'nullable': 'NO'},
                'password_hash': {'type': 'varchar', 'length': 255, 'nullable': 'YES'},
                'google_id': {'type': 'varchar', 'length': 255, 'nullable': 'YES'},
                'created_at': {'type': 'timestamp', 'nullable': 'NO'},
                'updated_at': {'type': 'timestamp', 'nullable': 'NO'},
            }
            
            print("=" * 60)
            print("USERS TABLE DIAGNOSTIC")
            print("=" * 60)
            print(f"\nExisting columns: {list(existing_columns.keys())}")
            print(f"\nRequired columns: {list(required_columns.keys())}")
            print("\n" + "-" * 60)
            
            missing_columns = []
            incorrect_columns = []
            
            for col_name, col_spec in required_columns.items():
                if col_name not in existing_columns:
                    missing_columns.append(col_name)
                    print(f"❌ MISSING: {col_name}")
                else:
                    existing = existing_columns[col_name]
                    # Check if nullable matches
                    expected_nullable = col_spec['nullable']
                    actual_nullable = 'YES' if existing[3] == 'YES' else 'NO'
                    
                    if expected_nullable != actual_nullable and col_name in ['full_name']:
                        incorrect_columns.append(f"{col_name} (nullable should be {expected_nullable}, but is {actual_nullable})")
                        print(f"⚠️  WARNING: {col_name} nullable mismatch (expected {expected_nullable}, got {actual_nullable})")
                    else:
                        print(f"✅ EXISTS: {col_name} ({existing[1]})")
            
            # Check for old columns that should be removed
            old_columns = ['password']  # Old column name
            for old_col in old_columns:
                if old_col in existing_columns:
                    print(f"⚠️  OLD COLUMN FOUND: {old_col} (should be migrated to password_hash)")
            
            print("\n" + "=" * 60)
            
            if missing_columns:
                print(f"\n❌ MISSING COLUMNS: {', '.join(missing_columns)}")
                print("\nACTION REQUIRED: Run the migration to add missing columns:")
                print("   Option 1: alembic upgrade head")
                print("   Option 2: Run migration_add_full_name.sql in Railway PostgreSQL")
                return False
            elif incorrect_columns:
                print(f"\n⚠️  COLUMN ISSUES: {', '.join(incorrect_columns)}")
                print("\nACTION REQUIRED: Fix column constraints")
                return False
            else:
                print("\n✅ All required columns exist!")
                return True
                
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_users_table()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Database Migration: Add Foreign Key Constraint to profiles table
If profiles table exists without foreign key, this recreates it with proper constraints.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "food_scanner.db")

def migrate_profiles_table():
    """Ensure profiles table has proper foreign key relationship."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("🔍 Checking profiles table structure...")
        
        # Get current table info
        cursor.execute("PRAGMA table_info(profiles)")
        columns = cursor.fetchall()
        
        print(f"   Found {len(columns)} columns")
        
        # Check if foreign key constraint exists
        cursor.execute("PRAGMA foreign_key_list(profiles)")
        fk_list = cursor.fetchall()
        
        if fk_list:
            print("   ✅ Foreign key already exists")
            return
        
        print("   ⚠️  Foreign key missing! Recreating table...")
        
        # Rename old table
        cursor.execute("ALTER TABLE profiles RENAME TO profiles_old")
        
        # Create new table with proper foreign key
        cursor.execute("""
            CREATE TABLE profiles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                age INTEGER,
                gender TEXT,
                weight REAL,
                height REAL,
                diet_type TEXT,
                state TEXT,
                cuisine TEXT,
                health_goal TEXT,
                weekly_budget INTEGER,
                activity_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Copy data from old table
        cursor.execute("""
            INSERT INTO profiles 
            SELECT * FROM profiles_old
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE profiles_old")
        
        conn.commit()
        print("   ✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"   ❌ Migration error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Foreign Key Setup")
    print("=" * 60)
    migrate_profiles_table()

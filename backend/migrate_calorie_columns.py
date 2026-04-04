#!/usr/bin/env python3
"""
Migration script to add calorie columns to existing profiles table.
"""

import sqlite3
import os
from pathlib import Path

def migrate_add_calorie_columns():
    """Add bmr, tdee, daily_calories columns to profiles table if they don't exist."""
    
    # Compute database path the same way history_service does:
    # _DB_PATH = str(Path(__file__).resolve().parents[2] / "food_scanner.db")
    # This script is in backend/, so parents[2] would be the food-scanner-app root
    db_path = Path(__file__).resolve().parents[2] / "food_scanner.db"
    
    print(f"Database path: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    
    # Create database and initial schema if it doesn't exist
    if not db_path.exists():
        print(f"\n📝 Creating database with full schema (first time)...")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, ensure users table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                email      TEXT    NOT NULL UNIQUE,
                password   TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        
        # Create or check profiles table - including all calorie columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
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
                bmr REAL DEFAULT NULL,
                tdee REAL DEFAULT NULL,
                daily_calories REAL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        
        # Now check if columns exist and add them if needed
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(profiles)")
        existing_columns = {row['name'] for row in cursor.fetchall()}
        
        columns_to_add = {
            'bmr': 'REAL DEFAULT NULL',
            'tdee': 'REAL DEFAULT NULL',
            'daily_calories': 'REAL DEFAULT NULL'
        }
        
        columns_added = []
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                print(f"Adding column '{col_name}' to profiles table...")
                try:
                    cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
                    columns_added.append(col_name)
                except sqlite3.OperationalError as e:
                    print(f"Warning: Could not add column {col_name}: {e}")
            else:
                print(f"Column '{col_name}' already exists")
        
        if columns_added:
            conn.commit()
            print(f"\n✅ Successfully added {len(columns_added)} columns: {', '.join(columns_added)}")
        else:
            print("\n✅ All calorie columns already exist")
        
        # Verify the table structure
        cursor.execute("PRAGMA table_info(profiles)")
        print("\nProfiles table structure:")
        for row in cursor.fetchall():
            print(f"  - {row['name']}: {row['type']}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Migration: Add Calorie Columns to Profiles Table")
    print("=" * 70 + "\n")
    
    success = migrate_add_calorie_columns()
    
    if not success:
        print("\n❌ Migration failed!")
        exit(1)
    else:
        print("\n✅ Migration completed successfully!")

#!/usr/bin/env python3
"""
Updated Supabase Migration Script
Easier connection configuration
"""

import sqlite3
import psycopg2
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# =============================================================================

# Path to your SQLite database file
SQLITE_DB_PATH = r"C:\Users\welcome 2\Downloads\fitcode-gym-platform-v1\gym-platform-backend\src\database\app.db"

# Supabase connection - PASTE YOUR FULL CONNECTION STRING HERE
# SUPABASE_URL = "postgresql://postgres:sanket242104@db.qqjpphojzkpastodgpfr.supabase.co:5432/postgres"
SUPABASE_URL = "postgresql://postgres.qqjpphojzkpastodgpfr:sanket242104@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"


# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

def connect_sqlite(db_path):
    """Connect to SQLite database"""
    try:
        if not os.path.exists(db_path):
            print(f"❌ SQLite database not found at: {db_path}")
            return None
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print(f"✅ Connected to SQLite: {os.path.basename(db_path)}")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to SQLite: {e}")
        return None

def connect_supabase():
    """Connect to Supabase PostgreSQL database"""
    try:
        if "YOUR_PASSWORD" in SUPABASE_URL or "YOUR_PROJECT_REF" in SUPABASE_URL:
            print("❌ Please update SUPABASE_URL with your actual connection string")
            return None
            
        conn = psycopg2.connect(SUPABASE_URL)
        print(f"✅ Connected to Supabase successfully")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return None

def clear_supabase_tables(pg_conn):
    """Clear existing data from Supabase tables"""
    tables = [
        'bookmarked_machines', 'scan_history', 'multilingual_content',
        'qr_codes', 'gym_machines', 'gyms', 'gym_clients', 'gym_owners'
    ]
    
    try:
        cursor = pg_conn.cursor()
        print("🧹 Clearing existing data from Supabase tables...")
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        
        pg_conn.commit()
        print("✅ Existing data cleared successfully")
        return True
    except Exception as e:
        print(f"⚠️  Warning clearing tables: {e}")
        pg_conn.rollback()
        return False

def migrate_table(sqlite_conn, pg_conn, table_name):
    """Migrate data from SQLite table to Supabase table"""
    try:
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"📝 No data found in {table_name}")
            return True
        
        # Get column names
        columns = [description[0] for description in sqlite_cursor.description]
        
        # Prepare PostgreSQL insert
        pg_cursor = pg_conn.cursor()
        
        # Create placeholders for INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Convert rows to list of tuples
        data_to_insert = []
        for row in rows:
            data_to_insert.append(tuple(row))
        
        # Execute batch insert
        pg_cursor.executemany(insert_query, data_to_insert)
        pg_conn.commit()
        
        print(f"✅ Successfully migrated {len(data_to_insert)} rows from {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating {table_name}: {e}")
        pg_conn.rollback()
        return False

def reset_sequences(pg_conn, tables_with_serial):
    """Reset PostgreSQL sequences after data migration"""
    try:
        pg_cursor = pg_conn.cursor()
        print("🔄 Resetting PostgreSQL sequences...")
        
        for table in tables_with_serial:
            # Get the maximum ID from the table
            pg_cursor.execute(f"SELECT MAX(id) FROM {table}")
            result = pg_cursor.fetchone()
            max_id = result[0] if result[0] else 0
            
            # Reset the sequence to max_id + 1
            sequence_name = f"{table}_id_seq"
            pg_cursor.execute(f"SELECT setval('{sequence_name}', {max_id + 1})")
            print(f"   Reset sequence {sequence_name} to {max_id + 1}")
        
        pg_conn.commit()
        print("✅ Sequences reset successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting sequences: {e}")
        return False

def verify_migration(sqlite_conn, pg_conn):
    """Verify migration by comparing row counts"""
    print("\n📊 Verifying migration...")
    
    tables = [
        'gym_owners', 'gyms', 'gym_clients', 'gym_machines',
        'qr_codes', 'multilingual_content', 'scan_history', 'bookmarked_machines'
    ]
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    all_match = True
    total_sqlite = 0
    total_supabase = 0
    
    for table in tables:
        try:
            # Count SQLite rows
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            # Count Supabase rows
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            
            total_sqlite += sqlite_count
            total_supabase += pg_count
            
            status = "✅" if sqlite_count == pg_count else "❌"
            print(f"{status} {table}: SQLite={sqlite_count}, Supabase={pg_count}")
            
            if sqlite_count != pg_count:
                all_match = False
        except Exception as e:
            print(f"❌ Error verifying {table}: {e}")
            all_match = False
    
    print(f"\n📋 Total Records: SQLite={total_sqlite}, Supabase={total_supabase}")
    return all_match

def show_sqlite_data_summary(sqlite_conn):
    """Show summary of data in SQLite database"""
    tables = [
        'gym_owners', 'gyms', 'gym_clients', 'gym_machines',
        'qr_codes', 'multilingual_content', 'scan_history', 'bookmarked_machines'
    ]
    
    cursor = sqlite_conn.cursor()
    print("📊 SQLite Database Summary:")
    
    total_records = 0
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"   {table}: {count} records")
        except Exception as e:
            print(f"   {table}: Error reading ({e})")
    
    print(f"   Total: {total_records} records")
    return total_records

def main():
    print("=" * 60)
    print("🚀 FITCODE GYM PLATFORM - SUPABASE MIGRATION")
    print("=" * 60)
    print(f"Source: SQLite Database")
    print(f"Target: Supabase PostgreSQL")
    print()
    
    # Check configuration
    if "YOUR_PASSWORD" in SUPABASE_URL:
        print("❌ Please update SUPABASE_URL with your actual connection string")
        print("\n📝 Get your connection string from:")
        print("1. Supabase Dashboard → Settings → Database")
        print("2. Copy the 'URI' connection string")
        print("3. Update SUPABASE_URL in this script")
        return
    
    # Connect to SQLite
    sqlite_conn = connect_sqlite(SQLITE_DB_PATH)
    if not sqlite_conn:
        print("\n🔧 Please check your SQLite database path")
        return
    
    # Show SQLite data summary
    total_records = show_sqlite_data_summary(sqlite_conn)
    if total_records == 0:
        print("\n⚠️  No data found in SQLite database")
        print("Are you sure this is the correct database file?")
        return
    
    print()
    
    # Connect to Supabase
    pg_conn = connect_supabase()
    if not pg_conn:
        print("\n🔧 Please check your Supabase connection string")
        return
    
    print()
    
    # Clear existing data
    clear_supabase_tables(pg_conn)
    print()
    
    # Define migration order (respecting foreign key constraints)
    migration_order = [
        'gym_owners',
        'gyms', 
        'gym_clients',
        'gym_machines',
        'qr_codes',
        'multilingual_content',
        'scan_history',
        'bookmarked_machines'
    ]
    
    # Migrate tables in order
    success_count = 0
    print("🔄 Starting data migration...")
    for table in migration_order:
        print(f"   Migrating {table}...")
        if migrate_table(sqlite_conn, pg_conn, table):
            success_count += 1
        else:
            print(f"❌ Failed to migrate {table}")
            break
    
    print()
    
    # Reset sequences for tables with SERIAL primary keys
    if success_count == len(migration_order):
        reset_sequences(pg_conn, migration_order)
        print()
        
        # Verify migration
        if verify_migration(sqlite_conn, pg_conn):
            print(f"\n🎉 MIGRATION SUCCESSFUL!")
            print("✅ All data migrated and verified")
            print("\n🚀 Next Steps:")
            print("1. Check your data in Supabase Table Editor")
            print("2. Update your Flask app configuration")
            print("3. Test your application")
        else:
            print(f"\n⚠️  Migration completed but verification found discrepancies")
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    print(f"\n📋 Migration Summary: {success_count}/{len(migration_order)} tables migrated")

if __name__ == "__main__":
    main()


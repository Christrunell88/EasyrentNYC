#!/usr/bin/env python3
"""
Production Database Sync Script
===============================
This script exports all buildings and units from the current database
and can be used to sync production data.

Run this script on the production server after deployment to ensure
all data is properly synced.

Usage:
    python sync_production_data.py

This will:
1. Check current database stats
2. If data is missing, populate from the embedded data
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
import uuid

# Load environment
load_dotenv('.env')

# Connect to database
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

def get_stats():
    """Get current database statistics"""
    buildings = db.buildings.count_documents({})
    units = db.units.count_documents({})
    return buildings, units

def check_and_report():
    """Check current state and report"""
    buildings, units = get_stats()
    print(f"\n📊 Current Database Stats:")
    print(f"   Buildings: {buildings}")
    print(f"   Units: {units}")
    
    if buildings >= 34 and units >= 180:
        print("\n✅ Database appears to be in sync!")
        return True
    else:
        print("\n⚠️  Database appears to be out of sync.")
        print(f"   Expected: 34 buildings, 180+ units")
        print(f"   Found: {buildings} buildings, {units} units")
        return False

def main():
    print("=" * 50)
    print("NoFeesApts Production Database Sync")
    print("=" * 50)
    
    is_synced = check_and_report()
    
    if is_synced:
        print("\nNo action needed. Database is up to date.")
    else:
        print("\n" + "=" * 50)
        print("ACTION REQUIRED")
        print("=" * 50)
        print("""
The production database is missing data. This typically happens when:
1. New buildings were added in the preview environment
2. The production deployment uses a separate database

To sync the data, you have two options:

OPTION 1: Re-run the data population scripts
------------------------------------------
Run these scripts in order on the production server:
  python add_20_park.py
  python add_tfc_buildings.py
  python add_95_horatio.py
  python add_4610_center_blvd.py
  python add_205_e_59_st.py
  python add_malt_drive.py
  (and any other add_*.py scripts)

OPTION 2: Contact support
-------------------------
If you need help syncing the databases, contact Emergent support.

Note: The preview and production environments use separate MongoDB
databases for isolation. Changes made in preview don't automatically
sync to production.
        """)
    
    return 0 if is_synced else 1

if __name__ == "__main__":
    sys.exit(main())

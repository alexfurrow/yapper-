#!/usr/bin/env python3
"""
Script to populate user_entry_id for existing entries.
Run this after the migration to set user_entry_id for all existing entries.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import create_app
from extensions import db
from backend.models.entries import entries
from backend.models.users import users
from sqlalchemy import func

def populate_user_entry_ids():
    """Populate user_entry_id for all existing entries"""
    app = create_app()
    
    with app.app_context():
        print("Starting user_entry_id population...")
        
        # Get all users
        all_users = users.query.all()
        total_entries_processed = 0
        
        for user in all_users:
            print(f"Processing user {user.id} ({user.username})...")
            
            # Get all entries for this user, ordered by creation date
            user_entries = entries.query.filter_by(user_id=user.id).order_by(entries.created_at.asc()).all()
            
            if not user_entries:
                print(f"  No entries found for user {user.username}")
                continue
            
            # Update each entry with its user_entry_id
            for i, entry in enumerate(user_entries):
                entry.user_entry_id = i + 1  # 1-based numbering
                print(f"  Entry {entry.entry_id} -> user_entry_id {entry.user_entry_id}")
            
            # Commit changes for this user
            db.session.commit()
            total_entries_processed += len(user_entries)
            print(f"  Updated {len(user_entries)} entries for user {user.username}")
        
        print(f"\nMigration complete! Processed {total_entries_processed} total entries.")
        
        # Verify the migration
        print("\nVerifying migration...")
        for user in all_users:
            user_entries = entries.query.filter_by(user_id=user.id).order_by(entries.user_entry_id.asc()).all()
            if user_entries:
                print(f"User {user.username}: {len(user_entries)} entries, IDs: {[e.user_entry_id for e in user_entries]}")

if __name__ == '__main__':
    populate_user_entry_ids()

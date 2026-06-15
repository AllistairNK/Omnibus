#!/usr/bin/env python3
"""
Script to set a user as admin in the database.
Run: python set_admin.py <user_id_or_email>
"""
import os
import sys
sys.path.append('.')

from app.core.supabase import SupabaseClient

def set_user_as_admin(user_identifier: str):
    """Set a user as admin in the database."""
    client = SupabaseClient()
    if not client._client:
        print("ERROR: Supabase client not initialized")
        return False
    
    try:
        # Try to find user by ID or email
        if '@' in user_identifier:
            # Search by email
            response = client._client.table('users').select('*').eq('email', user_identifier).execute()
        else:
            # Search by ID
            response = client._client.table('users').select('*').eq('id', user_identifier).execute()
        
        if not response.data:
            print(f"User not found: {user_identifier}")
            return False
        
        user = response.data[0]
        print(f"Found user: {user['email']} (ID: {user['id']})")
        print(f"Current role: {user.get('role', 'NOT SET')}")
        
        if user.get('role') == 'admin':
            print("User already has admin role")
            return True
        
        # Update to admin
        update_data = {'role': 'admin'}
        update_result = client._client.table('users').update(update_data).eq('id', user['id']).execute()
        
        print("User role updated to admin")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python set_admin.py <user_id_or_email>")
        print("Example: python set_admin.py d1335931-8ee7-46e4-a348-adae08b0e542")
        print("Example: python set_admin.py allistair99@yahoo.com.my")
        sys.exit(1)
    
    success = set_user_as_admin(sys.argv[1])
    sys.exit(0 if success else 1)
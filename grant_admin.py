#!/usr/bin/env python3
"""
Script to grant admin privileges to jsun2016@live.com
Run this script to directly update the user's admin status in the database
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def grant_admin_privileges():
    """Grant admin privileges to jsun2016@live.com"""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        print("Please make sure you have set the DATABASE_URL in your .env file")
        return False
    
    try:
        print("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("👤 Checking if user exists...")
        cursor.execute("""
            SELECT email, is_admin FROM users WHERE email = %s
        """, ('jsun2016@live.com',))
        
        result = cursor.fetchone()
        
        if not result:
            print("❌ User jsun2016@live.com not found in database")
            cursor.close()
            conn.close()
            return False
        
        email, current_admin_status = result
        print(f"✅ User found: {email}")
        print(f"📊 Current admin status: {current_admin_status}")
        
        if current_admin_status:
            print("✅ User is already an admin!")
            cursor.close()
            conn.close()
            return True
        
        print("🔧 Granting admin privileges...")
        cursor.execute("""
            UPDATE users 
            SET is_admin = TRUE 
            WHERE email = %s
            RETURNING email, is_admin
        """, ('jsun2016@live.com',))
        
        updated_result = cursor.fetchone()
        
        if updated_result:
            conn.commit()
            email, is_admin = updated_result
            print(f"✅ SUCCESS! Admin privileges granted to {email}")
            print(f"📊 New admin status: {is_admin}")
            
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Failed to update user")
            cursor.close()
            conn.close()
            return False
            
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Admin Privilege Grant Tool")
    print("=" * 50)
    
    success = grant_admin_privileges()
    
    if success:
        print("\n🎉 Admin privileges successfully granted!")
        print("👤 jsun2016@live.com can now access admin features")
    else:
        print("\n❌ Failed to grant admin privileges")
        print("Please check the error messages above")
    
    print("=" * 50)
#!/usr/bin/env python3
"""
setup_admin.py
Run this ONCE after importing database.sql to create the admin account
with a properly hashed password.

Usage:
    python setup_admin.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
import MySQLdb

# ── Config (must match config.py) ────────────────────────────
MYSQL_HOST     = 'localhost'
MYSQL_USER     = 'root'
MYSQL_PASSWORD = ''          # ← change to your MySQL root password
MYSQL_DB       = 'mockmentor_db'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'  # ← default admin password

def setup_admin():
    try:
        conn = MySQLdb.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cur = conn.cursor()

        hashed = generate_password_hash(ADMIN_PASSWORD)

        # Delete existing admin and re-insert with hashed password
        cur.execute("DELETE FROM admins WHERE username = %s", (ADMIN_USERNAME,))
        cur.execute(
            "INSERT INTO admins (username, password) VALUES (%s, %s)",
            (ADMIN_USERNAME, hashed)
        )
        conn.commit()
        cur.close()
        conn.close()

        print("✅ Admin account created successfully!")
        print(f"   Username: {ADMIN_USERNAME}")
        print(f"   Password: {ADMIN_PASSWORD}")
        print("\n⚠️  Change the password after first login in production!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("  1. MySQL is running")
        print("  2. You have imported database.sql")
        print("  3. MYSQL_PASSWORD in this script matches your MySQL root password")

if __name__ == '__main__':
    setup_admin()

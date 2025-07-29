#!/usr/bin/env python3
"""
Scheduled notification script for diet reminders
This script should be run daily via cron to check for users with 1 day remaining
"""

import requests
import sys
import os
from datetime import datetime

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.firebase_client import check_users_with_one_day_remaining

def main():
    """Main function to check diet reminders and send notifications"""
    print(f"[{datetime.now()}] Starting diet reminder check...")
    
    try:
        # Check for users with 1 day remaining
        one_day_users = check_users_with_one_day_remaining()
        
        if one_day_users:
            print(f"[{datetime.now()}] Found {len(one_day_users)} users with 1 day remaining:")
            for user in one_day_users:
                print(f"  - {user['name']} ({user['email']})")
        else:
            print(f"[{datetime.now()}] No users with 1 day remaining")
            
        print(f"[{datetime.now()}] Diet reminder check completed successfully")
        return 0
        
    except Exception as e:
        print(f"[{datetime.now()}] Error during diet reminder check: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
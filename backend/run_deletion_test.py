#!/usr/bin/env python3
"""
Automated account deletion test runner
"""
import sys
import subprocess

# Run the test script
if __name__ == "__main__":
    print("="*60)
    print("ACCOUNT DELETION TEST RUNNER")
    print("="*60)
    print("\nThis will test account deletion on production backend.")
    print("You will need to provide a test user ID.\n")
    
    # Run the test script
    subprocess.run([sys.executable, "test_account_deletion.py"])

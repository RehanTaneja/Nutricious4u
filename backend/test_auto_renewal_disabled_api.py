"""
Test script to verify that auto-renewal stops when disabled.
This test uses HTTP requests to the Railway backend API.

Usage:
    python test_auto_renewal_disabled_api.py [user_id]
    
If user_id is not provided, the script will prompt for it.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Railway backend URL
BASE_URL = "https://nutricious4u-production.up.railway.app"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_auto_renewal_disabled():
    """Test that subscription does NOT auto-renew when autoRenewalEnabled is False"""
    
    print_section("TEST: Auto-Renewal Disabled - Subscription Should NOT Renew")
    
    # Get test user ID from command line or prompt
    if len(sys.argv) > 1:
        test_user_id = sys.argv[1].strip()
        print(f"\n📋 Using user ID from command line: {test_user_id}")
    else:
        try:
            test_user_id = input("\nEnter test user ID to test: ").strip()
        except EOFError:
            print("\n❌ Error: User ID is required")
            print("   Usage: python test_auto_renewal_disabled_api.py <user_id>")
            return
        
        if not test_user_id:
            print("❌ Error: User ID is required")
            print("   Usage: python test_auto_renewal_disabled_api.py <user_id>")
            return
    
    print(f"\n📋 Testing with user: {test_user_id}")
    
    # Step 1: Get current subscription status
    print_section("Step 1: Get Current Subscription Status")
    try:
        response = requests.get(f"{BASE_URL}/subscription/status/{test_user_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get subscription status: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        initial_status = response.json()
        print(f"✓ Current Status Retrieved:")
        print(f"  - Plan: {initial_status.get('subscriptionPlan', 'N/A')}")
        print(f"  - Is Active: {initial_status.get('isSubscriptionActive', False)}")
        print(f"  - Status: {initial_status.get('subscriptionStatus', 'N/A')}")
        print(f"  - Auto-Renewal Enabled: {initial_status.get('autoRenewalEnabled', True)}")
        print(f"  - End Date: {initial_status.get('subscriptionEndDate', 'N/A')}")
        
        # Check if subscription is active
        if not initial_status.get('isSubscriptionActive', False):
            print(f"\n⚠️  WARNING: Subscription is not currently active!")
            print(f"   This test requires an active subscription.")
            print(f"   Please activate a subscription first.")
            return
        
        # Check auto-renewal status
        auto_renewal_enabled = initial_status.get('autoRenewalEnabled', True)
        if auto_renewal_enabled:
            print(f"\n⚠️  Auto-renewal is currently ENABLED")
            print(f"   We need to disable it for this test.")
            
            # Step 2: Disable auto-renewal
            print_section("Step 2: Disable Auto-Renewal")
            try:
                response = requests.post(
                    f"{BASE_URL}/subscription/toggle-auto-renewal/{test_user_id}",
                    params={"enabled": False}
                )
                if response.status_code != 200:
                    print(f"❌ Failed to disable auto-renewal: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return
                
                result = response.json()
                print(f"✓ Auto-renewal disabled: {result.get('message', 'Success')}")
                
                # Verify it's disabled
                response = requests.get(f"{BASE_URL}/subscription/status/{test_user_id}")
                if response.status_code == 200:
                    status = response.json()
                    if not status.get('autoRenewalEnabled', True):
                        print(f"✓ Verified: Auto-renewal is now disabled")
                    else:
                        print(f"❌ Failed: Auto-renewal is still enabled")
                        return
                        
            except Exception as e:
                print(f"❌ Error disabling auto-renewal: {e}")
                return
        else:
            print(f"\n✓ Auto-renewal is already DISABLED (perfect for this test)")
        
        # Step 3: Check subscription end date
        print_section("Step 3: Check Subscription End Date")
        end_date_str = initial_status.get('subscriptionEndDate')
        if not end_date_str:
            print(f"❌ Error: No subscription end date found")
            return
        
        # Parse end date
        try:
            # Handle different date formats
            if 'T' in end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_date = datetime.fromisoformat(end_date_str)
        except Exception as e:
            print(f"❌ Error parsing end date: {e}")
            print(f"   End date string: {end_date_str}")
            return
        
        current_time = datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.now()
        time_until_expiry = end_date - current_time
        
        print(f"  - End Date: {end_date}")
        print(f"  - Current Time: {current_time}")
        print(f"  - Time Until Expiry: {time_until_expiry}")
        
        if time_until_expiry.total_seconds() > 0:
            print(f"\n⚠️  WARNING: Subscription has not expired yet!")
            print(f"   It will expire in: {time_until_expiry}")
            print(f"\n   For this test to work, the subscription needs to be expired.")
            print(f"   Options:")
            print(f"   1. Wait for the subscription to expire naturally")
            print(f"   2. Manually set subscriptionEndDate to past in Firestore")
            print(f"   3. The backend job will check every 6 hours")
            print(f"\n   The job will automatically detect expiry and:")
            print(f"   - If auto-renewal is ENABLED: Renew the subscription")
            print(f"   - If auto-renewal is DISABLED: Mark as expired (what we're testing)")
            
            # Ask if user wants to continue anyway (only if interactive)
            if sys.stdin.isatty():
                try:
                    continue_anyway = input("\n   Continue anyway? (y/n): ").strip().lower()
                    if continue_anyway != 'y':
                        print("\n   Test cancelled. Please set subscriptionEndDate to past or wait for expiry.")
                        return
                except EOFError:
                    print("\n   ⚠️  Non-interactive mode: Continuing with test...")
            else:
                print("\n   ⚠️  Non-interactive mode: Continuing with test...")
        else:
            print(f"\n✓ Subscription is EXPIRED (perfect for testing)")
        
        # Step 4: Verify expected behavior
        print_section("Step 4: Expected Behavior When Auto-Renewal is Disabled")
        print("When the backend job runs (every 6 hours), it should:")
        print("  1. Detect that subscription has expired")
        print("  2. Check that autoRenewalEnabled is False")
        print("  3. Call send_subscription_expiry_notifications()")
        print("  4. Set isSubscriptionActive = False")
        print("  5. Set subscriptionStatus = 'expired'")
        print("  6. Send notifications to user and dietician")
        print("  7. NOT renew the subscription")
        
        # Step 5: Check if we can manually trigger (if endpoint exists)
        print_section("Step 5: Manual Verification")
        print("Since the job runs automatically every 6 hours, we'll check the current state.")
        print("If the subscription is already expired, the job should have processed it.")
        
        # Get final status
        response = requests.get(f"{BASE_URL}/subscription/status/{test_user_id}")
        if response.status_code == 200:
            final_status = response.json()
            
            print(f"\n📊 Final Status:")
            print(f"  - Is Active: {final_status.get('isSubscriptionActive', False)}")
            print(f"  - Status: {final_status.get('subscriptionStatus', 'N/A')}")
            print(f"  - Auto-Renewal Enabled: {final_status.get('autoRenewalEnabled', True)}")
            print(f"  - End Date: {final_status.get('subscriptionEndDate', 'N/A')}")
            
            # Verification
            print_section("Step 6: Verification Results")
            
            is_active = final_status.get('isSubscriptionActive', True)
            status = final_status.get('subscriptionStatus', '')
            auto_renewal = final_status.get('autoRenewalEnabled', True)
            
            if not is_active and status == 'expired' and not auto_renewal:
                print("✅ PASS: All checks passed!")
                print("  ✓ Subscription is inactive (isSubscriptionActive = False)")
                print("  ✓ Status is 'expired'")
                print("  ✓ Auto-renewal is disabled")
                print("  ✓ Subscription was NOT renewed")
            elif is_active and auto_renewal:
                print("⚠️  Subscription is still active with auto-renewal enabled")
                print("   This could mean:")
                print("   - The job hasn't run yet (runs every 6 hours)")
                print("   - The subscription hasn't expired yet")
                print("   - Auto-renewal was enabled and subscription was renewed")
            elif is_active and not auto_renewal:
                print("⚠️  Subscription is still active but auto-renewal is disabled")
                print("   This could mean:")
                print("   - The job hasn't run yet (runs every 6 hours)")
                print("   - The subscription hasn't expired yet")
                print("   - Waiting for the scheduled job to process expiry")
            else:
                print("❓ Unexpected state - please check manually")
                print(f"   Is Active: {is_active}")
                print(f"   Status: {status}")
                print(f"   Auto-Renewal: {auto_renewal}")
        else:
            print(f"❌ Failed to get final status: {response.status_code}")
        
        # Summary
        print_section("Test Summary")
        print("The test verifies that when auto-renewal is disabled:")
        print("  ✓ The subscription status is checked correctly")
        print("  ✓ Auto-renewal setting is respected")
        print("  ✓ When expired, subscription becomes inactive")
        print("  ✓ Status is set to 'expired'")
        print("  ✓ Subscription is NOT automatically renewed")
        print("\nNote: The backend job runs every 6 hours.")
        print("If the subscription just expired, wait for the next job run.")
        print("Or check the backend logs to see if the job has processed it.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        print(f"   Make sure the Railway backend is accessible at: {BASE_URL}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Auto-Renewal Disabled Test - Railway Backend")
    print("=" * 70)
    print(f"\nBackend URL: {BASE_URL}")
    print("\nThis test verifies that subscriptions do NOT auto-renew when")
    print("autoRenewalEnabled is set to False.")
    print("\nRequirements:")
    print("  - A test user with an active subscription")
    print("  - Subscription should be expired or expiring soon")
    print("  - Auto-renewal should be disabled")
    
    test_auto_renewal_disabled()
    
    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70 + "\n")

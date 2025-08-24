#!/usr/bin/env python3
"""
Backend Logging Test Script
This script tests if we can capture frontend events in backend logs
"""

import requests
import json
import time

def test_backend_logging():
    """Test the backend logging endpoint"""
    backend_url = "https://nutricious4u-production.up.railway.app"
    
    # Test data for frontend logging
    test_log = {
        "userId": "test_user_123",
        "event": "TEST_FRONTEND_LOG",
        "data": json.dumps({
            "test": True,
            "platform": "ios",
            "timestamp": time.time()
        }),
        "platform": "ios",
        "timestamp": "2025-08-23T07:00:00Z",
        "userAgent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0"
    }
    
    print("🔍 Testing backend logging endpoint...")
    print(f"Backend URL: {backend_url}")
    print(f"Test payload: {json.dumps(test_log, indent=2)}")
    
    try:
        response = requests.post(
            f"{backend_url}/api/debug/frontend-log",
            json=test_log,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Nutricious4u/1 CFNetwork/3826.500.131 Darwin/24.5.0"
            },
            timeout=10
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        print(f"✅ Response Headers: {dict(response.headers)}")
        print(f"✅ Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 Backend logging endpoint is working!")
            print("Frontend events will now appear in your Railway backend logs")
        elif response.status_code == 404:
            print("\n⚠️ Endpoint not found - you need to add this to your backend")
            print("Add this endpoint to your backend server:")
            print("""
@app.route('/api/debug/frontend-log', methods=['POST'])
def log_frontend_event():
    data = request.get_json()
    
    # Log with clear formatting for easy identification
    print(f"📱 FRONTEND EVENT: {data.get('event', 'UNKNOWN')}")
    print(f"👤 User: {data.get('userId', 'anonymous')}")
    print(f"📊 Platform: {data.get('platform', 'unknown')}")
    print(f"🕐 Time: {data.get('timestamp', 'unknown')}")
    print(f"📄 Data: {data.get('data', '{}')}")
    print(f"🌐 UserAgent: {data.get('userAgent', 'unknown')}")
    print("=" * 50)
    
    return {'success': True, 'message': 'Event logged'}
            """)
        else:
            print(f"\n❌ Unexpected response: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection failed - check backend URL")
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_backend_logging()
